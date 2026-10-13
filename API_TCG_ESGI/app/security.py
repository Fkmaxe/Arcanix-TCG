from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from .models import Utilisateur


pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # bcrypt_sha256 par défaut, bcrypt en fallback
    deprecated="auto",
    bcrypt__rounds=12,
)
ALGO = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-me")
bearer_required = HTTPBearer()
bearer_optional = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hache un mot de passe en utilisant le contexte par défaut (bcrypt)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe non haché contre un hachage stocké."""
    return pwd_context.verify(plain_password, hashed_password)

def create_token(user: Utilisateur) -> str:
    payload = {
        "sub": str(user.id),
        "role_utilisateur": user.role_utilisateur,
        "email": user.adresse_mail,
        "nom": user.nom,
        "prenom": user.prenom,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGO)

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_required),
    db: Session = Depends(get_db),
) -> Utilisateur:
    token = creds.credentials
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[ALGO])
        uid = int(data.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    user = db.get(Utilisateur, uid)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user

def require_roles(*roles: str):
    def _guard(user: Utilisateur = Depends(get_current_user)):
        if user.role_utilisateur not in roles:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return user
    return _guard


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
    db: Session = Depends(get_db),
) -> Utilisateur | None:
    # Pas de header -> None
    if not creds:
        return None
    # Header présent -> on tente le decode
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[ALGO])
        uid = int(data.get("sub"))
    except (JWTError, ValueError):
        return None
    return db.get(Utilisateur, uid)

