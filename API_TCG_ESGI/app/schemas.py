from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["user", "moderator", "admin"]


def _clean(v: str | None) -> str | None:
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
    # Mot de passe provisoire, ou invitation par email (le membre choisit lui-même)
    password: str | None = Field(default=None, min_length=8, max_length=512)
    envoyer_invitation: bool = False


class UserUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    adresse_mail: EmailStr | None = None
    role_utilisateur: Role | None = None
    classe: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("nom", "prenom", "classe")
    @classmethod
    def _strip(cls, v):
        return _clean(v)

    @field_validator("adresse_mail")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if v else v


class MeUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    classe: str | None = Field(default=None, min_length=1, max_length=50)

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
    discord_id: str | None = None
    doit_changer_mdp: bool = False


class PasswordChange(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=8, max_length=512)


class LienMotDePasse(BaseModel):
    url: str
    expire_dans_heures: int
    email_envoye: bool = False


class MotDePasseOublie(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class ConfigPublique(BaseModel):
    smtp: bool
    qr_periode_s: int


class CodeDiscord(BaseModel):
    code: str
    expire_dans_minutes: int


# --- Semestre ------------------------------------------------------------------
class SemestreCreate(BaseModel):
    annee: int = Field(ge=2000, le=2100)
    numero: Literal[1, 2]


class SemestreUpdate(BaseModel):
    annee: int | None = Field(default=None, ge=2000, le=2100)
    numero: Literal[1, 2] | None = None


class SemestreOut(ORM):
    id: int
    annee: int
    numero: int
    actif: bool = False


# --- Séance --------------------------------------------------------------------
class SeanceBase(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    date_seance: date
    heure_debut: time | None = None
    lieu: str | None = Field(default=None, max_length=150)
    jeu: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=4000)
    nb_point: float = Field(ge=0, le=9999)
    semestre_id: int
    places_max: int | None = Field(default=None, ge=1, le=1000)

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
    nom: str | None = Field(default=None, min_length=1, max_length=150)
    date_seance: date | None = None
    heure_debut: time | None = None
    lieu: str | None = Field(default=None, max_length=150)
    jeu: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=4000)
    nb_point: float | None = Field(default=None, ge=0, le=9999)
    semestre_id: int | None = None
    places_max: int | None = Field(default=None, ge=1, le=1000)

    @field_validator("lieu", "jeu", "description")
    @classmethod
    def _optionnels(cls, v):
        return _clean(v) or None


class SeanceOut(ORM):
    id: int
    nom: str
    date_seance: date
    heure_debut: time | None = None
    lieu: str | None = None
    jeu: str | None = None
    description: str | None = None
    nb_point: float
    semestre_id: int
    semestre: SemestreOut | None = None
    nb_participants: int = 0
    nb_presents: int = 0
    places_max: int | None = None
    nb_inscrits: int = 0
    nb_attente: int = 0
    mon_inscription: Literal["inscrit", "attente"] | None = None
    a_resultats: bool = False


class ParticipantDetail(BaseModel):
    utilisateur_id: int
    seance_id: int
    present: bool
    commentaire: str | None = None
    nom: str
    prenom: str
    classe: str
    adresse_mail: str | None = None
    discord_lie: bool = False


class MembreResume(BaseModel):
    utilisateur_id: int
    prenom: str
    nom: str
    classe: str
    discord_lie: bool = False


class InscritDetail(MembreResume):
    statut: Literal["inscrit", "attente"]
    cree_le: datetime


class PointageDetail(MembreResume):
    cree_le: datetime


class ResultatOut(BaseModel):
    utilisateur_id: int
    prenom: str
    nom: str
    place: int
    victoires: int | None = None
    defaites: int | None = None
    nuls: int | None = None
    deck: str | None = None
    bonus: float = 0
    moi: bool = False


class SeanceDetail(SeanceOut):
    participants: list[ParticipantDetail] = []
    ma_participation: bool | None = None  # présence de l'utilisateur connecté
    inscrits: list[InscritDetail] = []       # modération uniquement
    pointages: list[PointageDetail] = []     # modération uniquement
    mon_pointage: bool = False
    pointage_ouvert: bool = False
    resultats: list[ResultatOut] = []


class InscriptionOut(BaseModel):
    statut: Literal["inscrit", "attente"] | None
    seance: SeanceOut


class PointageInfo(BaseModel):
    ouvert: bool
    expire_le: datetime | None = None
    code: str | None = None
    url: str | None = None
    secondes_restantes: int = 0
    periode_s: int
    pointages: list[PointageDetail] = []


class PointageOuvrir(BaseModel):
    duree_heures: int = Field(default=4, ge=1, le=12)


class PointerBody(BaseModel):
    code: str = Field(min_length=4, max_length=20)


class PointerOut(BaseModel):
    resultat: Literal["pointe", "deja_pointe", "deja_valide"]
    seance: SeanceOut


