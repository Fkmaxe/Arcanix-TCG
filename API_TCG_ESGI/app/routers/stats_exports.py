from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi.responses import StreamingResponse
from io import StringIO
import csv

from ..database import get_db
from ..models import Participation, Seance, Semestre, Utilisateur
from ..security import require_roles

router = APIRouter(tags=["stats","exports"])

@router.get("/stats/points")
def stats_points(
    semestreId: int | None = None,
    classe: str | None = None,
    userId: int | None = None,
    db: Session = Depends(get_db),
    _: any = Depends(require_roles("admin","moderator")),
):
    q = (
        db.query(
            Utilisateur.id.label("user_id"),
            Utilisateur.nom, Utilisateur.prenom, Utilisateur.classe,
            func.coalesce(func.sum(case((Participation.present, Seance.nb_point), else_=0)), 0).label("points")
        )
        .join(Participation, Participation.utilisateur_id == Utilisateur.id, isouter=True)
        .join(Seance, Participation.seance_id == Seance.id, isouter=True)
    )
    if semestreId:
        q = q.filter(Seance.semestre_id == semestreId)
    if classe:
        q = q.filter(Utilisateur.classe == classe)
    if userId:
        q = q.filter(Utilisateur.id == userId)
    q = q.group_by(Utilisateur.id, Utilisateur.nom, Utilisateur.prenom, Utilisateur.classe).order_by(func.coalesce(func.sum(case((Participation.present, Seance.nb_point), else_=0)), 0).desc())
    rows = q.all()
    return [{"userId": r.user_id, "nom": r.nom, "prenom": r.prenom, "classe": r.classe, "points": float(r.points or 0)} for r in rows]

@router.get("/exports/participations.csv")
def export_participations_csv(
    semestreId: int | None = None,
    db: Session = Depends(get_db),
    _: any = Depends(require_roles("admin","moderator")),
):
    q = (
        db.query(
            Participation.utilisateur_id, Participation.seance_id,
            Participation.present, Participation.commentaire,
            Seance.date_seance, Seance.nb_point, Seance.nom.label("seance_nom")
        )
        .join(Seance, Seance.id == Participation.seance_id)
    )
    if semestreId:
        q = q.filter(Seance.semestre_id == semestreId)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["utilisateur_id","seance_id","present","commentaire","date_seance","nb_point","seance_nom"])
    for r in q.all():
        writer.writerow([r.utilisateur_id, r.seance_id, r.present, r.commentaire or "", r.date_seance, r.nb_point, r.seance_nom])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=participations.csv"})
