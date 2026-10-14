"""Tests sur une vraie base Postgres.

TEST_DATABASE_URL pointe vers une base dédiée (elle est vidée et recréée).
Ex. : TEST_DATABASE_URL=postgresql+psycopg://admin:password@localhost:5432/arcanix_test
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TEST_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://admin:password@localhost:55432/arcanix_test")
os.environ["DATABASE_URL"] = TEST_URL
os.environ.setdefault("JWT_SECRET", "secret-de-test")
os.environ["DISCORD_BOT_TOKEN"] = "bot-test"
os.environ["DISCORD_WEBHOOK_URL"] = ""
os.environ["FRONTEND_URL"] = "https://arcanix.test"
os.environ["EMAIL_DOMAINE_ECOLE"] = "ex.com"  # domaine « école » des tests


def _recreer_base():
    url = make_url(TEST_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        c.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


_recreer_base()

from app import migrate  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Utilisateur  # noqa: E402
from app.security import create_token, hash_password  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

migrate.main()  # installation neuve : toutes les migrations depuis zéro


@pytest.fixture(autouse=True)
def base_vide():
    from app.ratelimit import connexion
    connexion.reset()
    with engine.begin() as c:
        c.execute(text("TRUNCATE participation, seance, semestre, jeton, utilisateur RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def make_user(db):
    def _make(role="user", email=None, discord_id=None, prenom="Test", nom="Membre", classe="3A", password="motdepasse"):
        u = Utilisateur(nom=nom, prenom=prenom, adresse_mail=email or f"{role}{db.query(Utilisateur).count()}@ex.com",
                        mot_de_passe_hash=hash_password(password), role_utilisateur=role, classe=classe,
                        discord_id=discord_id)
        db.add(u)
        db.commit()
        return u
    return _make


def auth(user) -> dict:
    return {"Authorization": f"Bearer {create_token(user)}"}


BOT = {"x-bot-token": "bot-test"}
