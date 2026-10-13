"""Consultation de l'historique des modifications (modération)."""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Journal
from ..schemas import JournalOut
from ..security import require_roles

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("", response_model=list[JournalOut])
def lister(response: Response, membreId: int | None = None, seanceId: int | None = None, auteurId: int | None = None,
           action: str | None = None, depuis: date | None = None, jusqua: date | None = None,
           page: int = 1, limit: int = 50, db: Session = Depends(get_db),
           _=Depends(require_roles("admin", "moderator"))):
    page, limit = max(page, 1), min(max(limit, 1), 200)
    q = db.query(Journal)
    if membreId:
        q = q.filter(Journal.membre_id == membreId)
    if seanceId:
        q = q.filter(Journal.seance_id == seanceId)
    if auteurId:
        q = q.filter(Journal.auteur_id == auteurId)
    if action:  # préfixe : 'presence', 'points', 'membre'…
        q = q.filter(Journal.action.like(f"{action}%"))
    if depuis:
        q = q.filter(Journal.cree_le >= datetime.combine(depuis, time.min))
    if jusqua:
        q = q.filter(Journal.cree_le < datetime.combine(jusqua + timedelta(days=1), time.min))
    response.headers["X-Total-Count"] = str(q.count())
    return q.order_by(Journal.cree_le.desc(), Journal.id.desc()).offset((page - 1) * limit).limit(limit).all()
