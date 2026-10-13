from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Participation, Seance, Semestre, Utilisateur
from ..schemas import (
    AppelBody, ParticipationCreate, ParticipationOut, ParticipationUpdate, SeanceCreate, SeanceDetail,
    SeanceOut, SeanceUpdate,
)
from ..security import get_current_user_optional, is_staff, require_roles
from ..services import seance_detail, seance_out, seances_out
from ..utils.discord import notifier_participants

router = APIRouter(prefix="/seances", tags=["seances"])
staff = require_roles("admin", "moderator")


def _get(db: Session, sid: int) -> Seance:
    s = db.get(Seance, sid, options=[joinedload(Seance.semestre)])
    if not s:
        raise HTTPException(404, "Séance introuvable")
    return s


def _check_semestre(db: Session, semestre_id: int) -> None:
    if not db.get(Semestre, semestre_id):
        raise HTTPException(422, "Semestre inconnu")


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
    return seances_out(db, seances)


@router.get("/{sid}", response_model=SeanceDetail)
def get_seance(sid: int, db: Session = Depends(get_db),
               user: Utilisateur | None = Depends(get_current_user_optional)):
    return seance_detail(db, _get(db, sid), user, is_staff(user))


@router.post("", response_model=SeanceOut, status_code=201)
def create_seance(body: SeanceCreate, db: Session = Depends(get_db), _=Depends(staff)):
    _check_semestre(db, body.semestre_id)
    s = Seance(**body.model_dump())
    db.add(s)
    db.commit()
    return seance_out(db, _get(db, s.id))


@router.patch("/{sid}", response_model=SeanceOut)
def update_seance(sid: int, body: SeanceUpdate, db: Session = Depends(get_db), _=Depends(staff)):
    s = _get(db, sid)
    data = body.model_dump(exclude_unset=True)
    for requis in ("nom", "date_seance", "nb_point", "semestre_id"):
        if requis in data and data[requis] is None:
            data.pop(requis)
    if "semestre_id" in data:
        _check_semestre(db, data["semestre_id"])
    date_changee = "date_seance" in data and data["date_seance"] != s.date_seance
    for k, v in data.items():
        setattr(s, k, v)
    if date_changee and s.date_seance >= date.today():
        # Nouvelle date : on ré-annonce et on reprogramme le rappel
        s.annonce_envoyee = False
        s.rappel_envoye = False
    db.commit()
    return seance_out(db, _get(db, sid))


@router.delete("/{sid}", status_code=204)
def delete_seance(sid: int, db: Session = Depends(get_db), _=Depends(staff)):
    s = _get(db, sid)
    db.delete(s)
    db.commit()


# --- Participants d'une séance ---------------------------------------------------
@router.get("/{sid}/participants", response_model=list[ParticipationOut])
def seance_participants(sid: int, db: Session = Depends(get_db), _=Depends(staff)):
    _get(db, sid)
    return db.query(Participation).filter(Participation.seance_id == sid).all()


@router.post("/{sid}/participants", response_model=ParticipationOut, status_code=201)
def add_participant(sid: int, body: ParticipationCreate, background: BackgroundTasks,
                    db: Session = Depends(get_db), _=Depends(staff)):
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
    if voulus:
        trouves = {u.id: u for u in db.query(Utilisateur).filter(Utilisateur.id.in_(voulus))}
        inconnus = set(voulus) - set(trouves)
        if inconnus:
            raise HTTPException(404, f"Utilisateur(s) introuvable(s) : {sorted(inconnus)}")
    else:
        trouves = {}
    existants = {p.utilisateur_id: p for p in db.query(Participation).filter(Participation.seance_id == sid)}
    nouveaux_presents: list[Utilisateur] = []
    for uid, item in voulus.items():
        p = existants.get(uid)
        if p is None:
            db.add(Participation(utilisateur_id=uid, seance_id=sid, present=item.present, commentaire=item.commentaire))
            if item.present:
                nouveaux_presents.append(trouves[uid])
        else:
            if item.present and not p.present:
                nouveaux_presents.append(trouves[uid])
            p.present = item.present
            if item.commentaire is not None:
                p.commentaire = item.commentaire
    if body.remplacer:
        for uid, p in existants.items():
            if uid not in voulus:
                db.delete(p)
    db.commit()
    if nouveaux_presents:
        background.add_task(notifier_participants, s, nouveaux_presents)
    return seance_detail(db, _get(db, sid), moderateur, True)


@router.patch("/{sid}/participants/{uid}", response_model=ParticipationOut)
def update_participant(sid: int, uid: int, body: ParticipationUpdate, db: Session = Depends(get_db), _=Depends(staff)):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p:
        raise HTTPException(404, "Participation introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "present" and v is None:
            continue
        setattr(p, k, v)
    db.commit()
    return p


@router.delete("/{sid}/participants/{uid}", status_code=204)
def remove_participant(sid: int, uid: int, db: Session = Depends(get_db), _=Depends(staff)):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p:
        raise HTTPException(404, "Participation introuvable")
    db.delete(p)
    db.commit()
