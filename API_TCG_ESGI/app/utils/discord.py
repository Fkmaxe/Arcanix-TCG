"""Notifications Discord via webhook (optionnel, exécutées en tâche de fond)."""
import logging

import httpx

from .. import config

log = logging.getLogger("arcanix.discord")

OR = 0xF5C24B
BRAISE = 0xFF7A1A


def envoyer_embed(title: str, description: str, color: int = OR, fields: list[dict] | None = None) -> None:
    if not config.DISCORD_WEBHOOK_URL:
        return
    embed = {"title": title, "description": description, "color": color}
    if fields:
        embed["fields"] = fields
    try:
        httpx.post(config.DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=5.0).raise_for_status()
    except Exception as e:  # une notification ne doit jamais faire échouer l'API
        log.warning("Notification Discord échouée : %s", e)


def notifier_participants(seance, membres: list) -> None:
    noms = ", ".join(f"**{m.prenom} {m.nom}**" for m in membres[:20])
    if len(membres) > 20:
        noms += f" et {len(membres) - 20} autre(s)"
    pluriel = "s" if len(membres) > 1 else ""
    envoyer_embed(
        title=f"🔥 {len(membres)} participant{pluriel} ajouté{pluriel}",
        description=f"{noms} — séance **{seance.nom}**",
        color=BRAISE,
        fields=[
            {"name": "Points gagnés", "value": f"**{float(seance.nb_point):g}** pts", "inline": True},
            {"name": "Date", "value": seance.date_seance.strftime("%d/%m/%Y"), "inline": True},
        ],
    )
