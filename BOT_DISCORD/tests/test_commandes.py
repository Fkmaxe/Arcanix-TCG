"""Chaque commande du bot exécutée hors Discord, avec une fausse API."""
import discord
import pytest

from cogs.annonces import Annonces
from cogs.compte import Compte, InscriptionModal
from cogs.membres import Membres
from cogs.moderation import Moderation, PresenceView, SeanceModal
from tests.fakes import lancer, FakeApi, FakeBot, FakeInteraction, FakeMessage, FakeUser, remplir, run_async
from utils.api import ApiError

SEMESTRE = {"id": 2, "annee": 2026, "numero": 1, "actif": True}
MEMBRE = {"prenom": "Jules", "nom": "Fontaine", "classe": "3A", "role_utilisateur": "user", "semestre": SEMESTRE,
          "points": 7.5, "rang": 3, "presences": 4, "total_points": 12}
MODO = {**MEMBRE, "prenom": "Elise", "role_utilisateur": "moderator"}
SEANCE = {"id": 9, "nom": "Draft Magic", "date_seance": "2026-10-14", "heure_debut": "18:30:00", "lieu": "Foyer",
          "jeu": "magic", "description": None, "nb_point": 2.0, "nb_presents": 0, "semestre": SEMESTRE}
NON_LIE = ApiError(404, "Aucun compte Arcanix n'est lié à ce compte Discord")


# --- Compte ---------------------------------------------------------------------------------
@run_async
async def test_register_ouvre_le_formulaire():
    cog, inter = Compte(FakeBot(FakeApi())), FakeInteraction()
    await lancer(cog.register.callback(cog, inter), inter)
    assert isinstance(inter.response.modal, InscriptionModal)


@run_async
async def test_inscription_envoie_un_lien_prive():
    api = FakeApi(inscription={"url": "https://arcanix.example/activer?jeton=abc", "expire_dans_heures": 48})
    inter = FakeInteraction(FakeUser(id=42))
    modal = remplir(InscriptionModal(FakeBot(api)), prenom=" Jane ", nom="Doe", email="Jane@Ex.com ", classe="2B")
    await lancer(modal.on_submit(inter), inter)
    # adresse perso : membre externe, la classe saisie est ignorée
    assert api.appels_de("inscription") == [((42, "Jane", "Doe", "jane@ex.com", None, True), {})]
    msg = inter.dernier
    assert msg.ephemeral and "Bienvenue" in msg.texte and "48 h" in msg.texte
    assert msg.boutons[0].url == "https://arcanix.example/activer?jeton=abc"
    assert "default1234" not in msg.texte


@run_async
async def test_inscription_deja_faite():
    api = FakeApi(inscription=ApiError(409, "Ce compte Discord est déjà inscrit"))
    inter = FakeInteraction()
    await lancer(remplir(InscriptionModal(FakeBot(api)), prenom="a", nom="b", email="c@d.fr", classe="e").on_submit(inter), inter)
    assert "déjà inscrit" in inter.dernier.texte and inter.dernier.ephemeral


@run_async
async def test_lier_et_code_invalide():
    api = FakeApi(lier=MEMBRE)
    cog, inter = Compte(FakeBot(api)), FakeInteraction()
    await lancer(cog.lier.callback(cog, inter, code=" abc123 "), inter)
    assert api.appels_de("lier")[0][0] == (100, "abc123")
    assert "Jules Fontaine" in inter.dernier.texte and "7,5 pts" in inter.dernier.texte

    api.reponses["lier"] = ApiError(400, "Lien ou code invalide ou expiré")
    inter = FakeInteraction()
    await lancer(cog.lier.callback(cog, inter, code="zzz"), inter)
    assert "invalide ou expiré" in inter.dernier.texte


@run_async
async def test_reinitialiser_sans_compte():
    cog, inter = Compte(FakeBot(FakeApi(reinitialiser=NON_LIE))), FakeInteraction()
    await lancer(cog.reinitialiser.callback(cog, inter), inter)
    assert "/register" in inter.dernier.texte


