"""Boutons « Je viens » / « Je ne viens plus » sous les annonces (persistants après redémarrage)."""
import logging

import discord
from discord.ext import commands

from utils import embeds
from utils.api import ApiError

log = logging.getLogger("arcanix.inscriptions")

LIBELLES = {
    "in": ("Je viens", discord.ButtonStyle.success, "✋"),
    "out": ("Je ne viens plus", discord.ButtonStyle.secondary, "↩️"),
}


class BoutonInscription(discord.ui.DynamicItem[discord.ui.Button], template=r"arcanix:inscr:(?P<action>in|out):(?P<sid>\d+)"):
    def __init__(self, action: str, seance_id: int):
        label, style, emoji = LIBELLES[action]
        super().__init__(discord.ui.Button(label=label, style=style, emoji=emoji,
                                           custom_id=f"arcanix:inscr:{action}:{seance_id}"))
        self.action = action
        self.seance_id = seance_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match):
        return cls(match["action"], int(match["sid"]))

    async def callback(self, interaction: discord.Interaction):
        api = interaction.client.api
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            r = await api.inscription_seance(self.seance_id, interaction.user.id, self.action)
        except ApiError as e:
            msg = ("Lie d'abord ton compte Arcanix : `/register` (nouveau) ou `/lier` (compte du site)."
                   if e.status == 404 and "lié" in e.message else e.message)
            return await interaction.followup.send(embed=embeds.erreur(msg), ephemeral=True)

        s = r["seance"]
        if r["statut"] == "inscrit":
            msg = embeds.succes(f"C'est noté, tu es inscrit·e à **{s['nom']}** ! À bientôt 🔥")
        elif r["statut"] == "attente":
            msg = embeds.embed("⏳ Liste d'attente",
                               f"**{s['nom']}** est complet. Tu es en liste d'attente : "
                               "tu seras prévenu·e si une place se libère.", embeds.OR, thumbnail=False)
        else:
            msg = embeds.succes(f"Désinscription prise en compte pour **{s['nom']}**.")
        await interaction.followup.send(embed=msg, ephemeral=True)

        # Compteur à jour dans l'annonce
        if interaction.message and interaction.message.embeds:
            try:
                await interaction.message.edit(embed=embeds.maj_inscrits(interaction.message.embeds[0], s))
            except discord.HTTPException as e:
                log.warning("Mise à jour de l'annonce impossible : %s", e)

        # Prévenir en MP les membres sortis de la liste d'attente
        for did in r.get("promus", []):
            try:
                user = await interaction.client.fetch_user(int(did))
                await user.send(embed=embeds.embed(
                    "🎉 Une place s'est libérée !",
                    f"Tu passes de la liste d'attente aux inscrits pour **{s['nom']}** "
                    f"({embeds.date_longue(s['date_seance'])}). Si tu ne peux plus venir, désinscris-toi.",
                    embeds.SUCCES))
            except discord.HTTPException:
                pass  # MP fermés : l'email (si SMTP) prend le relais


def vue_inscription(s: dict) -> discord.ui.View:
    """Boutons d'inscription + lien vers la séance, à joindre aux annonces."""
    v = discord.ui.View(timeout=None)
    v.add_item(BoutonInscription("in", s["id"]))
    v.add_item(BoutonInscription("out", s["id"]))
    url = embeds.site_url(f"/seances/{s['id']}")
    if embeds.lien_valide(url):
        v.add_item(discord.ui.Button(label="Détails", url=url, emoji="🌐"))
    return v


async def setup(bot: commands.Bot):
    bot.add_dynamic_items(BoutonInscription)
