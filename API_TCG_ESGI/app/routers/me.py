from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, func
from ..database import get_db
from ..models import Utilisateur, Participation, Seance, Semestre
from ..schemas import ParticipationOut, MyPointsOut, PointsSemestre
from ..security import get_current_user

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/participations", response_model=list[ParticipationOut])
def my_participations(
    semestreId: int | None = None,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
):
    q = db.query(Participation).filter(Participation.utilisateur_id == user.id)
    if semestreId:
        q = q.join(Seance, Participation.seance_id == Seance.id).filter(Seance.semestre_id == semestreId)
    return q.all()


@router.get("/points")
def my_points(db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    # SUM(nb_point) uniquement pour les présences ; COALESCE -> 0 si NULL
    points_expr = func.coalesce(
        func.sum(Seance.nb_point).filter(Participation.present.is_(True)),
        0
    ).label("points")

    stmt = (
        select(
            Semestre.id.label("semestre_id"),
            Semestre.annee,
            Semestre.numero,
            points_expr,
        )
        .join(Seance, Seance.semestre_id == Semestre.id)
        .join(Participation, Participation.seance_id == Seance.id)
        .where(Participation.utilisateur_id == user.id)
        .group_by(Semestre.id, Semestre.annee, Semestre.numero)
        .order_by(Semestre.annee.desc(), Semestre.numero.desc())
    )

    rows = db.execute(stmt).all()

    # ✅ Cas “aucune séance / aucun semestre” : renvoyer structure vide + total 0
    if not rows:
        return {
            "userId": user.id,
            "semestres": [],
            "total": 0,
        }

    semestres = [
        {"semestre_id": r.semestre_id, "annee": r.annee, "numero": r.numero, "points": int(r.points or 0)}
        for r in rows
    ]
    total = sum(s["points"] for s in semestres)

    return {
        "userId": user.id,
        "semestres": semestres,
        "total": total,
    }