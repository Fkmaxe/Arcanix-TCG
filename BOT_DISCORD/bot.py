import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils import embeds
from utils.api import ApiClient

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

    async def setup_hook(self):
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
            log.info("🔁 %d commandes synchronisées sur le serveur %s", len(synced), config.GUILD_ID)
            # Supprime les commandes globales (ex. l'ancien /register à 4 champs) : sinon Discord
            # affiche chaque commande en double et l'ancienne version fait remplir les infos deux fois.
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            log.info("🧹 Anciennes commandes globales supprimées")
        else:
            synced = await self.tree.sync()
            log.info("🔁 %d commandes synchronisées globalement (propagation jusqu'à 1 h)", len(synced))

    async def close(self):
        await self.api.close()
        await super().close()

    async def on_ready(self):
        log.info("✅ Connecté en tant que %s (ID %s)", self.user, self.user.id)
        await self.change_presence(activity=discord.Game(name="/points · /seances"))

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "Tu n'as pas la permission d'utiliser cette commande."
        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = "Cette commande s'utilise sur le serveur de l'association."
        else:
            log.exception("Erreur dans /%s", interaction.command.name if interaction.command else "?", exc_info=error)
            msg = "Oups, une erreur inattendue est survenue. Réessaie dans un instant."
        send = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        try:
            await send(embed=embeds.erreur(msg), ephemeral=True)
        except discord.DiscordException:
            pass


if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN manquant")
    if not config.API_BOT_TOKEN:
        raise SystemExit("API_BOT_TOKEN manquant (doit être égal à DISCORD_BOT_TOKEN côté API)")
    ArcanixBot().run(config.DISCORD_TOKEN, log_handler=None)
