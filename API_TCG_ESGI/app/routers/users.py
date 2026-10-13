from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import Utilisateur
from ..schemas import UserCreate, UserOut, UserUpdate, PasswordChange
from ..security import require_roles, get_current_user, hash_password, get_current_user_optional

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    q: str | None = None,
    role: str | None = None,
    classe: str | None = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: any = Depends(require_roles("admin", "moderator")),
):
    query = db.query(Utilisateur)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Utilisateur.nom.ilike(like),
                                 Utilisateur.prenom.ilike(like),
                                 Utilisateur.adresse_mail.ilike(like)))
    if role:
        query = query.filter(Utilisateur.role_utilisateur == role)
    if classe:
        query = query.filter(Utilisateur.classe == classe)
    return query.offset((page-1)*limit).limit(limit).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    if current.role_utilisateur in ("admin", "moderator") or current.id == user_id:
        user = db.get(Utilisateur, user_id)
        if not user:
            raise HTTPException(404, "Utilisateur introuvable")
        return user
    raise HTTPException(403, "Accès refusé")


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current = Depends(get_current_user_optional),
):
    if db.query(Utilisateur).filter_by(adresse_mail=body.adresse_mail).first():
        raise HTTPException(409, "Email déjà utilisé")

    # Non connecté -> rôle imposé à 'user'
    role = "user" if not current else body.role_utilisateur

    if current and current.role_utilisateur not in ("admin", "moderator"):
        raise HTTPException(403, "Accès refusé.")

    # ⚠️ discord_id est NOT NULL et UNIQUE : on génère un ID unique si non fourni
    # Format: "web_<email>" pour éviter les conflits avec les vrais Discord IDs
    discord_id = body.discord_id if body.discord_id else f"web_{body.adresse_mail}"

    user = Utilisateur(
        nom=body.nom,
        prenom=body.prenom,
        adresse_mail=body.adresse_mail,
        role_utilisateur=role,
        classe=body.classe,
        mot_de_passe_hash=hash_password(body.password),  # <-- champ correct
        discord_id=discord_id,                        # <-- fourni pour respecter NOT NULL + UNIQUE
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current = Depends(require_roles("admin", "moderator")),
):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    # Le modérateur ne peut pas modifier un admin (promotion/déclassement)
    if current.role_utilisateur == "moderator" and user.role_utilisateur == "admin":
        raise HTTPException(403, "Interdit sur admin")
    data = body.model_dump(exclude_unset=True)
    if "adresse_mail" in data:
        taken = db.query(Utilisateur).filter(
            Utilisateur.adresse_mail == data["adresse_mail"],
            Utilisateur.id != user_id
        ).first()
        if taken:
            raise HTTPException(409, "Email déjà utilisé")
    for k,v in data.items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: any = Depends(require_roles("admin")),
):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    db.delete(user); db.commit()

@router.patch("/{user_id}/password", status_code=204)
def change_password(
    user_id: int,
    body: PasswordChange,
    db: Session = Depends(get_db),
    current: Utilisateur = Depends(get_current_user),
):
    user = db.get(Utilisateur, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    # Règles d'autorisation :
    # - un admin peut changer n'importe quel MDP sans current_password
    # - un moderator ne change pas celui d'un admin
    # - un user ne change QUE son propre MDP et DOIT fournir current_password correct
    if current.role_utilisateur == "moderator" and user.role_utilisateur == "admin":
        raise HTTPException(403, "Interdit sur admin")
    if current.role_utilisateur not in ("admin", "moderator"):
        if current.id != user_id:
            raise HTTPException(403, "Accès refusé")
        # vérification current_password pour un user qui change son MDP
        if not body.current_password:
            raise HTTPException(400, "Mot de passe actuel requis")
        from ..security import verify_password
        if not verify_password(body.current_password, user.mot_de_passe_hash):
            raise HTTPException(401, "Mot de passe actuel invalide")

    # Appliquer le nouveau hash
    user.mot_de_passe_hash = hash_password(body.new_password)
    db.commit()
    return