@run_async
async def test_lien_http_local_affiche_en_clair_si_bouton_impossible():
    api = FakeApi(reinitialiser={"url": "localhost:3000/activer?jeton=x", "expire_dans_heures": 48})
    cog, inter = Compte(FakeBot(api)), FakeInteraction()
    await lancer(cog.reinitialiser.callback(cog, inter), inter)
    assert inter.dernier.view is None and "localhost:3000/activer" in inter.dernier.texte


# --- Membres --------------------------------------------------------------------------------
@run_async
async def test_points():
    for nom in ("points",):
        cog, inter = Membres(FakeBot(FakeApi(membre=MEMBRE))), FakeInteraction()
        await lancer(getattr(cog, nom).callback(cog, inter), inter)
        t = inter.dernier.texte
        assert "7,5 points" in t and "#3" in t and "12 pts" in t and inter.dernier.ephemeral


@run_async
async def test_points_sans_compte_lie():
    cog, inter = Membres(FakeBot(FakeApi(membre=NON_LIE))), FakeInteraction()
    await lancer(cog.points.callback(cog, inter), inter)
    assert "/register" in inter.dernier.texte and "/lier" in inter.dernier.texte


@run_async
async def test_api_injoignable():
    cog, inter = Membres(FakeBot(FakeApi(membre=ApiError(0, "Le site Arcanix est injoignable")))), FakeInteraction()
    await lancer(cog.points.callback(cog, inter), inter)
    assert "injoignable" in inter.dernier.texte


@run_async
async def test_profil_d_un_autre_membre():
    api = FakeApi(membre=MEMBRE)
    cog, inter = Membres(FakeBot(api)), FakeInteraction()
    await lancer(cog.profil.callback(cog, inter, membre=FakeUser(id=7, display_name="Jules")), inter)
    assert api.appels_de("membre")[0][0] == (7,)
    assert "Jules F." in inter.dernier.texte  # nom abrégé

    api.reponses["membre"] = NON_LIE
    inter = FakeInteraction()
    await lancer(cog.profil.callback(cog, inter, membre=FakeUser(id=7, display_name="Jules")), inter)
    assert "Jules n'a pas lié" in inter.dernier.texte


@run_async
async def test_classement_public_avec_ma_position():
    lignes = [{"rang": i, "prenom": f"P{i}", "nom": "X.", "points": 10 - i} for i in range(1, 5)]
    api = FakeApi(classement={"semestre": SEMESTRE, "lignes": lignes}, membre=MEMBRE)
    cog, inter = Membres(FakeBot(api)), FakeInteraction()
    await lancer(cog.classement.callback(cog, inter, semestre=None), inter)
    msg = inter.dernier
    assert not msg.ephemeral  # visible par tout le salon
    assert "🥇 **P1 X.** — 9 pts" in msg.texte and "`# 4`" in msg.texte
    assert "Ta position #3" in msg.texte


@run_async
async def test_classement_vide():
    cog, inter = Membres(FakeBot(FakeApi(classement={"semestre": SEMESTRE, "lignes": []}))), FakeInteraction()
    await lancer(cog.classement.callback(cog, inter, semestre=None), inter)
    assert "Aucune présence" in inter.dernier.texte


@run_async
async def test_autocomplete_semestres():
    api = FakeApi(semestres=[SEMESTRE, {"id": 1, "annee": 2025, "numero": 2, "actif": False}])
    cog = Membres(FakeBot(api))
    choix = await cog._semestre_autocomplete(FakeInteraction(), "2025")
    assert [c.value for c in choix] == [1]


@run_async
async def test_seances_et_historique():
    api = FakeApi(seances_a_venir=[SEANCE], historique=[
        {"seance_nom": "Draft Magic", "date_seance": "2026-10-14", "present": True, "nb_point": 2.0},
        {"seance_nom": "Tournoi", "date_seance": "2026-10-07", "present": False, "nb_point": 3.0},
    ])
    cog = Membres(FakeBot(api))
    inter = FakeInteraction()
    await lancer(cog.seances.callback(cog, inter), inter)
    assert "Draft Magic" in inter.dernier.texte and "18h30" in inter.dernier.texte and "Mercredi 14 octobre" in inter.dernier.texte
    inter = FakeInteraction()
    await lancer(cog.historique.callback(cog, inter), inter)
    assert "✅ **Draft Magic**" in inter.dernier.texte and "❌ **Tournoi**" in inter.dernier.texte and "absent" in inter.dernier.texte


