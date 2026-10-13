"""Réponses aux interactions : toujours répondre, même en cas d'erreur.

Une interaction différée (« … réfléchit ») qui ne reçoit jamais de réponse reste bloquée pour le membre.
Tout passe donc par `repondre` (qui retombe sur un lien en texte si Discord refuse un bouton) et toutes
les erreurs (commandes, formulaires, boutons) aboutissent à `signaler`.
"""
import logging

import discord
from discord import app_commands

from . import embeds
from .api import ApiError

log = logging.getLogger("arcanix.interactions")

PAS_DE_COMPTE = (
    "Aucun compte Arcanix n'est lié à ton Discord : tape `/register` (nouveau) "
    "ou `/lier` (compte déjà créé sur le site)."
)


def _sans_liens(embed: discord.Embed, view: discord.ui.View) -> discord.Embed:
    """Copie de l'embed avec les boutons-liens écrits en texte."""
    liens = [f"{b.label} : {b.url}" for b in view.children if isinstance(b, discord.ui.Button) and b.url]
    e = embed.copy()
    if liens:
        e.add_field(name="🔗 Liens", value="\n".join(liens)[:1024], inline=False)
    return e


async def repondre(interaction: discord.Interaction, *, embed: discord.Embed, view: discord.ui.View | None = None,
                   ephemeral: bool = True) -> None:
    """Réponse initiale ou suivi selon l'état de l'interaction.

    Si Discord refuse le message à cause d'un bouton (URL non publique…), il est renvoyé sans
    bouton, le lien écrit en texte : le membre a toujours une réponse.
    """
    envoyer = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
    try:
        await envoyer(embed=embed, view=view or discord.utils.MISSING, ephemeral=ephemeral)
    except discord.HTTPException as e:
        if view is None or e.status != 400:
            raise
        log.warning("Discord a refusé les boutons (%s) : envoi du lien en texte", e.text or e)
        envoyer = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await envoyer(embed=_sans_liens(embed, view), ephemeral=ephemeral)


def message_erreur(error: BaseException) -> str:
    """Message lisible pour le membre (le détail technique va dans les logs)."""
    original = getattr(error, "original", error)  # CommandInvokeError -> exception réelle
    if isinstance(original, ApiError):
        if original.status == 404 and "lié" in original.message:
            return PAS_DE_COMPTE
        return original.message
    if isinstance(error, app_commands.CommandSignatureMismatch):
        return "Cette commande vient d'être mise à jour : recharge Discord (Ctrl+R) puis réessaie."
    if isinstance(error, app_commands.MissingPermissions):
        return "Tu n'as pas la permission d'utiliser cette commande."
    if isinstance(error, app_commands.NoPrivateMessage):
        return "Cette commande s'utilise sur le serveur de l'association."
    if isinstance(error, app_commands.CheckFailure):
        return "Tu ne peux pas utiliser cette commande ici."
    log.error("Erreur inattendue", exc_info=original)
    return "Oups, une erreur inattendue est survenue. Réessaie dans un instant."


async def signaler(interaction: discord.Interaction, error: BaseException) -> None:
    """Affiche l'erreur au membre ; ne lève jamais (l'interaction a pu expirer)."""
    try:
        await repondre(interaction, embed=embeds.erreur(message_erreur(error)))
    except discord.HTTPException as e:
        log.warning("Impossible de signaler l'erreur au membre : %s", e)


class Formulaire(discord.ui.Modal):
    """Modal dont les erreurs sont toujours signalées au membre."""

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await signaler(interaction, error)


class Vue(discord.ui.View):
    """Vue dont les erreurs (boutons, menus) sont toujours signalées au membre."""

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await signaler(interaction, error)
