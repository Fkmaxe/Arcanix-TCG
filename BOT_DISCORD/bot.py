import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

class ArcanixBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Charge les commandes
        await self.load_extension("commands.register")
        await self.load_extension("commands.mypoint")

        # Synchronisation globale (peut prendre 1h la 1ère fois)
        await self.tree.sync()
        print("🔁 Commandes slash synchronisées (global)")

bot = ArcanixBot()

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user} (ID: {bot.user.id})")

bot.run(TOKEN)