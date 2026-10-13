"""Inscriptions, pointage QR, ajustements de points, résultats de tournoi, journal

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seance", sa.Column("places_max", sa.Integer()))
    op.add_column("seance", sa.Column("pointage_secret", sa.String(64)))
    op.add_column("seance", sa.Column("pointage_expire_le", sa.DateTime(timezone=True)))
    op.add_column("seance", sa.Column("resultats_a_annoncer", sa.Boolean(), nullable=False, server_default="false"))
    op.create_check_constraint("seance_places_max_check", "seance", "places_max IS NULL OR places_max > 0")

    op.create_table(
        "inscription",
        sa.Column("utilisateur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("statut", sa.String(10), nullable=False, server_default="inscrit"),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_inscription_seance", "inscription", ["seance_id", "statut", "cree_le"])

    op.create_table(
        "pointage",
        sa.Column("utilisateur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ajustement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("utilisateur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semestre_id", sa.Integer(), sa.ForeignKey("semestre.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seance.id", ondelete="CASCADE")),
        sa.Column("points", sa.Numeric(6, 2), nullable=False),
        sa.Column("categorie", sa.String(20), nullable=False, server_default="autre"),
        sa.Column("motif", sa.String(300), nullable=False),
        sa.Column("cree_par_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="SET NULL")),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("points <> 0", name="ajustement_points_check"),
    )
    op.create_index("idx_ajustement_semestre_user", "ajustement", ["semestre_id", "utilisateur_id"])

    op.create_table(
        "resultat",
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seance.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("utilisateur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("place", sa.Integer(), nullable=False),
        sa.Column("victoires", sa.Integer()),
        sa.Column("defaites", sa.Integer()),
        sa.Column("nuls", sa.Integer()),
        sa.Column("deck", sa.String(120)),
        sa.CheckConstraint("place > 0", name="resultat_place_check"),
    )

    op.create_table(
        "journal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("auteur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="SET NULL")),
        sa.Column("auteur_nom", sa.String(210), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("resume", sa.String(500), nullable=False),
        sa.Column("membre_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="SET NULL")),
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seance.id", ondelete="SET NULL")),
        sa.Column("details", JSONB()),
    )
    op.create_index("ix_journal_cree_le", "journal", ["cree_le"])
    op.create_index("ix_journal_membre_id", "journal", ["membre_id"])
    op.create_index("ix_journal_seance_id", "journal", ["seance_id"])


def downgrade() -> None:
    for t in ("journal", "resultat", "ajustement", "pointage", "inscription"):
        op.drop_table(t)
    op.drop_constraint("seance_places_max_check", "seance")
    for c in ("resultats_a_annoncer", "pointage_expire_le", "pointage_secret", "places_max"):
        op.drop_column("seance", c)
