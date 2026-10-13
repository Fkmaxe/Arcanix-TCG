"""Scénario complet du bot contre une VRAIE API, sans Discord.

Prérequis : API démarrée sur une base remplie par `python -m scripts.seed_demo` (admin lié au Discord 100).
    ARCANIX_E2E_API=http://localhost:8000 ARCANIX_E2E_BOT_TOKEN=<DISCORD_BOT_TOKEN> python -m pytest tests/test_e2e.py -v
"""
import os
import random
from datetime import date, timedelta

import aiohttp
import pytest

import config
from cogs.annonces import Annonces
from cogs.compte import Compte, InscriptionModal
from cogs.inscriptions import BoutonInscription
from utils import embeds
from cogs.membres import Membres
from cogs.moderation import Moderation, PresenceView, SeanceModal
from tests.fakes import FakeBot, FakeInteraction, FakeMessage, FakeUser, remplir, run_async
from utils.api import ApiClient

API = os.getenv("ARCANIX_E2E_API")
pytestmark = pytest.mark.skipif(not API, reason="ARCANIX_E2E_API non défini (test de bout en bout)")

ADMIN_DISCORD = 100  # compte admin du jeu de démo


async def _bot() -> FakeBot:
    config.API_BASE_URL = API.rstrip("/")
    config.API_BOT_TOKEN = os.getenv("ARCANIX_E2E_BOT_TOKEN", "bot-dev")
    api = ApiClient()
    await api.start()
    return FakeBot(api)


async def _http(method: str, path: str, token: str | None = None, **kw):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with aiohttp.ClientSession() as s:
        async with s.request(method, API.rstrip("/") + path, headers=headers, **kw) as r:
            return r.status, (await r.json() if r.content_type == "application/json" else None)


