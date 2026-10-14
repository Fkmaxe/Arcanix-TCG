from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..journal import journaliser, nom_complet
from ..mail import mail_invitation, mail_reinitialisation
from ..models import Utilisateur
from ..schemas import LienMotDePasse, PasswordChange, UserCreate, UserOut, UserUpdate, regle_interne_externe
from ..security import (
    get_current_user, get_current_user_optional, hash_password, lien_mot_de_passe, require_roles,
    unusable_password_hash, verify_password,
)

router = APIRouter(prefix="/users", tags=["users"])


def _email_pris(db: Session, email: str, sauf_id: int | None = None) -> bool:
    q = db.query(Utilisateur).filter(func.lower(Utilisateur.adresse_mail) == email.lower())
    if sauf_id:
        q = q.filter(Utilisateur.id != sauf_id)
    return db.query(q.exists()).scalar()


def _nb_admins(db: Session) -> int:
    return db.query(func.count(Utilisateur.id)).filter(Utilisateur.role_utilisateur == "admin").scalar() or 0


@router.get("", response_model=list[UserOut])
def list_users(
    response: Response,
    q: str | None = None,
    role: str | None = None,
    classe: str | None = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "moderator")),
):
    page, limit = max(page, 1), min(max(limit, 1), 200)
    query = db.query(Utilisateur)
    if q:
        for mot in q.split():
            like = f"%{mot}%"
            query = query.filter(or_(Utilisateur.nom.ilike(like), Utilisateur.prenom.ilike(like),
                                     Utilisateur.adresse_mail.ilike(like), Utilisateur.classe.ilike(like)))
    if role:
        query = query.filter(Utilisateur.role_utilisateur == role)
    if classe:
        query = query.filter(Utilisateur.classe == classe)
    response.headers["X-Total-Count"] = str(query.count())
    return (query.order_by(Utilisateur.prenom, Utilisateur.nom, Utilisateur.id)
            .offset((page - 1) * limit).limit(limit).all())


@router.get("/classes", response_model=list[str])
def list_classes(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [c for (c,) in db.query(Utilisateur.classe).distinct().order_by(Utilisateur.classe)]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current: Utilisateur = Depends(get_current_user)):
    if current.role_utilisateur not in ("admin", "moderator") and current.id != user_id:
        raise HTTPException(403, "Accès refusé")
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    return user


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, background: BackgroundTasks, db: Session = Depends(get_db),
                current: Utilisateur | None = Depends(get_current_user_optional)):
    """Inscription publique (rôle forcé à « user ») ou création par la modération."""
    if current and current.role_utilisateur not in ("admin", "moderator"):
        raise HTTPException(403, "Accès refusé")
    if _email_pris(db, body.adresse_mail):
        raise HTTPException(409, "Email déjà utilisé")

    role = body.role_utilisateur if current else "user"
    if current and current.role_utilisateur == "moderator" and role != "user":
        raise HTTPException(403, "Seul un admin peut attribuer ce rôle")

    invitation = bool(current) and body.envoyer_invitation
    if invitation and not config.SMTP_ACTIF:
        raise HTTPException(409, "L'envoi d'emails n'est pas configuré : indique un mot de passe provisoire")
    if not invitation and not body.password:
        raise HTTPException(422, "Mot de passe requis (8 caractères minimum)")

    user = Utilisateur(
        nom=body.nom, prenom=body.prenom, adresse_mail=body.adresse_mail, classe=body.classe,
        externe=body.externe, role_utilisateur=role,
        mot_de_passe_hash=unusable_password_hash() if invitation else hash_password(body.password),
        # Un compte créé par la modération doit choisir son propre mot de passe
        doit_changer_mdp=bool(current),
    )
    db.add(user)
    db.flush()
    if current:
        journaliser(db, current, "membre.creation", f"Compte de {user.prenom} {user.nom} créé ({role})", membre_id=user.id)
    if invitation:
        url, heures = lien_mot_de_passe(db, user)
        background.add_task(mail_invitation, user.adresse_mail, user.prenom, url, heures, nom_complet(current))
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                current: Utilisateur = Depends(require_roles("admin", "moderator"))):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    data = body.model_dump(exclude_unset=True, exclude_none=True)

    if current.role_utilisateur == "moderator":
        if user.role_utilisateur != "user" and user.id != current.id:
            raise HTTPException(403, "Un modérateur ne peut modifier que des membres")
        if "role_utilisateur" in data and data["role_utilisateur"] != user.role_utilisateur:
            raise HTTPException(403, "Seul un admin peut changer les rôles")

    nouveau_role = data.get("role_utilisateur")
    if user.role_utilisateur == "admin" and nouveau_role and nouveau_role != "admin" and _nb_admins(db) <= 1:
        raise HTTPException(409, "Impossible de rétrograder le dernier admin")

    if "adresse_mail" in data and _email_pris(db, data["adresse_mail"], user_id):
        raise HTTPException(409, "Email déjà utilisé")
    if {"externe", "adresse_mail", "classe"} & data.keys():
        try:
            data["classe"] = regle_interne_externe(data.get("adresse_mail", user.adresse_mail),
                                                   data.get("classe", user.classe), data.get("externe", user.externe))
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
    changements = {k: [getattr(user, k), v] for k, v in data.items() if getattr(user, k) != v}
    for k, v in data.items():
        setattr(user, k, v)
    if "role_utilisateur" in changements:
        avant, apres = changements["role_utilisateur"]
        journaliser(db, current, "membre.role", f"Rôle de {user.prenom} {user.nom} : {avant} → {apres}",
                    membre_id=user.id, details={"avant": avant, "apres": apres})
    elif changements:
        journaliser(db, current, "membre.modification", f"Profil de {user.prenom} {user.nom} modifié ({', '.join(changements)})",
                    membre_id=user.id, details={k: {"avant": a, "apres": b} for k, (a, b) in changements.items()})
    db.commit()
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db),
                current: Utilisateur = Depends(require_roles("admin"))):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    if user.id == current.id:
        raise HTTPException(409, "Vous ne pouvez pas supprimer votre propre compte")
    journaliser(db, current, "membre.suppression", f"Compte de {user.prenom} {user.nom} ({user.adresse_mail}) supprimé",
                details={"utilisateur_id": user.id})
    db.delete(user)
    db.commit()


