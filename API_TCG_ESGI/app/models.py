from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger,
    String, Text, Time, UniqueConstraint, func,
)
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
    classe: Mapped[str] = mapped_column(String(50), nullable=False)
    doit_changer_mdp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

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
    __table_args__ = (CheckConstraint("nb_point >= 0", name="seance_nb_point_check"),)

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
