from sqlalchemy import (
    Column, Integer, String, SmallInteger, Date, Boolean, Text, UniqueConstraint, ForeignKey, CheckConstraint, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class Semestre(Base):
    __tablename__ = "semestre"
    id: Mapped[int] = mapped_column(primary_key=True)
    annee: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    numero: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (UniqueConstraint("annee", "numero", name="uniq_semestre_annee_numero"),)
    seances: Mapped[list["Seance"]] = relationship(back_populates="semestre", cascade="all,delete-orphan")

class Utilisateur(Base):
    __tablename__ = "utilisateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    adresse_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_utilisateur: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user' | 'moderator' | 'admin'
    classe: Mapped[str] = mapped_column(String(50), nullable=False)
    participations: Mapped[list["Participation"]] = relationship(back_populates="utilisateur", cascade="all,delete")

class Seance(Base):
    __tablename__ = "seance"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    date_seance: Mapped[Date] = mapped_column(Date, nullable=False)
    nb_point: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    semestre_id: Mapped[int] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"), nullable=False)
    __table_args__ = (CheckConstraint("nb_point >= 0", name="check_nb_point_nonneg"),)

    semestre: Mapped["Semestre"] = relationship(back_populates="seances")
    participants: Mapped[list["Participation"]] = relationship(back_populates="seance", cascade="all,delete")

class Participation(Base):
    __tablename__ = "participation"
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    seance_id: Mapped[int] = mapped_column(ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    commentaire: Mapped[str | None] = mapped_column(Text)

    utilisateur: Mapped["Utilisateur"] = relationship(back_populates="participations")
    seance: Mapped["Seance"] = relationship(back_populates="participants")