@run_async
async def test_parcours_complet_du_bot():
    bot = await _bot()
    try:
        nouveau = FakeUser(id=random.randint(10**17, 10**18), display_name="Nouveau")
        email = f"e2e.{nouveau.id}@exemple.fr"

        # 1. /register -> formulaire -> lien privé
        compte = Compte(bot)
        inter = FakeInteraction(nouveau)
        await compte.register.callback(compte, inter)
        await remplir(inter.response.modal, prenom="Alex", nom="Testeur", email=email, classe="1A").on_submit(inter)
        lien = inter.dernier.boutons[0].url
        assert "/activer?jeton=" in lien, inter.dernier.texte

        # 2. Le lien permet de choisir un mot de passe puis de se connecter sur le site
        jeton = lien.split("jeton=")[1]
        status, _ = await _http("POST", "/auth/definir-mot-de-passe", json={"jeton": jeton, "mot_de_passe": "mot-de-passe-e2e"})
        assert status == 200
        status, tok = await _http("POST", "/auth/login", json={"email": email, "password": "mot-de-passe-e2e"})
        assert status == 200

        # 3. /points : 0 point au départ
        membres = Membres(bot)
        inter = FakeInteraction(nouveau)
        await membres.points.callback(membres, inter)
        assert "0 points" in inter.dernier.texte

        # 4. /mod seance (admin du jeu de démo) pour demain
        admin = FakeUser(id=ADMIN_DISCORD)
        mod = Moderation(bot)
        demain = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        inter = FakeInteraction(admin)
        await remplir(SeanceModal(bot, "pokemon"), nom=f"E2E {nouveau.id}", jour=demain, heure="19h", lieu="Foyer",
                      points="2,5").on_submit(inter)
        assert "Séance créée" in inter.dernier.texte, inter.dernier.texte

        # 5. /mod presence : l'autocomplétion trouve la séance, on valide le nouveau membre
        choix = await mod._seance_autocomplete(FakeInteraction(admin), f"E2E {nouveau.id}")
        assert len(choix) == 1
        inter = FakeInteraction(admin)
        await mod.presence.callback(mod, inter, seance=choix[0].value)
        view = inter.dernier.view
        assert isinstance(view, PresenceView)
        view.selection = [nouveau, FakeUser(id=123)]  # 123 : aucun compte lié
        clic = FakeInteraction(admin)
        await view.valider.callback(clic)
        assert f"<@{nouveau.id}>" in clic.dernier.texte and "<@123>" in clic.dernier.texte

        # 6. Les points sont crédités
        inter = FakeInteraction(nouveau)
        await membres.points.callback(membres, inter)
        assert "2,5 points" in inter.dernier.texte, inter.dernier.texte

        # 7. Un membre refuse l'accès à /mod presence
        inter = FakeInteraction(nouveau)
        await mod.presence.callback(mod, inter, seance=choix[0].value)
        assert "réservée à la modération" in inter.dernier.texte

        # 8. Annonces : la nouvelle séance est publiée une seule fois
        annonces = Annonces(bot)
        await annonces.boucle.coro(annonces)
        titres = [m.embed.title for m in bot.channel.messages]
        assert f"🔥 Nouvelle séance : E2E {nouveau.id}" in titres
        avant = len(bot.channel.messages)
        await annonces.boucle.coro(annonces)
        assert len(bot.channel.messages) == avant

        # 9. /lier : un compte créé sur le site se lie avec le code du profil
        status, tok_membre = await _http("POST", "/auth/login", json={"email": "membre@arcanix.fr", "password": "arcanix123"})
        assert status == 200
        status, code = await _http("POST", "/me/code-discord", token=tok_membre["access_token"])
        lie = FakeUser(id=random.randint(10**17, 10**18))
        inter = FakeInteraction(lie)
        await compte.lier.callback(compte, inter, code=code["code"].lower())
        assert "Compte lié" in inter.dernier.texte, inter.dernier.texte

        # 9b. Bouton « Je viens » sous l'annonce : inscription puis désinscription, compteur à jour
        sid = choix[0].value
        annonce = FakeMessage(bot.channel.messages[0].embed if bot.channel.messages else embeds.embed("x"))
        inter = FakeInteraction(nouveau, client=bot, message=annonce)
        await BoutonInscription("in", sid).callback(inter)
        assert "inscrit·e" in inter.dernier.texte, inter.dernier.texte
        assert any(f.name == "👥 Inscrits" and f.value.startswith("1") for f in annonce.embeds[0].fields)
        inter = FakeInteraction(nouveau, client=bot, message=annonce)
        await BoutonInscription("out", sid).callback(inter)
        assert "Désinscription" in inter.dernier.texte

        # 9c. /mod points : bonus par l'admin, visible dans /points
        cible = FakeUser(id=nouveau.id)
        cible.mention = f"<@{nouveau.id}>"
        inter = FakeInteraction(admin)
        await mod.points.callback(mod, inter, membre=cible, points=1.5, motif="Aide au rangement", categorie=None)
        assert "+1,5 pts" in inter.dernier.texte, inter.dernier.texte
        inter = FakeInteraction(nouveau)
        await membres.points.callback(membres, inter)
        assert "4 points" in inter.dernier.texte, inter.dernier.texte  # 2,5 (présence) + 1,5 (bonus)

        # 9d. Rôles : le nouveau membre est lié
        roles = await bot.api.roles()
        assert str(nouveau.id) in roles["membres"] and len(roles["top3"]) <= 3

        # 10. /reinitialiser, /classement, /profil, /historique, /seances
        for cmd, cible in ((compte.reinitialiser, compte), (membres.historique, membres), (membres.seances, membres)):
            inter = FakeInteraction(nouveau)
            await cmd.callback(cible, inter)
            assert "❌" not in inter.dernier.texte, inter.dernier.texte
        inter = FakeInteraction(nouveau)
        await membres.classement.callback(membres, inter, semestre=None)
        assert "Classement" in inter.dernier.texte and "Ta position" in inter.dernier.texte
        inter = FakeInteraction(nouveau)
        await membres.profil.callback(membres, inter, membre=None)
        assert "Alex T." in inter.dernier.texte
    finally:
        await bot.api.close()
