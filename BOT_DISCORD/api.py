import aiohttp
import os

API_BASE = os.getenv("API_BASE_URL")
API_TOKEN = os.getenv("API_BOT_TOKEN")

async def create_user(discord_id, email, prenom, nom, classe):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/discord/users", headers={
            "Content-Type": "application/json",
            "x-bot-token": API_TOKEN
        }, json={
            "discord_id": str(discord_id),
            "adresse_mail": email,
            "prenom": prenom,
            "nom": nom,
            "classe": classe
        }) as resp:
            if resp.status != 201:
                raise Exception(f"Échec création : {resp.status}")
            return await resp.json()

async def get_points(discord_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/discord/points/discord/{discord_id}") as resp:
            if resp.status != 200:
                raise Exception("Aucun point trouvé")
            return await resp.json()