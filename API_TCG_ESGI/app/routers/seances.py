from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .. import config
from ..database import get_db
from ..journal import journaliser
from ..mail import mail_place_liberee
from ..models import Inscription, Participation, Seance, Semestre, Utilisateur
from ..ratelimit import Limiteur
from ..schemas import (
    AppelBody, InscriptionOut, ParticipationCreate, ParticipationOut, ParticipationUpdate, PointageInfo,
    PointageOuvrir, PointerBody, PointerOut, ResultatOut, ResultatsBody, SeanceCreate, SeanceDetail, SeanceOut,
    SeanceUpdate,
)
from ..security import get_current_user, get_current_user_optional, is_staff, require_roles
from ..services import resultats_out, seance_detail, seance_out, seances_out
from ..utils.discord import notifier_participants
from .. import vie

router = APIRouter(prefix="/seances", tags=["seances"])
staff = require_roles("admin", "moderator")
limiteur_pointage = Limiteur(max_echecs=10, fenetre_s=15 * 60)


def _get(db: Session, sid: int) -> Seance:
    s = db.get(Seance, sid, options=[joinedload(Seance.semestre)])
    if not s:
        raise HTTPException(404, "Séance introuvable")
    return s


def _check_semestre(db: Session, semestre_id: int) -> None:
    if not db.get(Semestre, semestre_id):
        raise HTTPException(422, "Semestre inconnu")


def _date_fr(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def notifier_promus(background: BackgroundTasks, seance: Seance, promus: list[Utilisateur]) -> None:
    """Prévient par email les membres sortis de la liste d'attente."""
    for u in promus:
        background.add_task(mail_place_liberee, u.adresse_mail, u.prenom, seance.nom, _date_fr(seance.date_seance),
                            f"{config.FRONTEND_URL}/seances/{seance.id}")


@router.get("", response_model=list[SeanceOut])
def list_seances(
    response: Response,
    semestreId: int | None = None,
    dateFrom: date | None = None,
    dateTo: date | None = None,
    a_venir: bool | None = None,
    jeu: str | None = None,
    q: str | None = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    viewer: Utilisateur | None = Depends(get_current_user_optional),
):
    page, limit = max(page, 1), min(max(limit, 1), 200)
    query = db.query(Seance).options(joinedload(Seance.semestre))
    if semestreId:
        query = query.filter(Seance.semestre_id == semestreId)
    if dateFrom:
        query = query.filter(Seance.date_seance >= dateFrom)
    if dateTo:
        query = query.filter(Seance.date_seance <= dateTo)
    if a_venir is True:
        query = query.filter(Seance.date_seance >= date.today())
    elif a_venir is False:
        query = query.filter(Seance.date_seance < date.today())
    if jeu:
        query = query.filter(Seance.jeu == jeu)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Seance.nom.ilike(like), Seance.lieu.ilike(like), Seance.description.ilike(like)))
    response.headers["X-Total-Count"] = str(query.count())
    # À venir : la plus proche d'abord ; sinon la plus récente d'abord
    ordre = (Seance.date_seance.asc(), Seance.heure_debut.asc().nulls_last()) if a_venir else \
        (Seance.date_seance.desc(), Seance.heure_debut.desc().nulls_last())
    seances = query.order_by(*ordre, Seance.id).offset((page - 1) * limit).limit(limit).all()
    return seances_out(db, seances, viewer)


@router.get("/{sid}", response_model=SeanceDetail)
def get_seance(sid: int, db: Session = Depends(get_db),
               user: Utilisateur | None = Depends(get_current_user_optional)):
    return seance_detail(db, _get(db, sid), user, is_staff(user))


