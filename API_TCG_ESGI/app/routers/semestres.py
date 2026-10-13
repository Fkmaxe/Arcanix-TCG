from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Semestre
from ..schemas import SemestreCreate, SemestreOut, SemestreUpdate
from ..security import require_roles, get_current_user

router = APIRouter(prefix="/semestres", tags=["semestres"])

@router.get("", response_model=list[SemestreOut])
def list_semestres(db: Session = Depends(get_db)):
    return db.query(Semestre).order_by(Semestre.annee, Semestre.numero).all()

@router.get("/{sid}", response_model=SemestreOut)
def get_semestre(sid: int, db: Session = Depends(get_db)):
    s = db.get(Semestre, sid)
    if not s: raise HTTPException(404, "Semestre introuvable")
    return s

@router.post("", response_model=SemestreOut, status_code=201)
def create_semestre(body: SemestreCreate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin"))):
    exists = db.query(Semestre).filter(Semestre.annee==body.annee, Semestre.numero==body.numero).first()
    if exists: raise HTTPException(409, "Semestre déjà existant")
    s = Semestre(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@router.patch("/{sid}", response_model=SemestreOut)
def update_semestre(sid: int, body: SemestreUpdate, db: Session = Depends(get_db), _: any = Depends(require_roles("admin"))):
    s = db.get(Semestre, sid)
    if not s: raise HTTPException(404, "Semestre introuvable")
    data = body.model_dump(exclude_unset=True)
    if "annee" in data or "numero" in data:
        annee = data.get("annee", s.annee)
        numero = data.get("numero", s.numero)
        dup = db.query(Semestre).filter(Semestre.annee==annee, Semestre.numero==numero, Semestre.id!=sid).first()
        if dup: raise HTTPException(409, "Doublon (annee, numero)")
    for k,v in data.items(): setattr(s, k, v)
    db.commit(); db.refresh(s); return s

@router.delete("/{sid}", status_code=204)
def delete_semestre(sid: int, db: Session = Depends(get_db), _: any = Depends(require_roles("admin"))):
    s = db.get(Semestre, sid)
    if not s: raise HTTPException(404, "Semestre introuvable")
    # Laisse l'ON DELETE RESTRICT côté FK seance -> semestre protéger si utilisé
    db.delete(s); db.commit()
