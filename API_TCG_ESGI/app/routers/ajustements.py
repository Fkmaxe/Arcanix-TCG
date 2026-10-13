"""Points bonus / malus hors présence."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..journal import journaliser
from ..models import Ajustement, Semestre, Utilisateur
from ..schemas import AjustementIn, AjustementOut, SemestreOut
from ..security import require_roles
from ..services import semestre_actif

router = APIRouter(prefix="/ajustements", tags=["ajustements"])
staff = require_roles("admin", "moderator")


def ajustement_out(a: Ajustement) -> AjustementOut:
    return AjustementOut(
        id=a.id, utilisateur_id=a.utilisateur_id, prenom=a.utilisateur.prenom, nom=a.utilisateur.nom,
        semestre=SemestreOut.model_validate(a.semestre), seance_id=a.seance_id, points=float(a.points),
        categorie=a.categorie, motif=a.motif,
        cree_par=f"{a.cree_par.prenom} {a.cree_par.nom}" if a.cree_par else None, cree_le=a.cree_le,
    )


def creer_ajustement(db: Session, auteur: Utilisateur, cible: Utilisateur, points: float, motif: str,
                     categorie: str, semestre: Semestre | None) -> Ajustement:
    if not semestre:
        raise HTTPException(422, "Aucun semestre défini")
    a = Ajustement(utilisateur_id=cible.id, semestre_id=semestre.id, points=points, motif=motif,
                   categorie=categorie, cree_par_id=auteur.id)
    db.add(a)
    db.flush()
    signe = f"+{points:g}" if points > 0 else f"{points:g}"
    journaliser(db, auteur, "points.ajustement", f"{signe} pts pour {cible.prenom} {cible.nom} : {motif}",
                membre_id=cible.id, details={"ajustement_id": a.id, "points": points, "categorie": categorie,
                                             "semestre_id": semestre.id})
    return a


def _query(db: Session):
    return db.query(Ajustement).options(
        joinedload(Ajustement.utilisateur), joinedload(Ajustement.cree_par), joinedload(Ajustement.semestre))


@router.get("", response_model=list[AjustementOut])
def lister(response: Response, semestreId: int | None = None, userId: int | None = None, categorie: str | None = None,
           page: int = 1, limit: int = 50, db: Session = Depends(get_db), _=Depends(staff)):
    page, limit = max(page, 1), min(max(limit, 1), 200)
    q = _query(db)
    if semestreId:
        q = q.filter(Ajustement.semestre_id == semestreId)
    if userId:
        q = q.filter(Ajustement.utilisateur_id == userId)
    if categorie:
        q = q.filter(Ajustement.categorie == categorie)
    response.headers["X-Total-Count"] = str(q.count())
    rows = q.order_by(Ajustement.cree_le.desc(), Ajustement.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return [ajustement_out(a) for a in rows]


@router.post("", response_model=AjustementOut, status_code=201)
def creer(body: AjustementIn, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    cible = db.get(Utilisateur, body.utilisateur_id)
    if not cible:
        raise HTTPException(404, "Membre introuvable")
    semestre = db.get(Semestre, body.semestre_id) if body.semestre_id else semestre_actif(db)
    a = creer_ajustement(db, moderateur, cible, body.points, body.motif, body.categorie, semestre)
    db.commit()
    return ajustement_out(_query(db).filter(Ajustement.id == a.id).one())


@router.delete("/{aid}", status_code=204)
def supprimer(aid: int, db: Session = Depends(get_db), moderateur: Utilisateur = Depends(staff)):
    a = _query(db).filter(Ajustement.id == aid).first()
    if not a:
        raise HTTPException(404, "Ajustement introuvable")
    if a.seance_id and a.categorie == "tournoi":
        raise HTTPException(409, "Bonus de tournoi : modifie plutôt les résultats du tournoi")
    journaliser(db, moderateur, "points.annulation",
                f"Annulation de {float(a.points):+g} pts pour {a.utilisateur.prenom} {a.utilisateur.nom} ({a.motif})",
                membre_id=a.utilisateur_id, details={"ajustement_id": a.id, "points": float(a.points)})
    db.delete(a)
    db.commit()