@run_async
async def test_aucune_seance_a_venir():
    cog, inter = Membres(FakeBot(FakeApi(seances_a_venir=[]))), FakeInteraction()
    await lancer(cog.seances.callback(cog, inter), inter)
    assert "Rien de prévu" in inter.dernier.texte


# --- Modération -----------------------------------------------------------------------------
@run_async
async def test_mod_seance_formulaire_et_creation():
    api = FakeApi(creer_seance=SEANCE)
    cog, inter = Moderation(FakeBot(api)), FakeInteraction()
    jeu = discord.app_commands.Choice(name="Magic", value="magic")
    await lancer(cog.seance.callback(cog, inter, jeu=jeu), inter)
    modal = inter.response.modal
    assert isinstance(modal, SeanceModal) and modal.jeu == "magic"

    inter = FakeInteraction()
    await lancer(remplir(modal, nom="Draft Magic", jour="14/10/2026", heure="18h30", lieu="", points="2,5").on_submit(inter), inter)
    (args, kwargs), = api.appels_de("creer_seance")
    assert args == (100,) and kwargs == {"nom": "Draft Magic", "date_seance": "2026-10-14", "heure_debut": "18:30",
                                         "lieu": None, "jeu": "magic", "nb_point": 2.5}
    assert "Séance créée" in inter.dernier.texte


@run_async
async def test_mod_seance_saisie_invalide_ou_refusee():
    api = FakeApi(creer_seance=ApiError(403, "Commande réservée à la modération"))
    inter = FakeInteraction()
    await lancer(remplir(SeanceModal(FakeBot(api), None), nom="X", jour="32/13/2026", heure="", lieu="", points="1").on_submit(inter), inter)
    assert "invalides" in inter.dernier.texte and not api.appels
    inter = FakeInteraction()
    await lancer(remplir(SeanceModal(FakeBot(api), None), nom="X", jour="01/12/2026", heure="", lieu="", points="1").on_submit(inter), inter)
    assert "réservée à la modération" in inter.dernier.texte


@run_async
async def test_mod_presence_refusee_aux_membres():
    cog, inter = Moderation(FakeBot(FakeApi(membre=MEMBRE))), FakeInteraction()
    await lancer(cog.presence.callback(cog, inter, seance=9), inter)
    assert "réservée à la modération" in inter.dernier.texte


@run_async
async def test_mod_presence_parcours_complet():
    api = FakeApi(membre=MODO, seances_recherche=[SEANCE], seance=SEANCE, presences={
        "seance": {**SEANCE, "nb_presents": 2}, "ajoutes": ["7", "8"], "deja_presents": [], "non_lies": ["99"],
    })
    cog, inter = Moderation(FakeBot(api)), FakeInteraction()
    choix = await cog._seance_autocomplete(inter, "dra")
    assert choix[0].value == 9 and "Draft Magic" in choix[0].name
    await lancer(cog.presence.callback(cog, inter, seance=9), inter)
    view = inter.dernier.view
    assert isinstance(view, PresenceView) and "Appel · Draft Magic" in inter.dernier.texte

    # Un autre utilisateur ne peut pas manipuler l'appel
    assert await view.interaction_check(FakeInteraction(FakeUser(id=555))) is False

    # Valider sans sélection
    clic = FakeInteraction()
    await lancer(view.valider.callback(clic), clic)
    assert "au moins un membre" in clic.dernier.texte

    view.selection = [FakeUser(id=7), FakeUser(id=8), FakeUser(id=99)]
    clic = FakeInteraction()
    await lancer(view.valider.callback(clic), clic)
    assert api.appels_de("presences")[0][0] == (9, 100, [7, 8, 99])
    resultat = clic.dernier
    assert resultat.canal == "edition" and "<@7>, <@8>" in resultat.texte and "<@99>" in resultat.texte
    # Nouvelle vue vierge pour continuer l'appel (l'ancienne est arrêtée)
    assert isinstance(resultat.view, PresenceView) and resultat.view is not view and resultat.view.selection == []
    assert view.is_finished()


