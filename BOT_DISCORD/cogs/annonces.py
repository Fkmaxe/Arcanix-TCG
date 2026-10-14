"""Publications automatiques : séances et rappels dans le salon des annonces, résultats et podium dans celui des points."""
import logging

import discord
from discord.ext import commands, tasks

import config
from utils import embeds
from utils.api import ApiError

from .inscriptions import vue_inscription

log = logging.getLogger("arcanix.annonces")


def salon_de(type_annonce: str) -> int | None:
    """Salon où publier ce type d'annonce."""
    return config.POINTS_CHANNEL_ID if type_annonce in ("resultats", "podium") else config.ANNONCES_CHANNEL_ID


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
        if config.ANNONCES_CHANNEL_ID or config.POINTS_CHANNEL_ID:
            self.boucle.change_interval(minutes=config.ANNONCES_INTERVALLE_MIN)
            self.boucle.start()
        else:
            log.info("DISCORD_ANNONCES_CHANNEL_ID et DISCORD_POINTS_CHANNEL_ID non définis : annonces automatiques désactivées")

    def cog_unload(self):
        self.boucle.cancel()

    @tasks.loop(minutes=5)
    async def boucle(self):
        try:
            annonces = await self.bot.api.annonces_en_attente()
        except ApiError as e:
            log.warning("Récupération des annonces impossible : %s", e.message)
            return
        faites = []
        mention = f"<@&{config.ANNONCES_ROLE_ID}>" if config.ANNONCES_ROLE_ID else None
        salons: dict[int, discord.abc.Messageable | None] = {}
        for a in annonces:
            channel_id = salon_de(a["type"])
            if not channel_id:
                continue  # salon non configuré : l'annonce attend qu'il le soit
            if channel_id not in salons:
                salons[channel_id] = await self._salon(channel_id)
            channel = salons[channel_id]
            if channel is None:
                continue
            e, view = construire(a)
            contenu = mention if a["type"] != "rappel" else None
            try:
                await self._publier(channel, contenu, e, view)
                faites.append({"type": a["type"], "id": a["id"]})
            except discord.DiscordException as err:
                log.error("Envoi de l'annonce %s/%s échoué : %s", a["type"], a["id"], err)
        if faites:
            try:
                await self.bot.api.annonces_ack(faites)
                log.info("%d annonce(s) publiée(s)", len(faites))
            except ApiError as err:
                log.error("Acquittement des annonces échoué : %s", err.message)

    async def _salon(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except discord.DiscordException as e:
                log.error("Salon %s inaccessible : %s", channel_id, e)
        return channel

    @staticmethod
    async def _publier(channel, contenu, e: discord.Embed, view: discord.ui.View | None):
        mentions = discord.AllowedMentions(roles=True)
        try:
            await channel.send(content=contenu, embed=e, view=view or discord.utils.MISSING, allowed_mentions=mentions)
        except discord.HTTPException as err:
            if view is None or err.status != 400:
                raise
            # Bouton refusé par Discord : on publie quand même l'annonce, sans les boutons
            log.warning("Annonce publiée sans boutons (refusés par Discord : %s)", err.text or err)
            await channel.send(content=contenu, embed=e, allowed_mentions=mentions)

    @boucle.before_loop
    async def avant(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Annonces(bot))
