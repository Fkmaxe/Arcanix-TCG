"""Schéma initial (identique à l'ancien POSTGRESQL/init.sql)

Les bases existantes sont « stampées » sur cette révision par app/migrate.py.

Revision ID: 0001
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE semestre (
        id          SERIAL PRIMARY KEY,
        annee       SMALLINT NOT NULL,
        numero      SMALLINT NOT NULL CHECK (numero IN (1, 2)),
        UNIQUE (annee, numero)
    );

    CREATE TABLE utilisateur (
        id                SERIAL PRIMARY KEY,
        discord_id        VARCHAR(255) UNIQUE,
        nom               VARCHAR(100) NOT NULL,
        prenom            VARCHAR(100) NOT NULL,
        adresse_mail      VARCHAR(255) NOT NULL,
        mot_de_passe_hash VARCHAR(255) NOT NULL,
        role_utilisateur  VARCHAR(50)  NOT NULL,
        classe            VARCHAR(50)  NOT NULL,
        CONSTRAINT utilisateur_adresse_mail_unique UNIQUE (adresse_mail)
    );

    CREATE TABLE seance (
        id          SERIAL PRIMARY KEY,
        nom         VARCHAR(150) NOT NULL,
        date_seance DATE         NOT NULL,
        nb_point    INTEGER      NOT NULL CHECK (nb_point >= 0),
        semestre_id INTEGER      NOT NULL REFERENCES semestre(id) ON DELETE RESTRICT
    );

    CREATE TABLE participation (
        utilisateur_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
        seance_id      INTEGER NOT NULL REFERENCES seance(id)      ON DELETE CASCADE,
        present        BOOLEAN NOT NULL DEFAULT TRUE,
        commentaire    TEXT,
        PRIMARY KEY (utilisateur_id, seance_id)
    );

    CREATE INDEX idx_seance_semestre    ON seance (semestre_id);
    CREATE INDEX idx_seance_date        ON seance (date_seance);
    CREATE INDEX idx_participation_user ON participation (utilisateur_id);
    CREATE INDEX idx_participation_sea  ON participation (seance_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE participation; DROP TABLE seance; DROP TABLE utilisateur; DROP TABLE semestre;")
