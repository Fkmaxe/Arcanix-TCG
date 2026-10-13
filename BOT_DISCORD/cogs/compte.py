"""Inscription, liaison de compte et réinitialisation du mot de passe."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.roles import donner_role_membre
from utils.api import ApiError


class InscriptionModal(discord.ui.Modal, title="Rejoindre Arcanix"):
    prenom = discord.ui.TextInput(label="Prénom", max_length=100)
    nom = discord.ui.TextInput(label="Nom", max_length=100)
    email = discord.ui.TextInput(label="Adresse email", placeholder="prenom.nom@exemple.fr", max_length=255)
    classe = discord.ui.TextInput(label="Classe", placeholder="ex. 3A-INFO", max_length=50)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            r = await self.bot.api.inscription(
                interaction.user.id, str(self.prenom).strip(), str(self.nom).strip(),
                str(self.email).strip(), str(self.classe).strip(),
            )
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message), ephemeral=True)
        e = embeds.embed(
            f"Bienvenue dans la guilde, {str(self.prenom).strip()} ! 🔥",
            "Ton compte Arcanix est créé et lié à ton Discord.\n"
            f"Dernière étape : **choisis ton mot de passe** pour le site (lien valable {r['expire_dans_heures']} h, "
            "à usage unique — ne le partage pas).",
        )
        e.add_field(name="Ensuite", value="`/points` · `/seances` · `/classement`", inline=False)
        await donner_role_membre(interaction.user, interaction.guild)
        view = embeds.bouton_lien("Définir mon mot de passe", r["url"], "🔑")
        if view is None:
            e.add_field(name="Lien", value=r["url"], inline=False)
        await interaction.followup.send(embed=e, view=view or discord.utils.MISSING, ephemeral=True)


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
        try:
            m = await self.bot.api.lier(interaction.user.id, code.strip())
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message), ephemeral=True)
        await donner_role_membre(interaction.user, interaction.guild)
        await interaction.followup.send(
            embed=embeds.succes(f"Compte lié : bienvenue **{m['prenom']} {m['nom']}** ! Tu as {embeds.pts(m['points'])} pts ce semestre."),
            ephemeral=True,
        )

    @app_commands.command(name="reinitialiser", description="Recevoir un lien pour (re)définir ton mot de passe du site")
    async def reinitialiser(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            r = await self.bot.api.reinitialiser(interaction.user.id)
        except ApiError as e:
            msg = e.message if e.status != 404 else "Aucun compte n'est lié à ton Discord. Utilise `/register` ou `/lier`."
            return await interaction.followup.send(embed=embeds.erreur(msg), ephemeral=True)
        e = embeds.embed("🔑 Nouveau mot de passe", f"Lien personnel, valable {r['expire_dans_heures']} h et utilisable une seule fois.")
        view = embeds.bouton_lien("Choisir mon mot de passe", r["url"], "🔑")
        if view is None:
            e.add_field(name="Lien", value=r["url"], inline=False)
        await interaction.followup.send(embed=e, view=view or discord.utils.MISSING, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Compte(bot))
