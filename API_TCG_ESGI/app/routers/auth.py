from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Utilisateur
from ..schemas import LoginRequest, Token
from ..security import create_token, get_current_user, verify_password
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # 1) Trouver l'utilisateur par email
    user = db.query(Utilisateur).filter(Utilisateur.adresse_mail == body.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    # 2) Vérifier le mot de passe (NB: le hash est dans mot_de_passe_hash)
    if not verify_password(body.password, user.mot_de_passe_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    # 3) OK -> token
    return Token(access_token=create_token(user))


@router.get("/me")
def me(user: Utilisateur = Depends(get_current_user)):
    # expose les deux clés d'email pour compat descendante
    return {
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.adresse_mail,
        "adresse_mail": user.adresse_mail,
        "role_utilisateur": user.role_utilisateur,
        "classe": user.classe,
    }