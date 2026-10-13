import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str) -> int | None:
    v = os.getenv(name, "").strip()
    return int(v) if v.isdigit() else None


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")
# Secret partagé avec l'API (variable DISCORD_BOT_TOKEN côté API)
API_BOT_TOKEN = os.getenv("API_BOT_TOKEN", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

# Synchronisation instantanée des commandes sur un serveur (sinon global, ~1 h)
GUILD_ID = _int("DISCORD_GUILD_ID")
# Salon des annonces automatiques (nouvelles séances, rappels, podiums)
ANNONCES_CHANNEL_ID = _int("DISCORD_ANNONCES_CHANNEL_ID")
# Rôle à mentionner dans les annonces (optionnel)
ANNONCES_ROLE_ID = _int("DISCORD_ANNONCES_ROLE_ID")
ANNONCES_INTERVALLE_MIN = int(os.getenv("ANNONCES_INTERVALLE_MIN", "5"))