# --- Annonces --------------------------------------------------------------------------------
@run_async
async def test_boucle_d_annonces_publie_puis_acquitte():
    api = FakeApi(annonces_en_attente=[
        {"type": "nouvelle_seance", "id": 9, "seance": SEANCE},
        {"type": "rappel", "id": 9, "seance": SEANCE},
        {"type": "podium", "id": 1, "semestre": SEMESTRE, "podium": []},
    ])
    bot = FakeBot(api)
    cog = Annonces(bot)  # salon non configuré : la boucle ne démarre pas toute seule
    await cog.boucle.coro(cog)
    titres = [m.embed.title for m in bot.channel.messages]
    assert titres[0] == "🔥 Nouvelle séance : Draft Magic" and titres[1].startswith("⏰") and titres[2].startswith("🏆")
    assert api.appels_de("annonces_ack")[0][0][0] == [
        {"type": "nouvelle_seance", "id": 9}, {"type": "rappel", "id": 9}, {"type": "podium", "id": 1}]


@run_async
async def test_boucle_sans_annonce_ni_api():
    api = FakeApi(annonces_en_attente=[])
    bot = FakeBot(api)
    await Annonces(bot).boucle.coro(Annonces(bot))
    assert not bot.channel.messages and not api.appels_de("annonces_ack")
    api.reponses["annonces_en_attente"] = ApiError(0, "injoignable")
    await Annonces(bot).boucle.coro(Annonces(bot))  # ne lève pas
    assert not bot.channel.messages


# --- Boutons « Je viens » ------------------------------------------------------------------------
from cogs.annonces import construire  # noqa: E402
from cogs.inscriptions import BoutonInscription  # noqa: E402
from cogs.roles import synchroniser  # noqa: E402
from utils import embeds as emb  # noqa: E402


@run_async
async def test_bouton_je_viens_met_a_jour_l_annonce():
    seance = {**SEANCE, "places_max": 2, "nb_inscrits": 1}
    api = FakeApi(inscription_seance={"statut": "inscrit", "seance": {**seance, "nb_inscrits": 2}, "promus": []})
    bot = FakeBot(api)
    annonce = FakeMessage(emb.seance_embed(seance, "🔥 Nouvelle séance"))
    assert {f.name: f.value for f in annonce.embeds[0].fields}["👥 Inscrits"] == "1/2"

    inter = FakeInteraction(FakeUser(id=7), client=bot, message=annonce)
    await lancer(BoutonInscription("in", 9).callback(inter), inter)
    assert api.appels_de("inscription_seance")[0][0] == (9, 7, "in")
    assert "inscrit·e" in inter.dernier.texte and inter.dernier.ephemeral
    assert {f.name: f.value for f in annonce.embeds[0].fields}["👥 Inscrits"] == "2/2 · complet"


@run_async
async def test_bouton_liste_d_attente_puis_promotion_en_mp():
    api = FakeApi(inscription_seance={"statut": "attente", "seance": {**SEANCE, "places_max": 1, "nb_inscrits": 1, "nb_attente": 1}, "promus": []})
    bot = FakeBot(api)
    inter = FakeInteraction(client=bot, message=FakeMessage(emb.seance_embed(SEANCE, "x")))
    await lancer(BoutonInscription("in", 9).callback(inter), inter)
    assert "Liste d'attente" in inter.dernier.texte

    api.reponses["inscription_seance"] = {"statut": None, "seance": {**SEANCE, "places_max": 1, "nb_inscrits": 1}, "promus": ["55"]}
    inter = FakeInteraction(client=bot, message=FakeMessage(emb.seance_embed(SEANCE, "x")))
    await lancer(BoutonInscription("out", 9).callback(inter), inter)
    assert "Désinscription" in inter.dernier.texte
    assert "place s'est libérée" in bot.mp[55][0].title


@run_async
async def test_bouton_sans_compte_lie():
    bot = FakeBot(FakeApi(inscription_seance=NON_LIE))
    inter = FakeInteraction(client=bot, message=FakeMessage())
    await lancer(BoutonInscription("in", 9).callback(inter), inter)
    assert "/register" in inter.dernier.texte


