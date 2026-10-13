from discord import app_commands
from discord.ext import commands
from utils.api import create_user

class RegisterCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="Créer ton compte Arcanix")
    @app_commands.describe(email="Ton adresse mail", prenom="Ton prénom", nom="Ton nom", classe="Ta classe")
    async def register(self, interaction, email: str, prenom: str, nom: str, classe: str):
        await interaction.response.defer(ephemeral=True)
        try:
            user = await create_user(interaction.user.id, email, prenom, nom, classe)
            await interaction.followup.send(f"✅ Compte créé pour **{user['prenom']} {user['nom']}**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {str(e)}")

async def setup(bot):
    await bot.add_cog(RegisterCommand(bot))