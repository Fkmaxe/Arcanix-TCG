from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/discord", tags=["discord"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_bot_token(x_bot_token: str = Header(...)):
    expected_token = os.getenv("DISCORD_BOT_TOKEN")
    if x_bot_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid bot token")

# 🔒 Création d’un compte utilisateur via Discord
@router.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user_discord(
    user_data: schemas.DiscordUserCreate,
    db: Session = Depends(get_db),
    _=Depends(verify_bot_token)
):
    existing = db.query(models.Utilisateur).filter(
        (models.Utilisateur.discord_id == user_data.discord_id) |
        (models.Utilisateur.adresse_mail == user_data.adresse_mail)
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = models.Utilisateur(
        discord_id=user_data.discord_id,
        nom=user_data.nom,
        prenom=user_data.prenom,
        adresse_mail=user_data.adresse_mail,
        mot_de_passe_hash=get_password_hash("default1234"),
        role_utilisateur="user",
        classe=user_data.classe
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 🔓 Récupérer les points d’un utilisateur par ID Discord
@router.get("/points/discord/{discord_id}", response_model=schemas.PublicPointsOut)
def get_points_discord(discord_id: str, db: Session = Depends(get_db)):
    user = db.query(models.Utilisateur).filter_by(discord_id=discord_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    semestre = db.query(models.Semestre).order_by(models.Semestre.annee.desc(), models.Semestre.numero.desc()).first()
    if not semestre:
        raise HTTPException(status_code=404, detail="No semestre defined")

    # Points = somme des points des séances du semestre où l’utilisateur est présent
    total_points = (
        db.query(models.Seance.nb_point)
        .join(models.Participation, models.Seance.id == models.Participation.seance_id)
        .filter(
            models.Participation.utilisateur_id == user.id,
            models.Participation.present == True,
            models.Seance.semestre_id == semestre.id
        )
        .all()
    )
    points_sum = sum([p[0] for p in total_points])

    return {
        "discord_id": discord_id,
        "semestre": {
            "id": semestre.id,
            "annee": semestre.annee,
            "numero": semestre.numero
        },
        "points": points_sum
    }