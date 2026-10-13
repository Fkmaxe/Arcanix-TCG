"""Synchronisation périodique des rôles : Membre (comptes liés) et Top 3 du semestre."""
import logging

import discord
from discord.ext import commands, tasks

import config
from utils.api import ApiError

log = logging.getLogger("arcanix.roles")


async def synchroniser(guild: discord.Guild, donnees: dict) -> dict:
    """Applique les rôles attendus ; retourne le nombre de changements par rôle."""
    bilan = {"membre_ajouts": 0, "top3_ajouts": 0, "top3_retraits": 0}
    lies = {int(i) for i in donnees["membres"]}
    top3 = {int(i) for i in donnees["top3"]}

    role_membre = guild.get_role(config.ROLE_MEMBRE_ID) if config.ROLE_MEMBRE_ID else None
    if role_membre:
        for uid in lies:
            m = guild.get_member(uid)
            if m and role_membre not in m.roles:
                await m.add_roles(role_membre, reason="Compte Arcanix lié")
                bilan["membre_ajouts"] += 1

    role_top3 = guild.get_role(config.ROLE_TOP3_ID) if config.ROLE_TOP3_ID else None
    if role_top3:
        for m in list(role_top3.members):
            if m.id not in top3:
                await m.remove_roles(role_top3, reason="Sorti du top 3 du semestre")
                bilan["top3_retraits"] += 1
        for uid in top3:
            m = guild.get_member(uid)
            if m and role_top3 not in m.roles:
                await m.add_roles(role_top3, reason="Top 3 du semestre")
                bilan["top3_ajouts"] += 1
    return bilan


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if config.SYNC_ROLES and config.GUILD_ID:
            self.boucle.change_interval(minutes=config.ROLES_INTERVALLE_MIN)
            self.boucle.start()
        elif config.SYNC_ROLES:
            log.warning("Synchronisation des rôles ignorée : DISCORD_GUILD_ID non défini")

    def cog_unload(self):
        self.boucle.cancel()

    @tasks.loop(minutes=15)
    async def boucle(self):
        guild = self.bot.get_guild(config.GUILD_ID)
        if guild is None:
            log.error("Serveur %s introuvable pour la synchronisation des rôles", config.GUILD_ID)
            return
        try:
            donnees = await self.bot.api.roles()
            bilan = await synchroniser(guild, donnees)
        except ApiError as e:
            log.warning("Synchronisation des rôles impossible : %s", e.message)
            return
        except discord.Forbidden:
            log.error("Permission « Gérer les rôles » manquante, ou rôles placés au-dessus de celui du bot")
            return
        if any(bilan.values()):
            log.info("Rôles synchronisés : %s", bilan)

    @boucle.before_loop
    async def avant(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Roles(bot))
