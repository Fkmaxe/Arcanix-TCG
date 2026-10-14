from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger,
    String, Text, Time, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

ROLES = ("user", "moderator", "admin")
JEUX = ("pokemon", "magic", "yugioh", "lorcana", "onepiece", "fab", "autre")


class Semestre(Base):
    __tablename__ = "semestre"
    id: Mapped[int] = mapped_column(primary_key=True)
    annee: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    numero: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    podium_annonce: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    __table_args__ = (UniqueConstraint("annee", "numero"),)

    # Pas de cascade : la FK seance -> semestre est en ON DELETE RESTRICT
    seances: Mapped[list["Seance"]] = relationship(back_populates="semestre", passive_deletes="all")


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    adresse_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_utilisateur: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user' | 'moderator' | 'admin'
    classe: Mapped[str | None] = mapped_column(String(50))  # obligatoire pour un interne (CHECK)
    externe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    annonces_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    doit_changer_mdp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("externe OR classe IS NOT NULL", name="utilisateur_classe_interne_check"),)

    participations: Mapped[list["Participation"]] = relationship(back_populates="utilisateur", passive_deletes=True)


class Seance(Base):
    __tablename__ = "seance"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    date_seance: Mapped[date] = mapped_column(Date, nullable=False)
    heure_debut: Mapped[time | None] = mapped_column(Time)
    lieu: Mapped[str | None] = mapped_column(String(150))
    jeu: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    nb_point: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    semestre_id: Mapped[int] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"), nullable=False)
    annonce_envoyee: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    rappel_envoye: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Inscriptions : None = places illimitées
    places_max: Mapped[int | None] = mapped_column(Integer)
    # Pointage par QR code : secret de la séance et fin de validité
    pointage_secret: Mapped[str | None] = mapped_column(String(64))
    pointage_expire_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Résultats de tournoi publiés mais pas encore annoncés sur Discord
    resultats_a_annoncer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Publication programmée (NULL = ne pas publier sur ce canal)
    discord_publier_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_publier_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_envoye: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    __table_args__ = (
        CheckConstraint("nb_point >= 0", name="seance_nb_point_check"),
        CheckConstraint("places_max IS NULL OR places_max > 0", name="seance_places_max_check"),
    )

    semestre: Mapped["Semestre"] = relationship(back_populates="seances")
    participants: Mapped[list["Participation"]] = relationship(back_populates="seance", passive_deletes=True)


class Participation(Base):
    __tablename__ = "participation"
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    seance_id: Mapped[int] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    commentaire: Mapped[str | None] = mapped_column(Text)

    utilisateur: Mapped["Utilisateur"] = relationship(back_populates="participations")
    seance: Mapped["Seance"] = relationship(back_populates="participants")


class Jeton(Base):
    """Jeton à usage unique : définition de mot de passe ou liaison Discord."""
    __tablename__ = "jeton"
    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'definir_mdp' | 'lier_discord'
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    utilise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    utilisateur: Mapped["Utilisateur"] = relationship()


class Inscription(Base):
    """« Je viens » : inscription à une séance (avec liste d'attente si complet)."""
    __tablename__ = "inscription"
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    seance_id: Mapped[int] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True)
    statut: Mapped[str] = mapped_column(String(10), nullable=False, default="inscrit")  # 'inscrit' | 'attente'
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    utilisateur: Mapped["Utilisateur"] = relationship()


class Pointage(Base):
    """Présence déclarée par le membre via QR code, en attente de validation par la modération."""
    __tablename__ = "pointage"
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    seance_id: Mapped[int] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Ajustement(Base):
    """Points bonus (>0) ou malus (<0) hors présence, toujours motivés."""
    __tablename__ = "ajustement"
    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False)
    semestre_id: Mapped[int] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"), nullable=False)
    # Renseigné pour les bonus générés par les résultats d'un tournoi
    seance_id: Mapped[int | None] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"))
    points: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    categorie: Mapped[str] = mapped_column(String(20), nullable=False, default="autre")
    motif: Mapped[str] = mapped_column(String(300), nullable=False)
    cree_par_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (CheckConstraint("points <> 0", name="ajustement_points_check"),)

    utilisateur: Mapped["Utilisateur"] = relationship(foreign_keys=[utilisateur_id])
    cree_par: Mapped["Utilisateur | None"] = relationship(foreign_keys=[cree_par_id])
    semestre: Mapped["Semestre"] = relationship()


class Resultat(Base):
    """Classement final d'un membre à un tournoi."""
    __tablename__ = "resultat"
    seance_id: Mapped[int] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    place: Mapped[int] = mapped_column(Integer, nullable=False)
    victoires: Mapped[int | None] = mapped_column(Integer)
    defaites: Mapped[int | None] = mapped_column(Integer)
    nuls: Mapped[int | None] = mapped_column(Integer)
    deck: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (CheckConstraint("place > 0", name="resultat_place_check"),)

    utilisateur: Mapped["Utilisateur"] = relationship()


class Journal(Base):
    """Historique des actions sensibles (présences, points, rôles…)."""
    __tablename__ = "journal"
    id: Mapped[int] = mapped_column(primary_key=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    auteur_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    auteur_nom: Mapped[str] = mapped_column(String(210), nullable=False)  # copie : reste lisible si l'auteur est supprimé
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    resume: Mapped[str] = mapped_column(String(500), nullable=False)
    membre_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"), index=True)
    seance_id: Mapped[int | None] = mapped_column(ForeignKey("seance.id", ondelete="SET NULL"), index=True)
    details: Mapped[dict | None] = mapped_column(JSONB)
