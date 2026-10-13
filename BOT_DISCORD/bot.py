import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils import embeds
from utils.api import ApiClient
from utils.interactions import signaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")
log = logging.getLogger("arcanix")

EXTENSIONS = ("cogs.compte", "cogs.membres", "cogs.moderation", "cogs.inscriptions", "cogs.annonces", "cogs.roles")


class ArcanixBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Seule la synchronisation des rôles a besoin de l'intent privilégié « Server Members »
        intents.members = config.SYNC_ROLES
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.api = ApiClient()
        self._nettoyage_fait = False

    async def setup_hook(self):
        if not embeds.adresse_publique(config.FRONTEND_URL):
            log.warning("FRONTEND_URL=%s n'est pas une adresse publique : les liens envoyés aux membres "
                        "(mot de passe, séances) ne fonctionneront pas depuis leur téléphone", config.FRONTEND_URL)
        await self.api.start()
        for ext in EXTENSIONS:
            await self.load_extension(ext)
        self.tree.on_error = self.on_app_command_error
        await self.synchroniser_commandes()

    async def synchroniser_commandes(self):
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("🔁 %d commandes synchronisées sur le serveur %s : %s", len(synced), config.GUILD_ID,
                     ", ".join(f"/{c.name}" for c in synced))
            # Supprime les commandes globales (ex. l'ancien /register à 4 champs) : sinon Discord
            # affiche chaque commande en double et l'ancienne version fait remplir les infos deux fois.
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            log.info("🧹 Anciennes commandes globales supprimées")
        else:
            synced = await self.tree.sync()
            log.info("🔁 %d commandes synchronisées globalement (propagation jusqu'à 1 h)", len(synced))

    async def nettoyer_commandes_serveurs(self):
        """Supprime les commandes enregistrées sur les serveurs où elles ne devraient pas être.

        Cas typique : le bot a d'abord tourné avec un autre DISCORD_GUILD_ID (ou sans), et Discord
        a gardé l'ancienne liste en plus de la nouvelle : chaque commande apparaît en double.
        """
        for guild in self.guilds:
            if guild.id == config.GUILD_ID:
                continue
            try:
                anciennes = await self.tree.fetch_commands(guild=guild)
                if anciennes:
                    self.tree.clear_commands(guild=guild)
                    await self.tree.sync(guild=guild)
                    log.info("🧹 %d commande(s) en double supprimée(s) sur le serveur %s", len(anciennes), guild.name)
            except discord.HTTPException as e:
                log.warning("Nettoyage des commandes impossible sur %s : %s", guild.name, e)

    async def close(self):
        await self.api.close()
        await super().close()

    async def on_ready(self):
        log.info("✅ Connecté en tant que %s (ID %s) sur %d serveur(s)", self.user, self.user.id, len(self.guilds))
        await self.change_presence(activity=discord.Game(name="/points · /seances"))
        if not self._nettoyage_fait:  # on_ready est rappelé à chaque reconnexion
            self._nettoyage_fait = True
            await self.nettoyer_commandes_serveurs()

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await signaler(interaction, error)


if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN manquant")
    if not config.API_BOT_TOKEN:
        raise SystemExit("API_BOT_TOKEN manquant (doit être égal à DISCORD_BOT_TOKEN côté API)")
    ArcanixBot().run(config.DISCORD_TOKEN, log_handler=None)