@router.patch("/{user_id}/password", status_code=204)
def change_password(user_id: int, body: PasswordChange, db: Session = Depends(get_db),
                    current: Utilisateur = Depends(get_current_user)):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    staff = current.role_utilisateur in ("admin", "moderator")
    if current.id == user_id and not user.doit_changer_mdp:
        if not body.current_password or not verify_password(body.current_password, user.mot_de_passe_hash):
            raise HTTPException(400, "Mot de passe actuel incorrect")
    elif current.id != user_id:
        if not staff:
            raise HTTPException(403, "Accès refusé")
        if current.role_utilisateur == "moderator" and user.role_utilisateur != "user":
            raise HTTPException(403, "Un modérateur ne peut modifier que des membres")

    user.mot_de_passe_hash = hash_password(body.new_password)
    # Mot de passe fixé par quelqu'un d'autre : le membre devra le changer
    user.doit_changer_mdp = current.id != user_id
    if current.id != user_id:
        journaliser(db, current, "membre.mdp", f"Mot de passe provisoire défini pour {user.prenom} {user.nom}",
                    membre_id=user.id)
    db.commit()


@router.post("/{user_id}/lien-mot-de-passe", response_model=LienMotDePasse)
def generer_lien_mdp(user_id: int, background: BackgroundTasks, envoyer: bool = False, db: Session = Depends(get_db),
                     current: Utilisateur = Depends(require_roles("admin", "moderator"))):
    """Lien de réinitialisation à transmettre au membre (pas d'email sortant)."""
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    if current.role_utilisateur == "moderator" and user.role_utilisateur != "user":
        raise HTTPException(403, "Un modérateur ne peut modifier que des membres")
    if envoyer and not config.SMTP_ACTIF:
        raise HTTPException(409, "L'envoi d'emails n'est pas configuré")
    url, heures = lien_mot_de_passe(db, user)
    journaliser(db, current, "membre.lien_mdp", f"Lien de mot de passe généré pour {user.prenom} {user.nom}"
                + (" (envoyé par email)" if envoyer else ""), membre_id=user.id)
    db.commit()
    if envoyer:
        background.add_task(mail_reinitialisation, user.adresse_mail, user.prenom, url, heures)
    return LienMotDePasse(url=url, expire_dans_heures=heures, email_envoye=envoyer)
