import os
import httpx
from typing import Optional

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

async def send_discord_notification(
    title: str,
    description: str,
    color: int = 0x5865F2,  # Discord blurple
    fields: Optional[list[dict]] = None
):
    """
    Envoie une notification Discord via webhook

    Args:
        title: Titre du message
        description: Description du message
        color: Couleur de l'embed (int hex)
        fields: Liste de dictionnaires avec 'name' et 'value'
    """
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL non configuré, notification ignorée")
        return

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": None,  # Discord ajoutera l'heure actuelle
    }

    if fields:
        embed["fields"] = fields

    payload = {
        "embeds": [embed]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            print(f"✅ Notification Discord envoyée: {title}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de la notification Discord: {e}")


def send_discord_notification_sync(
    title: str,
    description: str,
    color: int = 0x5865F2,
    fields: Optional[list[dict]] = None
):
    """
    Version synchrone de send_discord_notification
    """
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL non configuré, notification ignorée")
        return

    embed = {
        "title": title,
        "description": description,
        "color": color,
    }

    if fields:
        embed["fields"] = fields

    payload = {
        "embeds": [embed]
    }

    try:
        response = httpx.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5.0)
        response.raise_for_status()
        print(f"✅ Notification Discord envoyée: {title}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de la notification Discord: {e}")
