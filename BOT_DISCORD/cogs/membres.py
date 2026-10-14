"""Commandes de consultation pour tous les membres."""
import asyncio
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.api import ApiError
from utils.interactions import repondre


class Membres(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._semestres: tuple[float, list[dict]] = (0.0, [])

    async def _liste_semestres(self) -> list[dict]:
        # Petit cache : l'autocomplétion appelle à chaque frappe
        expire, semestres = self._semestres
        if time.monotonic() > expire:
            semestres = await self.bot.api.semestres()
            self._semestres = (time.monotonic() + 60, semestres)
        return semestres

    async def _semestre_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            semestres = await self._liste_semestres()
        except ApiError:
            return []
        choix = [app_commands.Choice(name=f"{embeds.semestre(s)}{' (en cours)' if s.get('actif') else ''}", value=s["id"])
                 for s in semestres]
        return [c for c in choix if current.lower() in c.name.lower()][:25]

    @app_commands.command(name="points", description="Tes points du semestre en cours")
    async def points(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        m = await self.bot.api.membre(interaction.user.id)
        e = embeds.embed(f"🔥 {embeds.pts(m['points'])} points", f"Semestre **{embeds.semestre(m['semestre'])}**")
        e.add_field(name="🏆 Rang", value=embeds.texte_rang(m), inline=True)
        e.add_field(name="📅 Présences", value=str(m["presences"]), inline=True)
        e.add_field(name="✨ Total cumulé", value=f"{embeds.pts(m['total_points'])} pts", inline=True)
        await repondre(interaction, embed=e)

    @app_commands.command(name="profil", description="Le profil Arcanix d'un membre")
    @app_commands.describe(membre="Le membre à consulter (toi par défaut)")
    async def profil(self, interaction: discord.Interaction, membre: discord.Member | None = None):
        cible = membre or interaction.user
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m = await self.bot.api.membre(cible.id)
        except ApiError as e:
            if e.status == 404 and cible != interaction.user:
                return await repondre(interaction, embed=embeds.erreur(f"{cible.display_name} n'a pas lié son compte Arcanix."))
            raise
        role = "🛡️ Modération" if m["role_utilisateur"] != "user" else "Membre"
        e = embeds.embed(f"{m['prenom']} {m['nom'][:1]}.", f"{embeds.classe(m)} · {role}", thumbnail=False)
        e.set_thumbnail(url=cible.display_avatar.url)
        e.add_field(name=f"Semestre {embeds.semestre(m['semestre'])}",
                    value=f"**{embeds.pts(m['points'])} pts** · {embeds.texte_rang(m)}", inline=False)
        e.add_field(name="Présences", value=str(m["presences"]), inline=True)
        e.add_field(name="Total cumulé", value=f"{embeds.pts(m['total_points'])} pts", inline=True)
        await repondre(interaction, embed=e)

    @app_commands.command(name="classement", description="Le top 10 du semestre")
    @app_commands.describe(semestre="Semestre (en cours par défaut)")
    @app_commands.autocomplete(semestre=_semestre_autocomplete)
    async def classement(self, interaction: discord.Interaction, semestre: int | None = None):
        await interaction.response.defer(thinking=True)
        # Les deux appels en parallèle ; « ta position » est facultative
        c, moi = await asyncio.gather(self.bot.api.classement(semestre, limit=10),
                                      self.bot.api.membre(interaction.user.id), return_exceptions=True)
        if isinstance(c, BaseException):
            raise c
        if not c["lignes"]:
            return await repondre(interaction, embed=embeds.embed("🏆 Classement", "Aucune présence enregistrée pour l'instant."),
                                  ephemeral=False)
        lignes = [f"{embeds.rang(l['rang'])} **{l['prenom']} {l['nom']}** — {embeds.pts(l['points'])} pts" for l in c["lignes"]]
        e = embeds.embed(f"🏆 Classement · {embeds.semestre(c['semestre'])}", "\n".join(lignes))
        meme_semestre = c["semestre"] and isinstance(moi, dict) and moi["semestre"] and c["semestre"]["id"] == moi["semestre"]["id"]
        if meme_semestre and moi["rang"]:
            e.add_field(name="Ta position", value=f"#{moi['rang']} avec {embeds.pts(moi['points'])} pts", inline=False)
        await repondre(interaction, embed=e, view=embeds.bouton_lien("Classement complet", embeds.site_url("/classement"), "📜"),
                       ephemeral=False)

    @app_commands.command(name="seances", description="Les prochaines séances de l'association")
    async def seances(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        seances = await self.bot.api.seances_a_venir(limit=6)
        if not seances:
            return await repondre(interaction, embed=embeds.embed("📅 Prochaines séances", "Rien de prévu pour le moment, reste à l'affût !"))
        e = embeds.embed("📅 Prochaines séances")
        for s in seances:
            e.add_field(name=s["nom"], value=embeds.ligne_seance(s), inline=False)
        await repondre(interaction, embed=e, view=embeds.bouton_lien("Voir sur le site", embeds.site_url("/seances"), "🌐"))

    @app_commands.command(name="historique", description="Tes 10 dernières séances")
    async def historique(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        h = await self.bot.api.historique(interaction.user.id)
        if not h:
            return await repondre(interaction, embed=embeds.embed("📜 Historique", "Aucune participation pour l'instant."))
        lignes = [
            f"{'✅' if p['present'] else '❌'} **{p['seance_nom']}** · {embeds.date_longue(p['date_seance'])}"
            + (f" · +{embeds.pts(p['nb_point'])}" if p["present"] else " · absent")
            for p in h
        ]
        await repondre(interaction, embed=embeds.embed("📜 Tes dernières séances", "\n".join(lignes)))


async def setup(bot):
    await bot.add_cog(Membres(bot))