@run_async
async def test_bouton_reconstruit_depuis_custom_id():
    import re
    m = re.fullmatch(BoutonInscription.__discord_ui_compiled_template__, "arcanix:inscr:out:42")
    b = await BoutonInscription.from_custom_id(None, None, m)
    assert (b.action, b.seance_id) == ("out", 42)


# --- /mod points --------------------------------------------------------------------------------
@run_async
async def test_mod_points_bonus_et_malus():
    api = FakeApi(ajustement={"points": -1.5, "prenom": "Jules", "nom": "F.", "motif": "Retard"})
    cog, inter = Moderation(FakeBot(api)), FakeInteraction()
    cible = FakeUser(id=7)
    cible.mention = "<@7>"
    await lancer(cog.points.callback(cog, inter, membre=cible, points=-1.5, motif=" Retard ", categorie=None), inter)
    assert api.appels_de("ajustement")[0][0] == (100, 7, -1.5, "Retard", "autre")
    assert "-1,5 pts" in inter.dernier.texte
    inter = FakeInteraction()
    await lancer(cog.points.callback(cog, inter, membre=cible, points=0, motif="rien", categorie=None), inter)
    assert "différents de 0" in inter.dernier.texte


# --- Annonce des résultats --------------------------------------------------------------------------
def test_annonce_resultats():
    import asyncio

    async def _run():
        return construire({"type": "resultats", "id": 9, "seance": SEANCE, "resultats": [
            {"place": 1, "prenom": "Zoé", "nom": "G.", "victoires": 4, "defaites": 0, "nuls": 1, "deck": "Dracaufeu", "bonus": 3},
            {"place": 2, "prenom": "Enzo", "nom": "M.", "bonus": 0},
        ]})
    e, view = asyncio.run(_run())
    assert e.title == "⚔️ Résultats · Draft Magic"
    assert "🥇 **Zoé G.** · 4-0-1 · _Dracaufeu_ · +3 pts" in e.description
    assert "🥈 **Enzo M.**" in e.description


# --- Rôles --------------------------------------------------------------------------------------------
class _Role:
    def __init__(self, rid):
        self.id, self.members = rid, []


class _Member:
    def __init__(self, uid):
        self.id, self.roles = uid, []

    async def add_roles(self, role, reason=None):
        self.roles.append(role)
        role.members.append(self)

    async def remove_roles(self, role, reason=None):
        self.roles.remove(role)
        role.members.remove(self)


class _Guild:
    def __init__(self, membres, roles):
        self._m = {m.id: m for m in membres}
        self._r = {r.id: r for r in roles}

    def get_member(self, uid):
        return self._m.get(uid)

    def get_role(self, rid):
        return self._r.get(rid)


@run_async
async def test_synchronisation_des_roles(monkeypatch):
    import config
    monkeypatch.setattr(config, "ROLE_MEMBRE_ID", 1)
    monkeypatch.setattr(config, "ROLE_TOP3_ID", 2)
    membre, top3 = _Role(1), _Role(2)
    a, b, c = _Member(10), _Member(11), _Member(12)
    await c.add_roles(top3)  # ancien top 3
    guild = _Guild([a, b, c], [membre, top3])
    bilan = await synchroniser(guild, {"membres": ["10", "11", "999"], "top3": ["11"]})
    assert bilan == {"membre_ajouts": 2, "top3_ajouts": 1, "top3_retraits": 1}
    assert membre in a.roles and membre in b.roles and top3 in b.roles and top3 not in c.roles
    # idempotent
    assert await synchroniser(guild, {"membres": ["10", "11"], "top3": ["11"]}) == {
        "membre_ajouts": 0, "top3_ajouts": 0, "top3_retraits": 0}


@run_async
async def test_role_membre_donne_a_l_inscription(monkeypatch):
    import discord
    import config
    from utils.roles import donner_role_membre
    monkeypatch.setattr(config, "ROLE_MEMBRE_ID", 1)
    role = _Role(1)
    m = _Member(10)
    monkeypatch.setattr(discord, "Member", _Member)  # isinstance(user, discord.Member)
    assert await donner_role_membre(m, _Guild([m], [role])) is True
    assert await donner_role_membre(m, _Guild([m], [role])) is False  # déjà attribué
    assert await donner_role_membre(m, None) is False


