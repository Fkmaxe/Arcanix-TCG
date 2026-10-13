"""Attribution des rôles Discord automatiques."""
import logging

import discord

import config

log = logging.getLogger("arcanix.roles")


async def donner_role_membre(user: discord.abc.User, guild: discord.Guild | None) -> bool:
    """Donne le rôle « Membre » (si configuré). Retourne True si le rôle a été ajouté."""
    if not config.ROLE_MEMBRE_ID or guild is None or not isinstance(user, discord.Member):
        return False
    role = guild.get_role(config.ROLE_MEMBRE_ID)
    if role is None or role in user.roles:
        return False
    try:
        await user.add_roles(role, reason="Compte Arcanix lié")
        return True
    except discord.Forbidden:
        log.error("Permission « Gérer les rôles » manquante ou rôle Membre placé au-dessus du rôle du bot")
    except discord.HTTPException as e:
        log.error("Attribution du rôle Membre impossible : %s", e)
    return False
