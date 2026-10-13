"""Routes réservées au bot Discord (en-tête x-bot-token obligatoire)."""
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Participation, Seance, Semestre, Utilisateur
from .. import vie
from ..journal import journaliser
from ..schemas import (
    AjustementOut, Annonce, AnnonceAck, Classement, DiscordAjustement, DiscordIdBody, DiscordInscription,
    DiscordInscriptionOut, DiscordLier, DiscordMembre, DiscordPresences, DiscordPresencesOut, DiscordRegister,
    DiscordRoles, DiscordSeanceCreate, LienMotDePasse, MaParticipation, SeanceOut, SemestreOut,
)
from .ajustements import ajustement_out, creer_ajustement
from .seances import notifier_promus
from ..security import consommer_jeton, lien_mot_de_passe, unusable_password_hash, verify_bot_token
from ..services import (
    classement, lignes_publiques, points_par_semestre, resoudre_semestre, resultats_out, seance_out, seances_out,
    semestre_actif, stats_membre,
)

router = APIRouter(prefix="/discord", tags=["discord"], dependencies=[Depends(verify_bot_token)])


def _membre(db: Session, discord_id: str) -> Utilisateur:
    u = db.query(Utilisateur).filter(Utilisateur.discord_id == str(discord_id)).first()
    if not u:
        raise HTTPException(404, "Aucun compte Arcanix n'est lié à ce compte Discord")
    return u


def _moderateur(db: Session, discord_id: str) -> Utilisateur:
    u = _membre(db, discord_id)
    if u.role_utilisateur not in ("admin", "moderator"):
        raise HTTPException(403, "Commande réservée à la modération")
    return u


