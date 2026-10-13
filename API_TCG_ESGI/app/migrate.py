"""Applique les migrations au démarrage du conteneur.

Une base créée par l'ancien init.sql (tables présentes, pas de table alembic_version)
est d'abord marquée sur la révision 0001 avant d'appliquer les suivantes.
"""
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from .database import engine

ROOT = Path(__file__).resolve().parent.parent


def wait_for_db(tries: int = 30) -> None:
    for i in range(tries):
        try:
            with engine.connect():
                return
        except OperationalError:
            print(f"⏳ Base indisponible, nouvel essai ({i + 1}/{tries})…")
            time.sleep(2)
    raise RuntimeError("Base de données injoignable")


def main() -> None:
    wait_for_db()
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    tables = inspect(engine).get_table_names()
    if "utilisateur" in tables and "alembic_version" not in tables:
        print("📌 Base existante détectée : stamp sur la révision 0001")
        command.stamp(cfg, "0001")
    command.upgrade(cfg, "head")
    print("✅ Migrations à jour")


if __name__ == "__main__":
    main()
