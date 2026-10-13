"""Commandes réservées à la modération (le rôle est vérifié par l'API via le compte lié)."""
import re
from datetime import date

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.api import ApiError

JEU_CHOIX = [app_commands.Choice(name=label, value=val) for val, label in embeds.JEUX.items()]


def parse_date(txt: str) -> str:
    txt = txt.strip()
    if m := re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?", txt):
        j, mo, a = int(m[1]), int(m[2]), m[3]
        annee = date.today().year if not a else (2000 + int(a) if len(a) == 2 else int(a))
        return date(annee, mo, j).isoformat()
    return date.fromisoformat(txt).isoformat()


def parse_heure(txt: str) -> str | None:
    txt = txt.strip().lower()
    if not txt:
        return None
    m = re.fullmatch(r"(\d{1,2})\s*[h:]\s*(\d{2})?", txt)
    if not m or int(m[1]) > 23 or int(m[2] or 0) > 59:
        raise ValueError("heure")
    return f"{int(m[1]):02d}:{int(m[2] or 0):02d}"


class SeanceModal(discord.ui.Modal, title="Nouvelle séance"):
    nom = discord.ui.TextInput(label="Nom", placeholder="Tournoi Pokémon", max_length=150)
    jour = discord.ui.TextInput(label="Date (JJ/MM/AAAA)", placeholder="25/10/2026", max_length=10)
    heure = discord.ui.TextInput(label="Heure (optionnel)", placeholder="18h30", required=False, max_length=5)
    lieu = discord.ui.TextInput(label="Lieu (optionnel)", placeholder="Salle B204", required=False, max_length=150)
    points = discord.ui.TextInput(label="Points par présence", default="1", max_length=6)

    def __init__(self, bot, jeu: str | None):
        super().__init__()
        self.bot = bot
        self.jeu = jeu

    async def on_submit(self, interaction: discord.Interaction):
        try:
            jour = parse_date(str(self.jour))
            heure = parse_heure(str(self.heure))
            nb = float(str(self.points).replace(",", "."))
            if nb < 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                embed=embeds.erreur("Date (JJ/MM/AAAA), heure (18h30) ou points invalides."), ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            s = await self.bot.api.creer_seance(
                interaction.user.id, nom=str(self.nom).strip(), date_seance=jour, heure_debut=heure,
                lieu=str(self.lieu).strip() or None, jeu=self.jeu, nb_point=nb,
            )
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message), ephemeral=True)
        e = embeds.seance_embed(s, f"✅ Séance créée : {s['nom']}", embeds.SUCCES)
        e.description = "Elle sera annoncée automatiquement dans le salon des annonces."
        view = embeds.bouton_lien("Ouvrir sur le site", embeds.site_url(f"/seances/{s['id']}"), "🌐")
        await interaction.followup.send(embed=e, view=view or discord.utils.MISSING, ephemeral=True)


class PresenceView(discord.ui.View):
    """Sélection multiple des membres présents (25 max par validation)."""

    def __init__(self, bot, seance: dict, auteur_id: int):
        super().__init__(timeout=600)
        self.bot = bot
        self.seance = seance
        self.auteur_id = auteur_id
        self.selection: list[discord.abc.User] = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.auteur_id

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Choisis les membres présents…", min_values=1, max_values=25)
    async def choisir(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        self.selection = [u for u in select.values if not u.bot]
        await interaction.response.defer()

    @discord.ui.button(label="Valider les présences", style=discord.ButtonStyle.success, emoji="✅")
    async def valider(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not self.selection:
            return await interaction.response.send_message(embed=embeds.erreur("Sélectionne au moins un membre."), ephemeral=True)
        await interaction.response.defer()
        try:
            r = await self.bot.api.presences(self.seance["id"], self.auteur_id, [u.id for u in self.selection])
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message), ephemeral=True)
        mention = lambda ids: ", ".join(f"<@{i}>" for i in ids) or "—"  # noqa: E731
        e = embeds.embed(f"📋 Appel · {r['seance']['nom']}", f"{r['seance']['nb_presents']} présent(s) au total.", embeds.SUCCES, thumbnail=False)
        e.add_field(name=f"✅ Ajoutés (+{embeds.pts(r['seance']['nb_point'])} pts)", value=mention(r["ajoutes"]), inline=False)
        if r["deja_presents"]:
            e.add_field(name="☑️ Déjà présents", value=mention(r["deja_presents"]), inline=False)
        if r["non_lies"]:
            e.add_field(name="⚠️ Sans compte lié (non comptés)", value=mention(r["non_lies"]) + "\n→ ils doivent faire `/register` ou `/lier`.", inline=False)
        self.selection = []
        await interaction.edit_original_response(embed=e, view=self)


@app_commands.default_permissions(manage_events=True)
@app_commands.guild_only()
class Moderation(commands.GroupCog, group_name="mod", group_description="Outils de modération Arcanix"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def _seance_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            seances = await self.bot.api.seances_recherche(current)
        except ApiError:
            return []
        return [
            app_commands.Choice(name=f"{s['nom']} · {embeds.date_longue(s['date_seance'])}"[:100], value=s["id"])
            for s in seances
        ][:25]

    @app_commands.command(name="seance", description="Créer une séance (annoncée automatiquement)")
    @app_commands.describe(jeu="Jeu de la séance")
    @app_commands.choices(jeu=JEU_CHOIX)
    async def seance(self, interaction: discord.Interaction, jeu: app_commands.Choice[str] | None = None):
        await interaction.response.send_modal(SeanceModal(self.bot, jeu.value if jeu else None))

    @app_commands.command(name="presence", description="Valider la présence de membres à une séance")
    @app_commands.describe(seance="Séance (±30 jours)")
    @app_commands.autocomplete(seance=_seance_autocomplete)
    async def presence(self, interaction: discord.Interaction, seance: int):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            # Vérifie les droits tôt (403 si l'auteur n'est pas modérateur)
            moi = await self.bot.api.membre(interaction.user.id)
            if moi["role_utilisateur"] not in ("moderator", "admin"):
                return await interaction.followup.send(embed=embeds.erreur("Commande réservée à la modération."), ephemeral=True)
            choix = await self.bot.api.seances_recherche("")
        except ApiError as e:
            msg = "Lie d'abord ton compte avec `/lier`." if e.status == 404 else e.message
            return await interaction.followup.send(embed=embeds.erreur(msg), ephemeral=True)
        s = next((x for x in choix if x["id"] == seance), None)
        if not s:
            return await interaction.followup.send(embed=embeds.erreur("Séance introuvable : choisis-la dans la liste."), ephemeral=True)
        e = embeds.embed(f"📋 Appel · {s['nom']}", embeds.ligne_seance(s), thumbnail=False)
        e.set_footer(text="Sélectionne jusqu'à 25 membres puis valide. Recommence pour en ajouter d'autres.")
        await interaction.followup.send(embed=e, view=PresenceView(self.bot, s, interaction.user.id), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
