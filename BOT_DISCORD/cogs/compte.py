"""Inscription, liaison de compte et réinitialisation du mot de passe."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.interactions import Formulaire, repondre
from utils.roles import donner_role_membre


def message_lien(titre: str, texte: str, label: str, url: str) -> tuple[discord.Embed, discord.ui.View | None]:
    """Embed + bouton vers le lien ; si l'adresse n'est pas publique, le lien est écrit en clair."""
    e = embeds.embed(titre, texte)
    view = embeds.bouton_lien(label, url, "🔑")
    if view is None:
        e.add_field(name="🔗 Lien", value=url, inline=False)
    return e, view


class InscriptionModal(Formulaire, title="Rejoindre Arcanix"):
    prenom = discord.ui.TextInput(label="Prénom", max_length=100)
    nom = discord.ui.TextInput(label="Nom", max_length=100)
    email = discord.ui.TextInput(label="Adresse email", placeholder="prenom.nom@exemple.fr", max_length=255)
    classe = discord.ui.TextInput(label="Classe", placeholder="ex. 3A-INFO", max_length=50)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        prenom = str(self.prenom).strip()
        r = await self.bot.api.inscription(interaction.user.id, prenom, str(self.nom).strip(),
                                           str(self.email).strip(), str(self.classe).strip())
        e, view = message_lien(
            f"Bienvenue dans la guilde, {prenom} ! 🔥",
            "Ton compte Arcanix est créé et lié à ton Discord.\n"
            f"Dernière étape : **choisis ton mot de passe** pour le site (lien valable {r['expire_dans_heures']} h, "
            "à usage unique — ne le partage pas).",
            "Définir mon mot de passe", r["url"],
        )
        e.add_field(name="Ensuite", value="`/points` · `/seances` · `/classement`", inline=False)
        await repondre(interaction, embed=e, view=view)
        # Après la réponse : un souci de rôle ne doit pas priver le membre de son lien
        await donner_role_membre(interaction.user, interaction.guild)


class Compte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="Créer ton compte Arcanix lié à ton Discord")
    async def register(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InscriptionModal(self.bot))

    @app_commands.command(name="lier", description="Lier ton compte du site à ce Discord (code à générer sur ton profil)")
    @app_commands.describe(code="Code à 6 caractères affiché sur ta page Profil du site")
    async def lier(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        m = await self.bot.api.lier(interaction.user.id, code.strip())
        await repondre(interaction, embed=embeds.succes(
            f"Compte lié : bienvenue **{m['prenom']} {m['nom']}** ! Tu as {embeds.pts(m['points'])} pts ce semestre."))
        await donner_role_membre(interaction.user, interaction.guild)

    @app_commands.command(name="reinitialiser", description="Recevoir un lien pour (re)définir ton mot de passe du site")
    async def reinitialiser(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        r = await self.bot.api.reinitialiser(interaction.user.id)
        e, view = message_lien("🔑 Nouveau mot de passe",
                               f"Lien personnel, valable {r['expire_dans_heures']} h et utilisable une seule fois.",
                               "Choisir mon mot de passe", r["url"])
        await repondre(interaction, embed=e, view=view)


async def setup(bot):
    await bot.add_cog(Compte(bot))
