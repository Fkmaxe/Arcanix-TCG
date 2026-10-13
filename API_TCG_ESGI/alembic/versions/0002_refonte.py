"""Refonte : points décimaux, séances enrichies, semestre actif, jetons, emails normalisés

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- utilisateur ---------------------------------------------------------
    doublons = conn.execute(sa.text(
        "SELECT lower(adresse_mail) AS m, count(*) FROM utilisateur GROUP BY 1 HAVING count(*) > 1"
    )).fetchall()
    if doublons:
        liste = ", ".join(r.m for r in doublons)
        raise RuntimeError(
            f"Emails en double (casse différente) à fusionner manuellement avant migration : {liste}"
        )

    op.execute("ALTER TABLE utilisateur ALTER COLUMN discord_id DROP NOT NULL")
    # Les comptes créés depuis le site avaient un faux discord_id « web_<email> »
    op.execute("UPDATE utilisateur SET discord_id = NULL WHERE discord_id LIKE 'web\\_%'")
    op.execute("UPDATE utilisateur SET adresse_mail = lower(trim(adresse_mail))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uniq_utilisateur_mail_lower ON utilisateur (lower(adresse_mail))")
    op.add_column("utilisateur", sa.Column("doit_changer_mdp", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("utilisateur", sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()))

    # --- seance --------------------------------------------------------------
    op.execute("ALTER TABLE seance ALTER COLUMN nb_point TYPE NUMERIC(6,2) USING nb_point::numeric")
    op.add_column("seance", sa.Column("heure_debut", sa.Time()))
    op.add_column("seance", sa.Column("lieu", sa.String(150)))
    op.add_column("seance", sa.Column("jeu", sa.String(50)))
    op.add_column("seance", sa.Column("description", sa.Text()))
    op.add_column("seance", sa.Column("annonce_envoyee", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("seance", sa.Column("rappel_envoye", sa.Boolean(), nullable=False, server_default="false"))
    # Les séances existantes ne doivent pas être (ré)annoncées au déploiement
    op.execute("UPDATE seance SET annonce_envoyee = true, rappel_envoye = true")

    # --- semestre ------------------------------------------------------------
    op.add_column("semestre", sa.Column("actif", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("semestre", sa.Column("podium_annonce", sa.Boolean(), nullable=False, server_default="true"))
    op.execute("CREATE UNIQUE INDEX uniq_semestre_actif ON semestre (actif) WHERE actif")
    op.execute("""
        UPDATE semestre SET actif = true
        WHERE id = (SELECT id FROM semestre ORDER BY annee DESC, numero DESC LIMIT 1)
    """)

    # --- jeton ---------------------------------------------------------------
    op.create_table(
        "jeton",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("utilisateur_id", sa.Integer(), sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expire_le", sa.DateTime(timezone=True), nullable=False),
        sa.Column("utilise_le", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_jeton_utilisateur", "jeton", ["utilisateur_id"])


def downgrade() -> None:
    op.drop_table("jeton")
    op.execute("DROP INDEX IF EXISTS uniq_semestre_actif")
    op.drop_column("semestre", "podium_annonce")
    op.drop_column("semestre", "actif")
    for col in ("rappel_envoye", "annonce_envoyee", "description", "jeu", "lieu", "heure_debut"):
        op.drop_column("seance", col)
    op.execute("ALTER TABLE seance ALTER COLUMN nb_point TYPE INTEGER USING round(nb_point)::integer")
    op.drop_column("utilisateur", "cree_le")
    op.drop_column("utilisateur", "doit_changer_mdp")
    op.execute("DROP INDEX IF EXISTS uniq_utilisateur_mail_lower")
