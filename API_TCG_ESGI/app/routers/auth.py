from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..mail import mail_reinitialisation
from ..ratelimit import connexion, ip_client
from ..models import Utilisateur
from ..schemas import ConfigPublique, DefinirMotDePasse, LoginRequest, MeOut, MotDePasseOublie, Token
from ..journal import journaliser
from ..security import (
    consommer_jeton, create_token, get_current_user, hash_password, lien_mot_de_passe, signature_desabonnement_valide,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def me_out(user: Utilisateur) -> MeOut:
    return MeOut(
        id=user.id, nom=user.nom, prenom=user.prenom,
        email=user.adresse_mail, adresse_mail=user.adresse_mail,
        role_utilisateur=user.role_utilisateur, classe=user.classe, externe=user.externe,
        annonces_email=user.annonces_email,
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


@router.post("/mot-de-passe-oublie", status_code=202)
def mot_de_passe_oublie(body: MotDePasseOublie, request: Request, background: BackgroundTasks,
                        db: Session = Depends(get_db)):
    """Envoie un lien de réinitialisation. Réponse identique que l'email existe ou non (pas d'énumération)."""
    if not config.SMTP_ACTIF:
        raise HTTPException(503, "L'envoi d'emails n'est pas configuré : utilise /reinitialiser sur Discord "
                                 "ou demande un lien à la modération.")
    cle = f"{ip_client(request)}|oubli|{body.email}"
    connexion.verifier(cle)
    connexion.echec(cle)  # chaque demande compte : 10 max par quart d'heure
    user = db.query(Utilisateur).filter(Utilisateur.adresse_mail == body.email).first()
    if user:
        url, heures = lien_mot_de_passe(db, user)
        db.commit()
        background.add_task(mail_reinitialisation, user.adresse_mail, user.prenom, url, heures)
    return {"message": "Si un compte existe pour cet email, un lien vient d'y être envoyé."}


@router.post("/desabonner")
def desabonner(u: int, s: str, db: Session = Depends(get_db)):
    """Désinscription en un clic des emails d'annonce (lien signé reçu dans chaque email)."""
    user = db.get(Utilisateur, u)
    if not user or not signature_desabonnement_valide(u, s):
        raise HTTPException(400, "Lien de désinscription invalide")
    if user.annonces_email:
        user.annonces_email = False
        journaliser(db, user, "membre.desabonnement", f"{user.prenom} {user.nom} ne reçoit plus les annonces par email",
                    membre_id=user.id)
        db.commit()
    return {"message": "Tu ne recevras plus les annonces de séances par email."}


config_router = APIRouter(tags=["config"])


@config_router.get("/config", response_model=ConfigPublique)
def config_publique():
    """Fonctionnalités disponibles, pour adapter l'interface."""
    return ConfigPublique(smtp=config.SMTP_ACTIF, qr_periode_s=config.QR_PERIODE_S, domaine_ecole=config.EMAIL_DOMAINE_ECOLE)
