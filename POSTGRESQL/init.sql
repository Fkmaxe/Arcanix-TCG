 -- (Optionnel) pour rendre l'unicité de l'email insensible à la casse
-- CREATE EXTENSION IF NOT EXISTS citext;

-- ===== Tables de référence =====

CREATE TABLE semestre (
    id          SERIAL PRIMARY KEY,
    annee       SMALLINT         NOT NULL,              -- ex: 2025
    numero      SMALLINT         NOT NULL CHECK (numero IN (1, 2)),  -- semestre 1 ou 2
    UNIQUE (annee, numero)                               -- un seul S1 et S2 par année
);

CREATE TABLE utilisateur (
    id              SERIAL PRIMARY KEY,
    discord_id      VARCHAR(255) UNIQUE,
    nom             VARCHAR(100)    NOT NULL,
    prenom          VARCHAR(100)    NOT NULL,
    adresse_mail    VARCHAR(255)    NOT NULL,           -- ou CITEXT si l'extension est activée
    mot_de_passe_hash VARCHAR(255)    NOT NULL,
    role_utilisateur VARCHAR(50)    NOT NULL,           -- ex: 'etudiant', 'enseignant', 'admin'
    classe          VARCHAR(50)     NOT NULL,           -- ex: 'L3-INFO-A'
    CONSTRAINT utilisateur_adresse_mail_unique UNIQUE (adresse_mail)
);

-- ===== Entités métiers =====

CREATE TABLE seance (
    id              SERIAL PRIMARY KEY,
    nom             VARCHAR(150)    NOT NULL,
    date_seance     DATE            NOT NULL,           -- évite le nom réservé "date"
    nb_point        INTEGER         NOT NULL CHECK (nb_point >= 0),
    semestre_id     INTEGER         NOT NULL REFERENCES semestre(id) ON DELETE RESTRICT
);

-- ===== Table de liaison (participation) =====
-- indique quels utilisateurs ont participé à quelles séances

CREATE TABLE participation (
    utilisateur_id  INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    seance_id       INTEGER NOT NULL REFERENCES seance(id)      ON DELETE CASCADE,
    present         BOOLEAN NOT NULL DEFAULT TRUE,              -- facultatif: présent/absent
    commentaire     TEXT,                                       -- facultatif
    PRIMARY KEY (utilisateur_id, seance_id)
);

-- ===== Index utiles =====
CREATE INDEX idx_seance_semestre    ON seance (semestre_id);
CREATE INDEX idx_seance_date        ON seance (date_seance);
CREATE INDEX idx_participation_user ON participation (utilisateur_id);
CREATE INDEX idx_participation_sea  ON participation (seance_id);