# --- Synchronisation des commandes -----------------------------------------------------------------
@run_async
async def test_sync_sur_le_serveur_supprime_les_commandes_globales(monkeypatch):
    """Régression : l'ancien /register global (4 champs) restait affiché à côté du formulaire."""
    import bot as botmod
    import config
    monkeypatch.setattr(config, "GUILD_ID", 42)
    b = botmod.ArcanixBot()
    for ext in botmod.EXTENSIONS:
        await b.load_extension(ext)
    appels = []

    async def faux_sync(*, guild=None):
        cmds = b.tree.get_commands(guild=guild)
        appels.append((guild.id if guild else None, sorted(c.name for c in cmds)))
        return cmds
    monkeypatch.setattr(b.tree, "sync", faux_sync)
    await b.synchroniser_commandes()

    (serveur, cmds_serveur), (global_, cmds_globales) = appels
    assert serveur == 42 and "register" in cmds_serveur and "mod" in cmds_serveur
    assert global_ is None and cmds_globales == []  # plus aucune commande globale
    register = b.tree.get_command("register", guild=discord.Object(id=42))
    assert register.parameters == []  # /register = formulaire uniquement, aucun champ à remplir avant



# --- Non-régression : le membre reçoit TOUJOURS une réponse ---------------------------------------------
from utils.embeds import adresse_publique  # noqa: E402


def test_adresse_publique():
    assert adresse_publique("https://arcanix.fr/activer?jeton=x")
    assert adresse_publique("http://tcg.esgi.fr")
    for url in ("http://localhost:3000/activer", "http://192.168.1.20:3000", "https://arcanix.local",
                "http://intranet", "ftp://arcanix.fr", "localhost:3000/x", ""):
        assert not adresse_publique(url), url


@run_async
async def test_register_avec_frontend_local_ne_bloque_pas():
    """Régression : FRONTEND_URL=localhost -> Discord refusait le bouton et le bot restait « réfléchit… »."""
    api = FakeApi(inscription={"url": "http://localhost:3000/activer?jeton=abc", "expire_dans_heures": 48})
    inter = FakeInteraction()
    modal = remplir(InscriptionModal(FakeBot(api)), prenom="Max", nom="G", email="m@g.fr", classe="5A")
    await lancer(modal.on_submit(inter), inter)
    msg = inter.dernier
    assert msg.view is None and "http://localhost:3000/activer?jeton=abc" in msg.texte and "Bienvenue" in msg.texte


@run_async
async def test_bouton_refuse_par_discord_lien_en_texte():
    api = FakeApi(reinitialiser={"url": "https://arcanix.example/activer?jeton=z", "expire_dans_heures": 48})
    cog, inter = Compte(FakeBot(api)), FakeInteraction()
    inter.refuser_liens = True
    await lancer(cog.reinitialiser.callback(cog, inter), inter)
    assert inter.dernier.view is None and "https://arcanix.example/activer?jeton=z" in inter.dernier.texte


@run_async
async def test_erreur_inattendue_dans_un_formulaire_est_signalee():
    def plante(*a, **k):
        raise RuntimeError("boum")
    inter = FakeInteraction()
    modal = remplir(InscriptionModal(FakeBot(FakeApi(inscription=plante))), prenom="a", nom="b", email="c@d.fr", classe="e")
    try:
        await modal.on_submit(inter)
    except RuntimeError as e:
        await modal.on_error(inter, e)  # ce que discord.py appelle en vrai
    assert "erreur inattendue" in inter.dernier.texte


@run_async
async def test_erreur_inattendue_dans_un_bouton_est_signalee():
    def plante(*a, **k):
        raise RuntimeError("boum")
    inter = FakeInteraction(client=FakeBot(FakeApi(inscription_seance=plante)), message=FakeMessage())
    await BoutonInscription("in", 9).callback(inter)  # sans lancer() : le bouton gère seul ses erreurs
    assert "erreur inattendue" in inter.dernier.texte


@run_async
async def test_mod_presence_seance_introuvable():
    from utils.api import ApiError as E
    cog, inter = Moderation(FakeBot(FakeApi(membre=MODO, seance=E(404, "Séance introuvable")))), FakeInteraction()
    await lancer(cog.presence.callback(cog, inter, seance=12345), inter)
    assert "choisis-la dans la liste" in inter.dernier.texte