# --- Compte --------------------------------------------------------------------------
@router.post("/inscription", response_model=LienMotDePasse, status_code=201)
def inscription(body: DiscordRegister, db: Session = Depends(get_db)):
    if db.query(Utilisateur).filter(Utilisateur.discord_id == body.discord_id).first():
        raise HTTPException(409, "Ce compte Discord est déjà inscrit")
    if db.query(Utilisateur).filter(func.lower(Utilisateur.adresse_mail) == body.adresse_mail).first():
        raise HTTPException(409, "Cet email a déjà un compte : connecte-toi sur le site puis utilise /lier")
    user = Utilisateur(
        discord_id=body.discord_id, nom=body.nom, prenom=body.prenom, adresse_mail=body.adresse_mail,
        classe=body.classe, role_utilisateur="user",
        mot_de_passe_hash=unusable_password_hash(), doit_changer_mdp=True,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Compte déjà existant") from None
    url, heures = lien_mot_de_passe(db, user)
    journaliser(db, user, "membre.inscription_discord", f"{user.prenom} {user.nom} s'est inscrit·e via Discord",
                membre_id=user.id)
    db.commit()
    return LienMotDePasse(url=url, expire_dans_heures=heures)


@router.post("/lier", response_model=DiscordMembre)
def lier(body: DiscordLier, db: Session = Depends(get_db)):
    deja = db.query(Utilisateur).filter(Utilisateur.discord_id == body.discord_id).first()
    user = consommer_jeton(db, body.code, "lier_discord")
    if deja and deja.id != user.id:
        db.rollback()
        raise HTTPException(409, "Ce compte Discord est déjà lié à un autre compte Arcanix")
    user.discord_id = body.discord_id
    journaliser(db, user, "membre.liaison_discord", f"{user.prenom} {user.nom} a lié son compte Discord", membre_id=user.id)
    db.commit()
    return _profil(db, user)


@router.post("/reinitialiser", response_model=LienMotDePasse)
def reinitialiser(body: DiscordIdBody, db: Session = Depends(get_db)):
    user = _membre(db, body.discord_id)
    url, heures = lien_mot_de_passe(db, user)
    db.commit()
    return LienMotDePasse(url=url, expire_dans_heures=heures)


# --- Consultation --------------------------------------------------------------------
def _profil(db: Session, user: Utilisateur) -> DiscordMembre:
    stats = stats_membre(db, user, semestre_actif(db))
    total = sum(s["points"] for s in points_par_semestre(db, user.id))
    return DiscordMembre(
        prenom=user.prenom, nom=user.nom, classe=user.classe, role_utilisateur=user.role_utilisateur,
        semestre=stats["semestre"], points=stats["points"], rang=stats["rang"],
        presences=stats["presences"], total_points=total,
    )


@router.get("/membres/{discord_id}", response_model=DiscordMembre)
def membre(discord_id: str, db: Session = Depends(get_db)):
    return _profil(db, _membre(db, discord_id))


@router.get("/membres/{discord_id}/historique", response_model=list[MaParticipation])
def historique(discord_id: str, limit: int = 10, db: Session = Depends(get_db)):
    user = _membre(db, discord_id)
    rows = (
        db.query(Participation, Seance)
        .join(Seance, Seance.id == Participation.seance_id)
        .filter(Participation.utilisateur_id == user.id)
        .order_by(Seance.date_seance.desc(), Seance.id.desc())
        .limit(min(max(limit, 1), 25))
        .all()
    )
    return [
        MaParticipation(seance_id=s.id, seance_nom=s.nom, date_seance=s.date_seance, jeu=s.jeu,
                        nb_point=float(s.nb_point), present=p.present, commentaire=p.commentaire,
                        semestre_id=s.semestre_id)
        for p, s in rows
    ]


# Compatibilité avec l'ancien bot (/mypoint)
@router.get("/points/discord/{discord_id}")
def get_points_discord(discord_id: str, db: Session = Depends(get_db)):
    p = membre(discord_id, db)
    if not p.semestre:
        raise HTTPException(404, "Aucun semestre défini")
    return {"discord_id": discord_id, "semestre": p.semestre, "points": p.points}


@router.get("/classement", response_model=Classement)
def classement_discord(semestreId: int | None = None, limit: int = 10, db: Session = Depends(get_db)):
    semestre = resoudre_semestre(db, semestreId)
    if not semestre:
        return Classement(semestre=None, lignes=[])
    lignes = classement(db, semestre.id)
    return Classement(semestre=SemestreOut.model_validate(semestre),
                      lignes=lignes_publiques(lignes[: min(max(limit, 1), 50)], None, False))


@router.get("/semestres", response_model=list[SemestreOut])
def semestres(db: Session = Depends(get_db)):
    return db.query(Semestre).order_by(Semestre.annee.desc(), Semestre.numero.desc()).all()


@router.get("/seances/a-venir", response_model=list[SeanceOut])
def seances_a_venir(limit: int = 5, db: Session = Depends(get_db)):
    q = (
        db.query(Seance).options(joinedload(Seance.semestre))
        .filter(Seance.date_seance >= date.today())
        .order_by(Seance.date_seance, Seance.heure_debut.asc().nulls_last(), Seance.id)
        .limit(min(max(limit, 1), 25))
    )
    return seances_out(db, q.all())


@router.get("/seances/recherche", response_model=list[SeanceOut])
def seances_recherche(q: str | None = None, db: Session = Depends(get_db)):
    """Pour l'autocomplétion : séances récentes (±30 jours) filtrées par nom."""
    query = db.query(Seance).options(joinedload(Seance.semestre)).filter(
        Seance.date_seance >= date.today() - timedelta(days=30),
        Seance.date_seance <= date.today() + timedelta(days=30),
    )
    if q:
        query = query.filter(Seance.nom.ilike(f"%{q}%"))
    seances = query.order_by(func.abs(Seance.date_seance - date.today()), Seance.id.desc()).limit(25).all()
    return seances_out(db, seances)


# --- Modération ------------------------------------------------------------------------
@router.post("/seances", response_model=SeanceOut, status_code=201)
def creer_seance(body: DiscordSeanceCreate, db: Session = Depends(get_db)):
    auteur = _moderateur(db, body.auteur_discord_id)
    semestre = resoudre_semestre(db, body.semestre_id)
    if not semestre:
        raise HTTPException(422, "Aucun semestre défini : créez-en un sur le site")
    data = body.model_dump(exclude={"auteur_discord_id", "semestre_id"})
    s = Seance(**data, semestre_id=semestre.id)
    db.add(s)
    db.flush()
    journaliser(db, auteur, "seance.creation", f"Séance « {s.nom} » du {s.date_seance:%d/%m/%Y} créée depuis Discord",
                seance_id=s.id)
    db.commit()
    return seance_out(db, s)


@router.post("/seances/{sid}/presences", response_model=DiscordPresencesOut)
def presences(sid: int, body: DiscordPresences, db: Session = Depends(get_db)):
    auteur = _moderateur(db, body.auteur_discord_id)
    s = db.get(Seance, sid)
    if not s:
        raise HTTPException(404, "Séance introuvable")
    ids = list(dict.fromkeys(str(i) for i in body.discord_ids))
    membres = {u.discord_id: u for u in db.query(Utilisateur).filter(Utilisateur.discord_id.in_(ids))}
    existants = {p.utilisateur_id: p for p in db.query(Participation).filter(Participation.seance_id == sid)}
    ajoutes, deja, non_lies = [], [], []
    for did in ids:
        u = membres.get(did)
        if not u:
            non_lies.append(did)
            continue
        p = existants.get(u.id)
        if p and p.present:
            deja.append(did)
            continue
        avant = p.present if p else None
        if p:
            p.present = True
        else:
            db.add(Participation(utilisateur_id=u.id, seance_id=sid, present=True))
        ajoutes.append(did)
        journaliser(db, auteur, "presence.ajout" if not p else "presence.modification",
                    f"{u.prenom} {u.nom} présent·e à « {s.nom} » (+{float(s.nb_point):g} pts, via Discord)",
                    membre_id=u.id, seance_id=s.id, details={"avant": avant, "apres": True,
                                                             "points": float(s.nb_point)})
    db.commit()
    return DiscordPresencesOut(seance=seance_out(db, s), ajoutes=ajoutes, deja_presents=deja, non_lies=non_lies)


# --- Annonces automatiques -------------------------------------------------------------
@router.get("/annonces/en-attente", response_model=list[Annonce])
def annonces_en_attente(db: Session = Depends(get_db)):
    aujourd_hui = date.today()
    annonces: list[Annonce] = []

    nouvelles = (db.query(Seance).options(joinedload(Seance.semestre))
                 .filter(Seance.annonce_envoyee.is_(False), Seance.date_seance >= aujourd_hui)
                 .order_by(Seance.date_seance).limit(10).all())
    for s in seances_out(db, nouvelles):
        annonces.append(Annonce(type="nouvelle_seance", id=s.id, seance=s))

    demain = aujourd_hui + timedelta(days=1)
    rappels = (db.query(Seance).options(joinedload(Seance.semestre))
               .filter(Seance.rappel_envoye.is_(False), Seance.annonce_envoyee.is_(True),
                       Seance.date_seance == demain).all())
    for s in seances_out(db, rappels):
        annonces.append(Annonce(type="rappel", id=s.id, seance=s))

    tournois = (db.query(Seance).options(joinedload(Seance.semestre))
                .filter(Seance.resultats_a_annoncer.is_(True)).order_by(Seance.date_seance).limit(5).all())
    for s in seances_out(db, tournois):
        annonces.append(Annonce(type="resultats", id=s.id, seance=s, resultats=resultats_out(db, s.id, None, False)[:8]))

    for sem in db.query(Semestre).filter(Semestre.podium_annonce.is_(False), Semestre.actif.is_(False)):
        lignes = classement(db, sem.id)[:3]
        annonces.append(Annonce(type="podium", id=sem.id, semestre=SemestreOut.model_validate(sem),
                                podium=lignes_publiques(lignes, None, False)))
    return annonces


@router.post("/annonces/ack", status_code=204)
def annonces_ack(body: list[AnnonceAck], db: Session = Depends(get_db)):
    for a in body:
        if a.type == "podium":
            sem = db.get(Semestre, a.id)
            if sem:
                sem.podium_annonce = True
            continue
        s = db.get(Seance, a.id)
        if not s:
            continue
        if a.type == "resultats":
            s.resultats_a_annoncer = False
        elif a.type == "nouvelle_seance":
            s.annonce_envoyee = True
            # Séance créée la veille : l'annonce fait office de rappel
            if s.date_seance <= date.today() + timedelta(days=1):
                s.rappel_envoye = True
        else:
            s.rappel_envoye = True
    db.commit()



# --- Inscriptions par bouton (« Je viens ») ------------------------------------------------------
@router.post("/seances/{sid}/inscription", response_model=DiscordInscriptionOut)
def inscription_seance(sid: int, body: DiscordInscription, background: BackgroundTasks, db: Session = Depends(get_db)):
    user = _membre(db, body.discord_id)
    s = db.get(Seance, sid, options=[joinedload(Seance.semestre)])
    if not s:
        raise HTTPException(404, "Séance introuvable")
    promus = []
    if body.action == "in":
        statut = vie.inscrire(db, s, user)
    else:
        promus = vie.desinscrire(db, s, user)
        statut = None
    db.commit()
    notifier_promus(background, s, promus)
    return DiscordInscriptionOut(statut=statut, seance=seance_out(db, s, user),
                                 promus=[u.discord_id for u in promus if u.discord_id])


# --- Bonus / malus ---------------------------------------------------------------------------
@router.post("/ajustements", response_model=AjustementOut, status_code=201)
def ajustement(body: DiscordAjustement, db: Session = Depends(get_db)):
    auteur = _moderateur(db, body.auteur_discord_id)
    cible = db.query(Utilisateur).filter(Utilisateur.discord_id == body.discord_id).first()
    if not cible:
        raise HTTPException(404, "Ce membre n'a pas lié son compte Arcanix")
    if body.points == 0:
        raise HTTPException(422, "Les points doivent être différents de 0")
    a = creer_ajustement(db, auteur, cible, round(body.points, 2), body.motif.strip(), body.categorie, semestre_actif(db))
    db.commit()
    db.refresh(a)
    return ajustement_out(a)


# --- Rôles automatiques -------------------------------------------------------------------------
@router.get("/roles", response_model=DiscordRoles)
def roles(db: Session = Depends(get_db)):
    """Comptes liés (rôle Membre) et top 3 du semestre en cours (rôle spécial)."""
    lies = [d for (d,) in db.query(Utilisateur.discord_id).filter(Utilisateur.discord_id.isnot(None))]
    sem = semestre_actif(db)
    top3 = [l["discord_id"] for l in classement(db, sem.id) if l["rang"] <= 3 and l["discord_id"]] if sem else []
    return DiscordRoles(membres=lies, top3=top3)
