from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..journal import journaliser
from ..models import Seance, Semestre
from ..schemas import SemestreCreate, SemestreOut, SemestreUpdate
from ..security import require_roles
from ..services import semestre_actif

router = APIRouter(prefix="/semestres", tags=["semestres"])


def _doublon(db: Session, annee: int, numero: int, sauf_id: int | None = None) -> bool:
    q = db.query(Semestre).filter(Semestre.annee == annee, Semestre.numero == numero)
    if sauf_id:
        q = q.filter(Semestre.id != sauf_id)
    return db.query(q.exists()).scalar()


@router.get("", response_model=list[SemestreOut])
def list_semestres(db: Session = Depends(get_db)):
    return db.query(Semestre).order_by(Semestre.annee.desc(), Semestre.numero.desc()).all()


@router.get("/actif", response_model=SemestreOut | None)
def get_semestre_actif(db: Session = Depends(get_db)):
    return semestre_actif(db)


@router.get("/{sid}", response_model=SemestreOut)
def get_semestre(sid: int, db: Session = Depends(get_db)):
    s = db.get(Semestre, sid)
    if not s:
        raise HTTPException(404, "Semestre introuvable")
    return s


@router.post("", response_model=SemestreOut, status_code=201)
def create_semestre(body: SemestreCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    if _doublon(db, body.annee, body.numero):
        raise HTTPException(409, f"Le semestre {body.annee} S{body.numero} existe déjà")
    premier = db.query(Semestre).count() == 0
    s = Semestre(annee=body.annee, numero=body.numero, actif=premier)
    db.add(s)
    db.commit()
    return s


@router.patch("/{sid}", response_model=SemestreOut)
def update_semestre(sid: int, body: SemestreUpdate, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    s = db.get(Semestre, sid)
    if not s:
        raise HTTPException(404, "Semestre introuvable")
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    annee, numero = data.get("annee", s.annee), data.get("numero", s.numero)
    if _doublon(db, annee, numero, sid):
        raise HTTPException(409, f"Le semestre {annee} S{numero} existe déjà")
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    return s


@router.post("/{sid}/activer", response_model=SemestreOut)
def activer_semestre(sid: int, db: Session = Depends(get_db), admin=Depends(require_roles("admin"))):
    """Définit le semestre courant. L'ancien est clôturé : son podium sera annoncé sur Discord."""
    s = db.get(Semestre, sid)
    if not s:
        raise HTTPException(404, "Semestre introuvable")
    if s.actif:
        return s
    for ancien in db.query(Semestre).filter(Semestre.actif.is_(True)):
        ancien.actif = False
        ancien.podium_annonce = False
    db.flush()
    s.actif = True
    journaliser(db, admin, "semestre.activation", f"Semestre {s.annee} S{s.numero} défini comme semestre en cours")
    db.commit()
    return s


@router.delete("/{sid}", status_code=204)
def delete_semestre(sid: int, db: Session = Depends(get_db), admin=Depends(require_roles("admin"))):
    s = db.get(Semestre, sid)
    if not s:
        raise HTTPException(404, "Semestre introuvable")
    nb = db.query(func.count(Seance.id)).filter(Seance.semestre_id == sid).scalar()
    if nb:
        raise HTTPException(409, f"Ce semestre contient {nb} séance(s) : supprimez-les ou déplacez-les d'abord")
    if s.actif:
        raise HTTPException(409, "Impossible de supprimer le semestre actif")
    from ..models import Ajustement
    if db.query(Ajustement).filter(Ajustement.semestre_id == sid).first():
        raise HTTPException(409, "Ce semestre contient des points bonus/malus : supprime-les d'abord")
    journaliser(db, admin, "semestre.suppression", f"Semestre {s.annee} S{s.numero} supprimé")
    db.delete(s)
    db.commit()
