"""Annonces automatiques : nouvelles séances, rappels la veille, podium de fin de semestre."""
import logging

import discord
from discord.ext import commands, tasks

import config
from utils import embeds
from utils.api import ApiError

from .inscriptions import vue_inscription

log = logging.getLogger("arcanix.annonces")


def construire(a: dict) -> tuple[discord.Embed, discord.ui.View | None]:
    if a["type"] == "resultats":
        s = a["seance"]
        lignes = []
        for r in a["resultats"]:
            bilan = "-".join(str(x) for x in (r.get("victoires"), r.get("defaites"), r.get("nuls")) if x is not None)
            ligne = f"{embeds.rang(r['place'])} **{r['prenom']} {r['nom']}**"
            if bilan:
                ligne += f" · {bilan}"
            if r.get("deck"):
                ligne += f" · _{r['deck']}_"
            if r.get("bonus"):
                ligne += f" · +{embeds.pts(r['bonus'])} pts"
            lignes.append(ligne)
        e = embeds.embed(f"⚔️ Résultats · {s['nom']}", "\n".join(lignes) or "Aucun résultat.", embeds.OR)
        e.set_footer(text=f"{embeds.date_longue(s['date_seance']).capitalize()} · Arcanix")
        return e, embeds.bouton_lien("Classement complet", embeds.site_url(f"/seances/{s['id']}"), "📜")
    if a["type"] == "podium":
        sem = a["semestre"]
        lignes = [f"{embeds.rang(l['rang'])} **{l['prenom']} {l['nom']}** — {embeds.pts(l['points'])} pts" for l in a["podium"]]
        e = embeds.embed(
            f"🏆 Podium du semestre {embeds.semestre(sem)}",
            ("\n".join(lignes) + "\n\nBravo aux champions ! Un nouveau semestre commence : tout le monde repart de zéro. 🔥")
            if lignes else "Aucune présence enregistrée ce semestre.",
            embeds.OR,
        )
        return e, embeds.bouton_lien("Voir le classement", embeds.site_url("/classement"), "📜")
    s = a["seance"]
    if a["type"] == "rappel":
        e = embeds.seance_embed(s, f"⏰ C'est demain : {s['nom']}", embeds.OR)
    else:
        e = embeds.seance_embed(s, f"🔥 Nouvelle séance : {s['nom']}", embeds.BRAISE)
    return e, vue_inscription(s)


class Annonces(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if config.ANNONCES_CHANNEL_ID:
            self.boucle.change_interval(minutes=config.ANNONCES_INTERVALLE_MIN)
            self.boucle.start()
        else:
            log.info("DISCORD_ANNONCES_CHANNEL_ID non défini : annonces automatiques désactivées")

    def cog_unload(self):
        self.boucle.cancel()

    @tasks.loop(minutes=5)
    async def boucle(self):
        channel = self.bot.get_channel(config.ANNONCES_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(config.ANNONCES_CHANNEL_ID)
            except discord.DiscordException as e:
                log.error("Salon d'annonces inaccessible (%s) : %s", config.ANNONCES_CHANNEL_ID, e)
                return
        try:
            annonces = await self.bot.api.annonces_en_attente()
        except ApiError as e:
            log.warning("Récupération des annonces impossible : %s", e.message)
            return
        faites = []
        mention = f"<@&{config.ANNONCES_ROLE_ID}>" if config.ANNONCES_ROLE_ID else None
        for a in annonces:
            e, view = construire(a)
            try:
                await channel.send(
                    content=mention if a["type"] != "rappel" else None,
                    embed=e,
                    view=view or discord.utils.MISSING,
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )
                faites.append({"type": a["type"], "id": a["id"]})
            except discord.DiscordException as err:
                log.error("Envoi de l'annonce %s/%s échoué : %s", a["type"], a["id"], err)
        if faites:
            try:
                await self.bot.api.annonces_ack(faites)
                log.info("%d annonce(s) publiée(s)", len(faites))
            except ApiError as err:
                log.error("Acquittement des annonces échoué : %s", err.message)

    @boucle.before_loop
    async def avant(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Annonces(bot))
