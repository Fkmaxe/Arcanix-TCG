from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..ratelimit import connexion, ip_client
from ..models import Utilisateur
from ..schemas import DefinirMotDePasse, LoginRequest, MeOut, Token
from ..security import consommer_jeton, create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def me_out(user: Utilisateur) -> MeOut:
    return MeOut(
        id=user.id, nom=user.nom, prenom=user.prenom,
        email=user.adresse_mail, adresse_mail=user.adresse_mail,
        role_utilisateur=user.role_utilisateur, classe=user.classe,
        doit_changer_mdp=user.doit_changer_mdp, discord_lie=bool(user.discord_id),
    )


@router.post("/login", response_model=Token)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    cle = f"{ip_client(request)}|{body.email}"
    connexion.verifier(cle)
    user = db.query(Utilisateur).filter(Utilisateur.adresse_mail == body.email).first()
    if not user or not verify_password(body.password, user.mot_de_passe_hash):
        connexion.echec(cle)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect")
    connexion.reussite(cle)
    return Token(access_token=create_token(user))


@router.post("/definir-mot-de-passe", response_model=Token)
def definir_mot_de_passe(body: DefinirMotDePasse, request: Request, db: Session = Depends(get_db)):
    """Active un compte (inscription Discord) ou réinitialise un mot de passe via un lien à usage unique."""
    cle = f"{ip_client(request)}|jeton"
    connexion.verifier(cle)
    try:
        user = consommer_jeton(db, body.jeton, "definir_mdp")
    except HTTPException:
        connexion.echec(cle)
        raise
    user.mot_de_passe_hash = hash_password(body.mot_de_passe)
    user.doit_changer_mdp = False
    db.commit()
    return Token(access_token=create_token(user))


@router.get("/me", response_model=MeOut)
def me(user: Utilisateur = Depends(get_current_user)):
    return me_out(user)
