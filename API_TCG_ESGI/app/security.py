import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, UTC

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import Jeton, Utilisateur

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # bcrypt_sha256 par défaut, bcrypt en fallback
    deprecated="auto",
    bcrypt__rounds=12,
)
ALGO = "HS256"
bearer_required = HTTPBearer(auto_error=False)
bearer_optional = HTTPBearer(auto_error=False)


def utcnow() -> datetime:
    return datetime.now(UTC)


# --- Mots de passe -------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def unusable_password_hash() -> str:
    """Hash d'un mot de passe aléatoire que personne ne connaît."""
    return hash_password(secrets.token_urlsafe(32))


# --- JWT -----------------------------------------------------------------------
def create_token(user: Utilisateur) -> str:
    now = utcnow()
    payload = {
        "sub": str(user.id),
        "role_utilisateur": user.role_utilisateur,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=config.JWT_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGO)


def _user_from_token(token: str, db: Session) -> Utilisateur | None:
    try:
        data = jwt.decode(token, config.JWT_SECRET, algorithms=[ALGO])
        uid = int(data.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
    return db.get(Utilisateur, uid)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_required),
    db: Session = Depends(get_db),
) -> Utilisateur:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise",
                            headers={"WWW-Authenticate": "Bearer"})
    user = _user_from_token(creds.credentials, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée ou invalide",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
    db: Session = Depends(get_db),
) -> Utilisateur | None:
    if not creds:
        return None
    return _user_from_token(creds.credentials, db)


def require_roles(*roles: str):
    def _guard(user: Utilisateur = Depends(get_current_user)):
        if user.role_utilisateur not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé")
        return user
    return _guard


def is_staff(user: Utilisateur | None) -> bool:
    return bool(user) and user.role_utilisateur in ("admin", "moderator")


# --- Bot Discord ---------------------------------------------------------------
def verify_bot_token(x_bot_token: str | None = Header(default=None)):
    expected = config.DISCORD_BOT_TOKEN
    if not expected or not x_bot_token or not hmac.compare_digest(x_bot_token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token du bot invalide")


# --- Jetons à usage unique -------------------------------------------------------
def _hash_jeton(valeur: str, type_: str) -> str:
    valeur = valeur.strip()
    if type_ == "lier_discord":  # code saisi à la main : insensible à la casse
        valeur = valeur.upper()
    return hashlib.sha256(f"{type_}:{valeur}".encode()).hexdigest()


def creer_jeton(db: Session, user: Utilisateur, type_: str) -> tuple[str, int]:
    """Crée un jeton et invalide les précédents du même type. Retourne (valeur, durée)."""
    now = utcnow()
    for j in db.query(Jeton).filter(Jeton.utilisateur_id == user.id, Jeton.type == type_,
                                    Jeton.utilise_le.is_(None)):
        j.utilise_le = now
    if type_ == "lier_discord":
        # Code court lisible (sans 0/O/1/I)
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        valeur = "".join(secrets.choice(alphabet) for _ in range(6))
        duree = config.JETON_DISCORD_MINUTES
        expire = now + timedelta(minutes=duree)
    else:
        valeur = secrets.token_urlsafe(32)
        duree = config.JETON_MDP_HEURES
        expire = now + timedelta(hours=duree)
    db.add(Jeton(utilisateur_id=user.id, type=type_, hash=_hash_jeton(valeur, type_), expire_le=expire))
    db.flush()
    return valeur, duree


def consommer_jeton(db: Session, valeur: str, type_: str) -> Utilisateur:
    j = db.query(Jeton).filter(Jeton.hash == _hash_jeton(valeur, type_), Jeton.type == type_).first()
    if not j or j.utilise_le is not None or j.expire_le < utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Lien ou code invalide ou expiré")
    j.utilise_le = utcnow()
    return j.utilisateur


def lien_mot_de_passe(db: Session, user: Utilisateur) -> tuple[str, int]:
    valeur, duree = creer_jeton(db, user, "definir_mdp")
    return f"{config.FRONTEND_URL}/activer?jeton={valeur}", duree
