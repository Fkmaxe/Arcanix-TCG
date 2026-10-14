"""Membres internes/externes, préférence d'emails, publication programmée des séances

Revision ID: 0004
Revises: 0003
"""
import os

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- utilisateur : interne (élève, classe obligatoire) ou externe (sans classe) ----------
    op.add_column("utilisateur", sa.Column("externe", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("utilisateur", sa.Column("annonces_email", sa.Boolean(), nullable=False, server_default="true"))
    op.alter_column("utilisateur", "classe", nullable=True)
    # Comptes existants hors domaine de l'école : externes (leur classe éventuelle est conservée)
    domaine = os.getenv("EMAIL_DOMAINE_ECOLE", "myskolae.fr").strip().lower().lstrip("@")
    op.get_bind().execute(
        sa.text("UPDATE utilisateur SET externe = true WHERE lower(adresse_mail) NOT LIKE :motif"),
        {"motif": f"%@{domaine}"},
    )
    op.create_check_constraint("utilisateur_classe_interne_check", "utilisateur", "externe OR classe IS NOT NULL")

    # --- seance : quand l'annoncer sur Discord et par email (NULL = ne pas publier) ----------
    op.add_column("seance", sa.Column("discord_publier_le", sa.DateTime(timezone=True)))
    op.add_column("seance", sa.Column("email_publier_le", sa.DateTime(timezone=True)))
    op.add_column("seance", sa.Column("email_envoye", sa.Boolean(), nullable=False, server_default="false"))
    # Séances existantes : déjà annoncées sur Discord, et aucun email ne doit partir au déploiement
    op.execute("UPDATE seance SET discord_publier_le = now(), email_envoye = true")


def downgrade() -> None:
    for col in ("email_envoye", "email_publier_le", "discord_publier_le"):
        op.drop_column("seance", col)
    op.drop_constraint("utilisateur_classe_interne_check", "utilisateur")
    op.execute("UPDATE utilisateur SET classe = 'Externe' WHERE classe IS NULL")
    op.alter_column("utilisateur", "classe", nullable=False)
    op.drop_column("utilisateur", "annonces_email")
    op.drop_column("utilisateur", "externe")
