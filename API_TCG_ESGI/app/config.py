# app/config.py — réglages lus depuis l'environnement
import os
import secrets


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


DEBUG = _bool("DEBUG")

JWT_SECRET = os.getenv("JWT_SECRET") or ""
if not JWT_SECRET:
    if not DEBUG:
        raise RuntimeError("JWT_SECRET doit être défini (ou DEBUG=true pour le développement)")
    # En dev : secret éphémère (les sessions sautent à chaque redémarrage)
    JWT_SECRET = secrets.token_urlsafe(48)
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Durées de validité des jetons
JETON_MDP_HEURES = int(os.getenv("JETON_MDP_HEURES", "48"))
JETON_DISCORD_MINUTES = int(os.getenv("JETON_DISCORD_MINUTES", "15"))

# Emails (SMTP). Sans SMTP_HOST, les fonctions d'email sont désactivées.
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "Arcanix <no-reply@arcanix.local>")
# 'starttls' (port 587), 'ssl' (port 465) ou 'aucune' (relais local / Mailpit)
SMTP_SECURITE = os.getenv("SMTP_SECURITE", "starttls").strip().lower()
SMTP_ACTIF = bool(SMTP_HOST)

# Pointage par QR code
QR_PERIODE_S = int(os.getenv("QR_PERIODE_S", "30"))
POINTAGE_DUREE_H = int(os.getenv("POINTAGE_DUREE_H", "4"))
