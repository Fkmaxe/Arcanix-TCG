from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict
from datetime import date
from typing import Optional, List

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    # accepte "password" ET "mot_de_passe" grâce à l'alias
    password: str = Field(min_length=8, alias="mot_de_passe")
    model_config = {
        "populate_by_name": True,   # permet d'accepter password OU mot_de_passe
    }

# --- Utilisateur ---
class UserBase(BaseModel):
    nom: str
    prenom: str
    adresse_mail: EmailStr
    role_utilisateur: str = Field(pattern="^(user|moderator|admin)$")
    classe: str
    discord_id: int | None = None

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=512)


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    adresse_mail: Optional[EmailStr] = None
    role_utilisateur: Optional[str] = Field(default=None, pattern="^(user|moderator|admin)$")
    classe: Optional[str] = None

class UserOut(UserBase):
    id: int
    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=8)

# --- Semestre ---
class SemestreBase(BaseModel):
    annee: int
    numero: int

class SemestreCreate(SemestreBase): pass
class SemestreUpdate(BaseModel):
    annee: Optional[int] = None
    numero: Optional[int] = None

class DiscordUserCreate(BaseModel):
    discord_id: str
    nom: str
    prenom: str
    adresse_mail: EmailStr
    classe: str

class SemestreOut(BaseModel):
    id: int
    annee: int
    numero: int

class PublicPointsOut(BaseModel):
    discord_id: str
    semestre: SemestreOut
    points: float

# --- Séance ---
class SeanceBase(BaseModel):
    nom: str
    date_seance: date
    nb_point: float
    semestre_id: int

class SeanceCreate(SeanceBase): pass
class SeanceUpdate(BaseModel):
    nom: Optional[str] = None
    date_seance: Optional[date] = None
    nb_point: Optional[float] = None
    semestre_id: Optional[int] = None

class SeanceOut(SeanceBase):
    id: int
    class Config:
        from_attributes = True

# --- Participation ---
class ParticipationBase(BaseModel):
    utilisateur_id: int
    seance_id: int
    present: bool = True
    commentaire: Optional[str] = None

class ParticipationCreate(ParticipationBase): pass

class ParticipationUpdate(BaseModel):
    present: Optional[bool] = None
    commentaire: Optional[str] = None

class ParticipationOut(ParticipationBase):
    class Config:
        from_attributes = True

# --- Points / Me ---
class PointsSemestre(BaseModel):
    semestre_id: int
    annee: int
    numero: int
    points: float

class MyPointsOut(BaseModel):
    userId: int
    semestres: List[PointsSemestre]
    total: float