class ResultatIn(BaseModel):
    utilisateur_id: int
    place: int = Field(ge=1, le=999)
    victoires: int | None = Field(default=None, ge=0, le=99)
    defaites: int | None = Field(default=None, ge=0, le=99)
    nuls: int | None = Field(default=None, ge=0, le=99)
    deck: str | None = Field(default=None, max_length=120)

    @field_validator("deck")
    @classmethod
    def _deck(cls, v):
        return _clean(v) or None


class ResultatsBody(BaseModel):
    resultats: list[ResultatIn] = Field(max_length=500)
    # Points bonus par place : [1re, 2e, 3e…]
    bareme: list[float] = Field(default=[3, 2, 1], max_length=32)
    annoncer: bool = True

    @field_validator("bareme")
    @classmethod
    def _bareme(cls, v: list[float]) -> list[float]:
        if any(x < 0 or x > 100 for x in v):
            raise ValueError("Le barème doit être compris entre 0 et 100 points")
        return v


# --- Ajustements (bonus / malus) -------------------------------------------------------
Categorie = Literal["organisation", "tournoi", "penalite", "autre"]


class AjustementIn(BaseModel):
    utilisateur_id: int
    points: float = Field(ge=-100, le=100)
    motif: str = Field(min_length=3, max_length=300)
    categorie: Categorie = "autre"
    semestre_id: int | None = None  # semestre actif par défaut

    @field_validator("points")
    @classmethod
    def _non_nul(cls, v: float) -> float:
        if v == 0:
            raise ValueError("Les points doivent être différents de 0")
        return round(v, 2)

    @field_validator("motif")
    @classmethod
    def _motif(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Motif trop court")
        return v


class AjustementOut(BaseModel):
    id: int
    utilisateur_id: int
    prenom: str
    nom: str
    semestre: SemestreOut
    seance_id: int | None = None
    points: float
    categorie: str
    motif: str
    cree_par: str | None = None
    cree_le: datetime


class MonAjustement(BaseModel):
    id: int
    points: float
    categorie: str
    motif: str
    semestre_id: int
    seance_id: int | None = None
    cree_le: datetime


# --- Journal ------------------------------------------------------------------------------
class JournalOut(ORM):
    id: int
    cree_le: datetime
    auteur_id: int | None = None
    auteur_nom: str
    action: str
    resume: str
    membre_id: int | None = None
    seance_id: int | None = None
    details: dict | None = None


# --- Participation -------------------------------------------------------------
class ParticipationBase(BaseModel):
    utilisateur_id: int
    seance_id: int
    present: bool = True
    commentaire: str | None = Field(default=None, max_length=1000)


class ParticipationCreate(ParticipationBase):
    pass


class ParticipationUpdate(BaseModel):
    present: bool | None = None
    commentaire: str | None = Field(default=None, max_length=1000)


class ParticipationOut(ORM):
    utilisateur_id: int
    seance_id: int
    present: bool
    commentaire: str | None = None


class AppelItem(BaseModel):
    utilisateur_id: int
    present: bool = True
    commentaire: str | None = Field(default=None, max_length=1000)


class AppelBody(BaseModel):
    participants: list[AppelItem]
    # True : les participants absents de la liste sont retirés de la séance
    remplacer: bool = True


class MaParticipation(BaseModel):
    seance_id: int
    seance_nom: str
    date_seance: date
    jeu: str | None = None
    nb_point: float
    present: bool
    commentaire: str | None = None
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
    seance: str  # libellé : séance ou motif du bonus
    points: float
    cumul: float
    type: Literal["presence", "ajustement"] = "presence"


class MesStats(BaseModel):
    semestre: SemestreOut | None
    points: float
    rang: int | None
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
    bonus: float = 0
    moi: bool = False


class Classement(BaseModel):
    semestre: SemestreOut | None
    lignes: list[LigneClassement]


# --- Discord -------------------------------------------------------------------
class DiscordRegister(BaseModel):
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
    semestre_id: int | None = None  # semestre actif par défaut


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
    semestre: SemestreOut | None
    points: float
    rang: int | None
    presences: int
    total_points: float


TypeAnnonce = Literal["nouvelle_seance", "rappel", "podium", "resultats"]


class Annonce(BaseModel):
    type: TypeAnnonce
    id: int
    seance: SeanceOut | None = None
    semestre: SemestreOut | None = None
    podium: list[LigneClassement] = []
    resultats: list[ResultatOut] = []


class AnnonceAck(BaseModel):
    type: TypeAnnonce
    id: int


class DiscordInscription(BaseModel):
    discord_id: str
    action: Literal["in", "out"]


class DiscordInscriptionOut(BaseModel):
    statut: Literal["inscrit", "attente"] | None
    seance: SeanceOut
    promus: list[str] = []  # discord_id des membres sortis de la liste d'attente


class DiscordAjustement(BaseModel):
    auteur_discord_id: str
    discord_id: str
    points: float = Field(ge=-100, le=100)
    motif: str = Field(min_length=3, max_length=300)
    categorie: Categorie = "autre"


class DiscordRoles(BaseModel):
    membres: list[str]
    top3: list[str]
