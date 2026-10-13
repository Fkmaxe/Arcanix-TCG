"""Commandes de consultation pour tous les membres."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.api import ApiError

PAS_DE_COMPTE = "Aucun compte Arcanix n'est lié à ton Discord : tape `/register` (nouveau) ou `/lier` (compte du site existant)."


class Membres(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _semestre_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            semestres = await self.bot.api.semestres()
        except ApiError:
            return []
        choix = [app_commands.Choice(name=f"{embeds.semestre(s)}{' (en cours)' if s.get('actif') else ''}", value=s["id"])
                 for s in semestres]
        return [c for c in choix if current.lower() in c.name.lower()][:25]

    async def _envoyer_points(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m = await self.bot.api.membre(interaction.user.id)
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(PAS_DE_COMPTE if e.status == 404 else e.message), ephemeral=True)
        e = embeds.embed(f"🔥 {embeds.pts(m['points'])} points", f"Semestre **{embeds.semestre(m['semestre'])}**")
        e.add_field(name="🏆 Rang", value=f"#{m['rang']}" if m["rang"] else "Non classé", inline=True)
        e.add_field(name="📅 Présences", value=str(m["presences"]), inline=True)
        e.add_field(name="✨ Total cumulé", value=f"{embeds.pts(m['total_points'])} pts", inline=True)
        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="points", description="Tes points du semestre en cours")
    async def points(self, interaction: discord.Interaction):
        await self._envoyer_points(interaction)

    @app_commands.command(name="mypoint", description="Tes points du semestre en cours (alias de /points)")
    async def mypoint(self, interaction: discord.Interaction):
        await self._envoyer_points(interaction)

    @app_commands.command(name="profil", description="Le profil Arcanix d'un membre")
    @app_commands.describe(membre="Le membre à consulter (toi par défaut)")
    async def profil(self, interaction: discord.Interaction, membre: discord.Member | None = None):
        cible = membre or interaction.user
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m = await self.bot.api.membre(cible.id)
        except ApiError as e:
            msg = (PAS_DE_COMPTE if cible == interaction.user else f"{cible.display_name} n'a pas lié son compte Arcanix.") \
                if e.status == 404 else e.message
            return await interaction.followup.send(embed=embeds.erreur(msg), ephemeral=True)
        e = embeds.embed(f"{m['prenom']} {m['nom'][:1]}.", f"{m['classe']} · {'🛡️ Modération' if m['role_utilisateur'] != 'user' else 'Membre'}", thumbnail=False)
        e.set_thumbnail(url=cible.display_avatar.url)
        e.add_field(name=f"Semestre {embeds.semestre(m['semestre'])}", value=f"**{embeds.pts(m['points'])} pts** · rang #{m['rang'] or '—'}", inline=False)
        e.add_field(name="Présences", value=str(m["presences"]), inline=True)
        e.add_field(name="Total cumulé", value=f"{embeds.pts(m['total_points'])} pts", inline=True)
        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="classement", description="Le top 10 du semestre")
    @app_commands.describe(semestre="Semestre (en cours par défaut)")
    @app_commands.autocomplete(semestre=_semestre_autocomplete)
    async def classement(self, interaction: discord.Interaction, semestre: int | None = None):
        await interaction.response.defer(thinking=True)
        try:
            c = await self.bot.api.classement(semestre, limit=10)
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message))
        if not c["lignes"]:
            return await interaction.followup.send(embed=embeds.embed("🏆 Classement", "Aucune présence enregistrée pour l'instant."))
        lignes = [
            f"{embeds.rang(l['rang'])} **{l['prenom']} {l['nom']}** — {embeds.pts(l['points'])} pts"
            for l in c["lignes"]
        ]
        e = embeds.embed(f"🏆 Classement · {embeds.semestre(c['semestre'])}", "\n".join(lignes))
        try:
            moi = await self.bot.api.membre(interaction.user.id)
            if moi["rang"] and (not semestre or (c["semestre"] and moi["semestre"] and c["semestre"]["id"] == moi["semestre"]["id"])):
                e.add_field(name="Ta position", value=f"#{moi['rang']} avec {embeds.pts(moi['points'])} pts", inline=False)
        except ApiError:
            pass
        view = embeds.bouton_lien("Classement complet", embeds.site_url("/classement"), "📜")
        await interaction.followup.send(embed=e, view=view or discord.utils.MISSING)

    @app_commands.command(name="seances", description="Les prochaines séances de l'association")
    async def seances(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            seances = await self.bot.api.seances_a_venir(limit=6)
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(e.message), ephemeral=True)
        if not seances:
            return await interaction.followup.send(embed=embeds.embed("📅 Prochaines séances", "Rien de prévu pour le moment, reste à l'affût !"), ephemeral=True)
        e = embeds.embed("📅 Prochaines séances")
        for s in seances:
            e.add_field(name=s["nom"], value=embeds.ligne_seance(s), inline=False)
        view = embeds.bouton_lien("Voir sur le site", embeds.site_url("/seances"), "🌐")
        await interaction.followup.send(embed=e, view=view or discord.utils.MISSING, ephemeral=True)

    @app_commands.command(name="historique", description="Tes 10 dernières séances")
    async def historique(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            h = await self.bot.api.historique(interaction.user.id)
        except ApiError as e:
            return await interaction.followup.send(embed=embeds.erreur(PAS_DE_COMPTE if e.status == 404 else e.message), ephemeral=True)
        if not h:
            return await interaction.followup.send(embed=embeds.embed("📜 Historique", "Aucune participation pour l'instant."), ephemeral=True)
        lignes = [
            f"{'✅' if p['present'] else '❌'} **{p['seance_nom']}** · {embeds.date_longue(p['date_seance'])}"
            + (f" · +{embeds.pts(p['nb_point'])}" if p["present"] else " · absent")
            for p in h
        ]
        await interaction.followup.send(embed=embeds.embed("📜 Tes dernières séances", "\n".join(lignes)), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Membres(bot))