@router.post("", response_model=SeanceOut, status_code=201)
def create_seance(body: SeanceCreate, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    _check_semestre(db, body.semestre_id)
    s = Seance(**body.model_dump())
    db.add(s)
    db.flush()
    journaliser(db, moderateur, "seance.creation", f"Séance « {s.nom} » du {_date_fr(s.date_seance)} créée "
                f"({float(s.nb_point):g} pts)", seance_id=s.id)
    db.commit()
    return seance_out(db, _get(db, s.id))


@router.patch("/{sid}", response_model=SeanceOut)
def update_seance(sid: int, body: SeanceUpdate, background: BackgroundTasks, db: Session = Depends(get_db),
                  moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    data = body.model_dump(exclude_unset=True)
    for requis in ("nom", "date_seance", "nb_point", "semestre_id"):
        if requis in data and data[requis] is None:
            data.pop(requis)
    if "semestre_id" in data:
        _check_semestre(db, data["semestre_id"])
    date_changee = "date_seance" in data and data["date_seance"] != s.date_seance
    changements = {}
    for k, v in data.items():
        avant = getattr(s, k)
        if (float(avant) if k == "nb_point" else avant) != v:
            changements[k] = {"avant": str(avant) if avant is not None else None, "apres": str(v) if v is not None else None}
        setattr(s, k, v)
    if date_changee and s.date_seance >= date.today():
        # Nouvelle date : on ré-annonce et on reprogramme le rappel
        s.annonce_envoyee = False
        s.rappel_envoye = False
    promus = vie.reequilibrer(db, s) if "places_max" in changements else []
    if changements:
        journaliser(db, moderateur, "seance.modification", f"Séance « {s.nom} » modifiée ({', '.join(changements)})",
                    seance_id=s.id, details=changements)
    db.commit()
    notifier_promus(background, s, promus)
    return seance_out(db, _get(db, sid))


@router.delete("/{sid}", status_code=204)
def delete_seance(sid: int, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    journaliser(db, moderateur, "seance.suppression", f"Séance « {s.nom} » du {_date_fr(s.date_seance)} supprimée "
                f"avec ses présences et résultats", details={"seance_id": s.id})
    db.delete(s)
    db.commit()


# --- Inscriptions (« Je viens ») -----------------------------------------------------------
@router.post("/{sid}/inscription", response_model=InscriptionOut)
def s_inscrire(sid: int, db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    s = _get(db, sid)
    statut = vie.inscrire(db, s, user)
    db.commit()
    return InscriptionOut(statut=statut, seance=seance_out(db, s, user))


@router.delete("/{sid}/inscription", response_model=InscriptionOut)
def se_desinscrire(sid: int, background: BackgroundTasks, db: Session = Depends(get_db),
                   user: Utilisateur = Depends(get_current_user)):
    s = _get(db, sid)
    promus = vie.desinscrire(db, s, user)
    db.commit()
    notifier_promus(background, s, promus)
    return InscriptionOut(statut=None, seance=seance_out(db, s, user))


@router.delete("/{sid}/inscriptions/{uid}", status_code=204)
def retirer_inscription(sid: int, uid: int, background: BackgroundTasks, db: Session = Depends(get_db),
                        moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    u = db.get(Utilisateur, uid)
    if not u or not db.get(Inscription, {"utilisateur_id": uid, "seance_id": sid}):
        raise HTTPException(404, "Inscription introuvable")
    promus = vie.desinscrire(db, s, u)
    journaliser(db, moderateur, "inscription.retrait", f"{u.prenom} {u.nom} retiré·e des inscrits de « {s.nom} »",
                membre_id=u.id, seance_id=s.id)
    db.commit()
    notifier_promus(background, s, promus)


# --- Pointage par QR code ---------------------------------------------------------------
def _pointage_info(db: Session, s: Seance) -> PointageInfo:
    detail = seance_detail(db, s, None, True)
    info = PointageInfo(ouvert=vie.pointage_ouvert(s), periode_s=config.QR_PERIODE_S, pointages=detail.pointages)
    if info.ouvert:
        code, restant = vie.code_courant(s)
        info.code, info.secondes_restantes, info.expire_le = code, restant, s.pointage_expire_le
        info.url = f"{config.FRONTEND_URL}/pointer/{s.id}?c={code}"
    return info


@router.get("/{sid}/pointage", response_model=PointageInfo)
def etat_pointage(sid: int, db: Session = Depends(get_db), _=Depends(staff)):
    return _pointage_info(db, _get(db, sid))


@router.post("/{sid}/pointage/ouvrir", response_model=PointageInfo)
def ouvrir_pointage(sid: int, body: PointageOuvrir | None = None, db: Session = Depends(get_db),
                    moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    deja = vie.pointage_ouvert(s)
    vie.ouvrir_pointage(s, body.duree_heures if body else None)
    if not deja:
        journaliser(db, moderateur, "pointage.ouverture", f"Pointage QR ouvert pour « {s.nom} »", seance_id=s.id)
    db.commit()
    return _pointage_info(db, s)


@router.post("/{sid}/pointage/fermer", response_model=PointageInfo)
def fermer_pointage(sid: int, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    if vie.pointage_ouvert(s):
        journaliser(db, moderateur, "pointage.fermeture", f"Pointage QR fermé pour « {s.nom} »", seance_id=s.id)
    vie.fermer_pointage(s)
    db.commit()
    return _pointage_info(db, s)


@router.post("/{sid}/pointer", response_model=PointerOut)
def pointer(sid: int, body: PointerBody, db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    """Le membre déclare sa présence en scannant le QR code (validée ensuite par la modération)."""
    cle = f"{user.id}|{sid}"
    limiteur_pointage.verifier(cle)
    s = _get(db, sid)
    if not vie.pointage_ouvert(s):
        raise HTTPException(409, "Le pointage de cette séance n'est pas ouvert")
    if not vie.code_valide(s, body.code):
        limiteur_pointage.echec(cle)
        raise HTTPException(400, "QR code expiré : scanne le code actuellement affiché")
    resultat = vie.pointer(db, s, user)
    db.commit()
    return PointerOut(resultat=resultat, seance=seance_out(db, s, user))


# --- Résultats de tournoi --------------------------------------------------------------------
@router.get("/{sid}/resultats", response_model=list[ResultatOut])
def get_resultats(sid: int, db: Session = Depends(get_db), user: Utilisateur | None = Depends(get_current_user_optional)):
    _get(db, sid)
    return resultats_out(db, sid, user, is_staff(user))


@router.put("/{sid}/resultats", response_model=list[ResultatOut])
def put_resultats(sid: int, body: ResultatsBody, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    s = _get(db, sid)
    vie.enregistrer_resultats(db, s, [r.model_dump() for r in body.resultats], body.bareme, moderateur)
    if not body.annoncer:
        s.resultats_a_annoncer = False
    db.commit()
    return resultats_out(db, sid, moderateur, True)


# --- Participants d'une séance ---------------------------------------------------------
@router.get("/{sid}/participants", response_model=list[ParticipationOut])
def seance_participants(sid: int, db: Session = Depends(get_db), _=Depends(staff)):
    _get(db, sid)
    return db.query(Participation).filter(Participation.seance_id == sid).all()


def _journal_presence(db: Session, moderateur: Utilisateur, s: Seance, u: Utilisateur, avant: bool | None,
                      apres: bool | None) -> None:
    pts = f"{float(s.nb_point):g}"
    if apres is None:
        action, txt = "presence.retrait", f"{u.prenom} {u.nom} retiré·e de « {s.nom} »" + (f" (−{pts} pts)" if avant else "")
    elif avant is None:
        action = "presence.ajout"
        txt = f"{u.prenom} {u.nom} ajouté·e à « {s.nom} » : " + (f"présent·e (+{pts} pts)" if apres else "absent·e")
    else:
        action = "presence.modification"
        txt = f"{u.prenom} {u.nom} à « {s.nom} » : " + (f"présent·e (+{pts} pts)" if apres else f"absent·e (−{pts} pts)")
    journaliser(db, moderateur, action, txt, membre_id=u.id, seance_id=s.id,
                details={"avant": avant, "apres": apres, "points": float(s.nb_point)})


@router.post("/{sid}/participants", response_model=ParticipationOut, status_code=201)
def add_participant(sid: int, body: ParticipationCreate, background: BackgroundTasks,
                    db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    if body.seance_id != sid:
        raise HTTPException(400, "seance_id incohérent")
    s = _get(db, sid)
    user = db.get(Utilisateur, body.utilisateur_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    if db.get(Participation, {"utilisateur_id": user.id, "seance_id": sid}):
        raise HTTPException(409, "Ce membre participe déjà à la séance")
    p = Participation(**body.model_dump())
    db.add(p)
    _journal_presence(db, moderateur, s, user, None, p.present)
    db.commit()
    if p.present:
        background.add_task(notifier_participants, s, [user])
    return p


@router.put("/{sid}/participants", response_model=SeanceDetail)
def appel(sid: int, body: AppelBody, background: BackgroundTasks, db: Session = Depends(get_db),
          moderateur: Utilisateur = Depends(staff)):
    """Appel de présence en une fois : crée, met à jour (et retire si `remplacer`) les participations."""
    s = _get(db, sid)
    voulus = {i.utilisateur_id: i for i in body.participants}
    ids = set(voulus)
    existants = {p.utilisateur_id: p for p in db.query(Participation).filter(Participation.seance_id == sid)}
    if body.remplacer:
        ids |= set(existants)
    membres = {u.id: u for u in db.query(Utilisateur).filter(Utilisateur.id.in_(ids))} if ids else {}
    inconnus = set(voulus) - set(membres)
    if inconnus:
        raise HTTPException(404, f"Utilisateur(s) introuvable(s) : {sorted(inconnus)}")
    nouveaux_presents: list[Utilisateur] = []
    for uid, item in voulus.items():
        p = existants.get(uid)
        if p is None:
            db.add(Participation(utilisateur_id=uid, seance_id=sid, present=item.present, commentaire=item.commentaire))
            _journal_presence(db, moderateur, s, membres[uid], None, item.present)
            if item.present:
                nouveaux_presents.append(membres[uid])
        else:
            if p.present != item.present:
                _journal_presence(db, moderateur, s, membres[uid], p.present, item.present)
                if item.present:
                    nouveaux_presents.append(membres[uid])
            p.present = item.present
            if item.commentaire is not None:
                p.commentaire = item.commentaire
    if body.remplacer:
        for uid, p in existants.items():
            if uid not in voulus:
                _journal_presence(db, moderateur, s, membres[uid], p.present, None)
                db.delete(p)
    db.commit()
    if nouveaux_presents:
        background.add_task(notifier_participants, s, nouveaux_presents)
    return seance_detail(db, _get(db, sid), moderateur, True)


@router.patch("/{sid}/participants/{uid}", response_model=ParticipationOut)
def update_participant(sid: int, uid: int, body: ParticipationUpdate, db: Session = Depends(get_db),
                       moderateur: Utilisateur = Depends(staff)):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p:
        raise HTTPException(404, "Participation introuvable")
    avant = p.present
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "present" and v is None:
            continue
        setattr(p, k, v)
    if p.present != avant:
        _journal_presence(db, moderateur, _get(db, sid), db.get(Utilisateur, uid), avant, p.present)
    db.commit()
    return p


@router.delete("/{sid}/participants/{uid}", status_code=204)
def remove_participant(sid: int, uid: int, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p:
        raise HTTPException(404, "Participation introuvable")
    _journal_presence(db, moderateur, _get(db, sid), db.get(Utilisateur, uid), p.present, None)
    db.delete(p)
    db.commit()
