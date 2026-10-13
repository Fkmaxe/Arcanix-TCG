from discord import app_commands
from discord.ext import commands
from utils.api import get_points

class MyPointCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mypoint", description="Consulte tes points du dernier semestre")
    async def mypoint(self, interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            data = await get_points(interaction.user.id)
            points = data["points"]
            semestre = data["semestre"]
            await interaction.followup.send(f"📊 Tu as **{points} points** pour le semestre **{semestre['annee']}-S{semestre['numero']}**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {str(e)}")

async def setup(bot):
    await bot.add_cog(MyPointCommand(bot))