from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from ..database import get_db
from ..models import Seance, Participation, Utilisateur
from ..schemas import SeanceCreate, SeanceOut, SeanceUpdate, ParticipationCreate, ParticipationOut, ParticipationUpdate
from ..security import require_roles, get_current_user
from ..utils.discord import send_discord_notification_sync

router = APIRouter(prefix="/seances", tags=["seances"])

@router.get("", response_model=list[SeanceOut])
def list_seances(
    semestreId: int | None = None,
    dateFrom: date | None = None,
    dateTo: date | None = None,
    q: str | None = None,
    page: int = 1, limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Seance)
    if semestreId: query = query.filter(Seance.semestre_id == semestreId)
    if dateFrom: query = query.filter(Seance.date_seance >= dateFrom)
    if dateTo:   query = query.filter(Seance.date_seance <= dateTo)
    if q:        query = query.filter(Seance.nom.ilike(f"%{q}%"))
    return query.order_by(Seance.date_seance.desc()).offset((page-1)*limit).limit(limit).all()

@router.get("/{sid}", response_model=SeanceOut)
def get_seance(sid: int, db: Session = Depends(get_db)):
    s = db.get(Seance, sid)
    if not s: raise HTTPException(404, "Séance introuvable")
    return s

@router.post("", response_model=SeanceOut, status_code=201)
def create_seance(body: SeanceCreate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    s = Seance(**body.model_dump())
    db.add(s); db.commit(); db.refresh(s); return s

@router.patch("/{sid}", response_model=SeanceOut)
def update_seance(sid: int, body: SeanceUpdate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    s = db.get(Seance, sid)
    if not s: raise HTTPException(404, "Séance introuvable")
    for k,v in body.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s); return s

@router.delete("/{sid}", status_code=204)
def delete_seance(sid: int, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    s = db.get(Seance, sid)
    if not s: raise HTTPException(404, "Séance introuvable")
    db.delete(s); db.commit()

# --- Participants d’une séance ---
@router.get("/{sid}/participants", response_model=list[ParticipationOut])
def seance_participants(sid: int, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    s = db.get(Seance, sid);
    if not s: raise HTTPException(404, "Séance introuvable")
    return db.query(Participation).filter(Participation.seance_id == sid).all()

@router.post("/{sid}/participants", response_model=ParticipationOut, status_code=201)
def add_participant(sid: int, body: ParticipationCreate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    if body.seance_id != sid:
        raise HTTPException(400, "seance_id incohérent")
    s = db.get(Seance, sid)
    if not s: raise HTTPException(404, "Séance introuvable")
    exists = db.get(Utilisateur, body.utilisateur_id)
    if not exists: raise HTTPException(404, "Utilisateur introuvable")
    p = db.get(Participation, {"utilisateur_id": body.utilisateur_id, "seance_id": sid})
    if p: raise HTTPException(409, "Participation déjà existante")
    p = Participation(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)

    # Envoyer une notification Discord si le participant est présent
    if p.present:
        try:
            send_discord_notification_sync(
                title="🎉 Nouveau participant ajouté !",
                description=f"**{exists.prenom} {exists.nom}** a été ajouté à la séance **{s.nom}**",
                color=0x00ff00,  # Vert
                fields=[
                    {"name": "Points gagnés", "value": f"**{s.nb_point}** points", "inline": True},
                    {"name": "Classe", "value": exists.classe, "inline": True},
                    {"name": "Date de la séance", "value": s.date_seance.strftime("%d/%m/%Y"), "inline": True}
                ]
            )
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi de la notification: {e}")

    return p

@router.patch("/{sid}/participants/{uid}", response_model=ParticipationOut)
def update_participant(sid: int, uid: int, body: ParticipationUpdate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p: raise HTTPException(404, "Participation introuvable")
    for k,v in body.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    db.commit(); db.refresh(p); return p

@router.delete("/{sid}/participants/{uid}", status_code=204)
def remove_participant(sid: int, uid: int, db: Session = Depends(get_db), _: any = Depends(require_roles("admin","moderator"))):
    p = db.get(Participation, {"utilisateur_id": uid, "seance_id": sid})
    if not p: raise HTTPException(404, "Participation introuvable")
    db.delete(p); db.commit()
