from datetime import date, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["user", "moderator", "admin"]


def _clean(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else v


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth --------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    # accepte "password" ET "mot_de_passe"
    model_config = ConfigDict(populate_by_name=True)
    email: EmailStr
    password: str = Field(min_length=1, max_length=512, alias="mot_de_passe")

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class DefinirMotDePasse(BaseModel):
    jeton: str = Field(min_length=10, max_length=200)
    mot_de_passe: str = Field(min_length=8, max_length=512)


class MeOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    adresse_mail: str
    role_utilisateur: Role
    classe: str
    doit_changer_mdp: bool
    discord_lie: bool


# --- Utilisateur ---------------------------------------------------------------
class UserBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    adresse_mail: EmailStr
    role_utilisateur: Role = "user"
    classe: str = Field(min_length=1, max_length=50)

    @field_validator("nom", "prenom", "classe")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("adresse_mail")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=512)


class UserUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    adresse_mail: Optional[EmailStr] = None
    role_utilisateur: Optional[Role] = None
    classe: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @field_validator("nom", "prenom", "classe")
    @classmethod
    def _strip(cls, v):
        return _clean(v)

    @field_validator("adresse_mail")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if v else v


class MeUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    classe: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @field_validator("nom", "prenom", "classe")
    @classmethod
    def _strip(cls, v):
        return _clean(v)


class UserOut(ORM):
    id: int
    nom: str
    prenom: str
    adresse_mail: str
    role_utilisateur: str
    classe: str
    discord_id: Optional[str] = None
    doit_changer_mdp: bool = False


class PasswordChange(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8, max_length=512)


class LienMotDePasse(BaseModel):
    url: str
    expire_dans_heures: int


class CodeDiscord(BaseModel):
    code: str
    expire_dans_minutes: int


# --- Semestre ------------------------------------------------------------------
class SemestreCreate(BaseModel):
    annee: int = Field(ge=2000, le=2100)
    numero: Literal[1, 2]


class SemestreUpdate(BaseModel):
    annee: Optional[int] = Field(default=None, ge=2000, le=2100)
    numero: Optional[Literal[1, 2]] = None


class SemestreOut(ORM):
    id: int
    annee: int
    numero: int
    actif: bool = False


# --- Séance --------------------------------------------------------------------
class SeanceBase(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    date_seance: date
    heure_debut: Optional[time] = None
    lieu: Optional[str] = Field(default=None, max_length=150)
    jeu: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=4000)
    nb_point: float = Field(ge=0, le=9999)
    semestre_id: int

    @field_validator("nom")
    @classmethod
    def _nom(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom est requis")
        return v

    @field_validator("lieu", "jeu", "description")
    @classmethod
    def _optionnels(cls, v):
        return _clean(v) or None


class SeanceCreate(SeanceBase):
    pass


class SeanceUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=150)
    date_seance: Optional[date] = None
    heure_debut: Optional[time] = None
    lieu: Optional[str] = Field(default=None, max_length=150)
    jeu: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=4000)
    nb_point: Optional[float] = Field(default=None, ge=0, le=9999)
    semestre_id: Optional[int] = None

    @field_validator("lieu", "jeu", "description")
    @classmethod
    def _optionnels(cls, v):
        return _clean(v) or None


class SeanceOut(ORM):
    id: int
    nom: str
    date_seance: date
    heure_debut: Optional[time] = None
    lieu: Optional[str] = None
    jeu: Optional[str] = None
    description: Optional[str] = None
    nb_point: float
    semestre_id: int
    semestre: Optional[SemestreOut] = None
    nb_participants: int = 0
    nb_presents: int = 0


class ParticipantDetail(BaseModel):
    utilisateur_id: int
    seance_id: int
    present: bool
    commentaire: Optional[str] = None
    nom: str
    prenom: str
    classe: str
    adresse_mail: Optional[str] = None
    discord_lie: bool = False


class SeanceDetail(SeanceOut):
    participants: list[ParticipantDetail] = []
    ma_participation: Optional[bool] = None  # présence de l'utilisateur connecté


# --- Participation -------------------------------------------------------------
class ParticipationBase(BaseModel):
    utilisateur_id: int
    seance_id: int
    present: bool = True
    commentaire: Optional[str] = Field(default=None, max_length=1000)


class ParticipationCreate(ParticipationBase):
    pass


class ParticipationUpdate(BaseModel):
    present: Optional[bool] = None
    commentaire: Optional[str] = Field(default=None, max_length=1000)


class ParticipationOut(ORM):
    utilisateur_id: int
    seance_id: int
    present: bool
    commentaire: Optional[str] = None


class AppelItem(BaseModel):
    utilisateur_id: int
    present: bool = True
    commentaire: Optional[str] = Field(default=None, max_length=1000)


class AppelBody(BaseModel):
    participants: list[AppelItem]
    # True : les participants absents de la liste sont retirés de la séance
    remplacer: bool = True


class MaParticipation(BaseModel):
    seance_id: int
    seance_nom: str
    date_seance: date
    jeu: Optional[str] = None
    nb_point: float
    present: bool
    commentaire: Optional[str] = None
    semestre_id: int


# --- Points / stats ------------------------------------------------------------
class PointsSemestre(BaseModel):
    semestre_id: int
    annee: int
    numero: int
    points: float


class MyPointsOut(BaseModel):
    userId: int
    semestres: list[PointsSemestre]
    total: float


class PointEvolution(BaseModel):
    date: date
    seance: str
    points: float
    cumul: float


class MesStats(BaseModel):
    semestre: Optional[SemestreOut]
    points: float
    rang: Optional[int]
    nb_membres_classes: int
    seances_semestre: int
    presences: int
    taux_presence: float
    evolution: list[PointEvolution]


class LigneClassement(BaseModel):
    rang: int
    userId: int
    prenom: str
    nom: str  # initiale seulement pour les membres, complet pour la modération
    classe: str
    points: float
    presences: int
    moi: bool = False


class Classement(BaseModel):
    semestre: Optional[SemestreOut]
    lignes: list[LigneClassement]


# --- Discord -------------------------------------------------------------------
class DiscordInscription(BaseModel):
    discord_id: str = Field(min_length=1, max_length=255)
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    adresse_mail: EmailStr
    classe: str = Field(min_length=1, max_length=50)

    @field_validator("nom", "prenom", "classe")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("adresse_mail")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class DiscordLier(BaseModel):
    discord_id: str
    code: str = Field(min_length=4, max_length=20)


class DiscordIdBody(BaseModel):
    discord_id: str


class DiscordSeanceCreate(SeanceBase):
    auteur_discord_id: str
    semestre_id: Optional[int] = None  # semestre actif par défaut


class DiscordPresences(BaseModel):
    auteur_discord_id: str
    discord_ids: list[str] = Field(min_length=1, max_length=50)


class DiscordPresencesOut(BaseModel):
    seance: SeanceOut
    ajoutes: list[str]
    deja_presents: list[str]
    non_lies: list[str]


class DiscordMembre(BaseModel):
    prenom: str
    nom: str
    classe: str
    role_utilisateur: str
    semestre: Optional[SemestreOut]
    points: float
    rang: Optional[int]
    presences: int
    total_points: float


class Annonce(BaseModel):
    type: Literal["nouvelle_seance", "rappel", "podium"]
    id: int
    seance: Optional[SeanceOut] = None
    semestre: Optional[SemestreOut] = None
    podium: list[LigneClassement] = []


class AnnonceAck(BaseModel):
    type: Literal["nouvelle_seance", "rappel", "podium"]
    id: int