@run_async
async def test_nettoyage_des_commandes_en_double_sur_les_autres_serveurs(monkeypatch):
    import bot as botmod
    import config
    from types import SimpleNamespace
    monkeypatch.setattr(config, "GUILD_ID", 1)
    b = botmod.ArcanixBot()
    serveurs = [SimpleNamespace(id=1, name="Asso"), SimpleNamespace(id=2, name="Ancien serveur de test")]
    monkeypatch.setattr(type(b), "guilds", property(lambda self: serveurs))
    restantes = {1: ["register", "points"], 2: ["register"]}
    nettoyes = []

    async def fetch(*, guild):
        return restantes[guild.id]

    async def sync(*, guild=None):
        nettoyes.append(guild.id)
        restantes[guild.id] = []
    monkeypatch.setattr(b.tree, "fetch_commands", fetch)
    monkeypatch.setattr(b.tree, "sync", sync)
    await b.nettoyer_commandes_serveurs()
    assert nettoyes == [2] and restantes == {1: ["register", "points"], 2: []}


def test_plus_de_commande_mypoint():
    import asyncio
    import bot as botmod

    async def _run():
        b = botmod.ArcanixBot()
        for ext in botmod.EXTENSIONS:
            await b.load_extension(ext)
        return sorted(c.name for c in b.tree.get_commands())
    noms = asyncio.run(_run())
    assert noms == ["classement", "historique", "lier", "mod", "points", "profil", "register", "reinitialiser", "seances"]



# --- Inscription interne / externe --------------------------------------------------------------------
from cogs.compte import analyser_inscription  # noqa: E402


@pytest.mark.parametrize("email,classe,attendu", [
    ("j.dupont", "3A", ("j.dupont@myskolae.fr", "3A", False)),          # identifiant seul -> interne
    (" J.Dupont@MySkolae.fr ", " 3A ", ("j.dupont@myskolae.fr", "3A", False)),
    ("fan.tcg@gmail.com", "3A", ("fan.tcg@gmail.com", None, True)),      # adresse perso -> externe
    ("fan.tcg@gmail.com", "", ("fan.tcg@gmail.com", None, True)),
])
def test_analyser_inscription(email, classe, attendu):
    assert analyser_inscription(email, classe, "myskolae.fr") == attendu


def test_analyser_inscription_interne_sans_classe():
    with pytest.raises(ValueError, match="classe"):
        analyser_inscription("j.dupont", "  ", "myskolae.fr")


@run_async
async def test_register_interne_identifiant_seul():
    api = FakeApi(inscription={"url": "https://arcanix.example/activer?jeton=a", "expire_dans_heures": 48})
    inter = FakeInteraction(FakeUser(id=5))
    await lancer(remplir(InscriptionModal(FakeBot(api)), prenom="Jean", nom="Dupont", email="j.dupont",
                         classe="3A-INFO").on_submit(inter), inter)
    assert api.appels_de("inscription")[0][0] == (5, "Jean", "Dupont", "j.dupont@myskolae.fr", "3A-INFO", False)


@run_async
async def test_register_interne_sans_classe_refuse_sans_appel_api():
    api = FakeApi()
    inter = FakeInteraction()
    await lancer(remplir(InscriptionModal(FakeBot(api)), prenom="Jean", nom="Dupont", email="j.dupont",
                         classe="").on_submit(inter), inter)
    assert "Indique ta classe" in inter.dernier.texte and not api.appels


@run_async
async def test_points_staff_hors_classement():
    cog, inter = Membres(FakeBot(FakeApi(membre={**MODO, "rang": None, "hors_classement": True}))), FakeInteraction()
    await lancer(cog.points.callback(cog, inter), inter)
    assert "Hors classement" in inter.dernier.texte


@run_async
async def test_profil_externe():
    m = {**MEMBRE, "classe": None, "externe": True}
    cog, inter = Membres(FakeBot(FakeApi(membre=m))), FakeInteraction()
    await lancer(cog.profil.callback(cog, inter, membre=None), inter)
    assert "Externe" in inter.dernier.texte
