from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Participation
from ..schemas import ParticipationCreate, ParticipationUpdate, ParticipationOut
from ..security import require_roles

router = APIRouter(prefix="/participations", tags=["participations"])

@router.get("", response_model=list[ParticipationOut])
def list_participations(
    userId: int | None = None,
    seanceId: int | None = None,
    present: bool | None = None,
    db: Session = Depends(get_db),
    _: any = Depends(require_roles("admin","moderator")),
):
    q = db.query(Participation)
    if userId is not None: q = q.filter(Participation.utilisateur_id == userId)
    if seanceId is not None: q = q.filter(Participation.seance_id == seanceId)
    if present is not None: q = q.filter(Participation.present == present)
    return q.all()

@router.post("", response_model=ParticipationOut, status_code=201)
def create_participation(body: ParticipationCreate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    exists = db.get(Participation, {"utilisateur_id": body.utilisateur_id, "seance_id": body.seance_id})
    if exists: raise HTTPException(409, "Déjà existant")
    p = Participation(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p); return p

@router.patch("", response_model=ParticipationOut)
def patch_participation(userId: int, seanceId: int, body: ParticipationUpdate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    p = db.get(Participation, {"utilisateur_id": userId, "seance_id": seanceId})
    if not p: raise HTTPException(404, "Introuvable")
    for k,v in body.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    db.commit(); db.refresh(p); return p

@router.delete("", status_code=204)
def delete_participation(userId: int, seanceId: int, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    p = db.get(Participation, {"utilisateur_id": userId, "seance_id": seanceId})
    if not p: raise HTTPException(404, "Introuvable")
    db.delete(p); db.commit()
