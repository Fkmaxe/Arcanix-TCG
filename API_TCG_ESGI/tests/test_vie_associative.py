"""Inscriptions, pointage QR, bonus/malus, résultats de tournoi, journal, emails."""
from datetime import date, timedelta

import pytest

from app import config, mail, vie
from tests.conftest import BOT, auth


@pytest.fixture
def emails(monkeypatch):
    """Active un faux SMTP et capture les emails envoyés."""
    envoyes = []
    monkeypatch.setattr(config, "SMTP_ACTIF", True)
    monkeypatch.setattr(mail, "envoyer", lambda dest, sujet, *a, **k: envoyes.append({"to": dest, "sujet": sujet, "args": a, "kw": k}))
    return envoyes


def _semestre(client, admin):
    return client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()


def _seance(client, staff, sem_id, jours=3, **extra):
    body = {"nom": "Tournoi", "date_seance": (date.today() + timedelta(days=jours)).isoformat(), "nb_point": 2,
            "semestre_id": sem_id, **extra}
    r = client.post("/seances", json=body, headers=auth(staff))
    assert r.status_code == 201, r.text
    return r.json()


# --- Inscriptions ---------------------------------------------------------------------------------
def test_inscriptions_liste_d_attente_et_promotion(client, make_user, emails):
    admin = make_user("admin")
    a, b, c = make_user(prenom="A"), make_user(prenom="B"), make_user(prenom="C")
    s = _seance(client, admin, _semestre(client, admin)["id"], places_max=2)

    assert client.post(f"/seances/{s['id']}/inscription", headers=auth(a)).json()["statut"] == "inscrit"
    assert client.post(f"/seances/{s['id']}/inscription", headers=auth(b)).json()["statut"] == "inscrit"
    r = client.post(f"/seances/{s['id']}/inscription", headers=auth(c)).json()
    assert r["statut"] == "attente" and r["seance"]["nb_inscrits"] == 2 and r["seance"]["nb_attente"] == 1
    # idempotent
    assert client.post(f"/seances/{s['id']}/inscription", headers=auth(c)).json()["statut"] == "attente"

    # A se désiste : C est promu et prévenu par email
    r = client.delete(f"/seances/{s['id']}/inscription", headers=auth(a)).json()
    assert r["statut"] is None
    vue_c = client.get(f"/seances/{s['id']}", headers=auth(c)).json()
    assert vue_c["mon_inscription"] == "inscrit"
    assert [e["to"] for e in emails] == [c.adresse_mail] and "place s'est libérée" in emails[0]["sujet"]

    # La modération voit les inscrits ; la liste publique montre ma place
    detail = client.get(f"/seances/{s['id']}", headers=auth(admin)).json()
    assert {i["utilisateur_id"] for i in detail["inscrits"]} == {b.id, c.id}
    liste = client.get("/seances?a_venir=true", headers=auth(b)).json()
    assert liste[0]["mon_inscription"] == "inscrit" and liste[0]["places_max"] == 2


def test_agrandir_la_salle_promeut_la_liste_d_attente(client, make_user):
    admin, a, b = make_user("admin"), make_user(), make_user()
    s = _seance(client, admin, _semestre(client, admin)["id"], places_max=1)
    client.post(f"/seances/{s['id']}/inscription", headers=auth(a))
    client.post(f"/seances/{s['id']}/inscription", headers=auth(b))
    r = client.patch(f"/seances/{s['id']}", json={"places_max": 5}, headers=auth(admin)).json()
    assert r["nb_inscrits"] == 2 and r["nb_attente"] == 0


def test_inscription_a_une_seance_passee_refusee(client, make_user):
    admin, a = make_user("admin"), make_user()
    s = _seance(client, admin, _semestre(client, admin)["id"], jours=-2)
    assert client.post(f"/seances/{s['id']}/inscription", headers=auth(a)).status_code == 409


# --- Pointage QR -------------------------------------------------------------------------------------
def test_pointage_qr_puis_validation_par_la_moderation(client, make_user):
    admin, membre = make_user("admin"), make_user()
    s = _seance(client, admin, _semestre(client, admin)["id"], jours=0)
    sid = s["id"]
    assert client.post(f"/seances/{sid}/pointer", json={"code": "12345678"}, headers=auth(membre)).status_code == 409

    info = client.post(f"/seances/{sid}/pointage/ouvrir", headers=auth(admin)).json()
    assert info["ouvert"] and len(info["code"]) == 8 and info["url"].endswith(f"/pointer/{sid}?c={info['code']}")
    assert client.get(f"/seances/{sid}/pointage", headers=auth(membre)).status_code == 403  # code réservé à la modération

    assert client.post(f"/seances/{sid}/pointer", json={"code": "00000000"}, headers=auth(membre)).status_code == 400
    r = client.post(f"/seances/{sid}/pointer", json={"code": info["code"]}, headers=auth(membre)).json()
    assert r["resultat"] == "pointe"
    assert client.post(f"/seances/{sid}/pointer", json={"code": info["code"]}, headers=auth(membre)).json()["resultat"] == "deja_pointe"

    # Pas de points tant que la modération n'a pas validé
    assert client.get("/me/points", headers=auth(membre)).json()["total"] == 0
    detail = client.get(f"/seances/{sid}", headers=auth(admin)).json()
    assert [p["utilisateur_id"] for p in detail["pointages"]] == [membre.id] and detail["pointage_ouvert"]

    client.put(f"/seances/{sid}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": membre.id, "present": True}]})
    assert client.get("/me/points", headers=auth(membre)).json()["total"] == 2
    assert client.post(f"/seances/{sid}/pointer", json={"code": vie.code_courant(_seance_obj(sid))[0]},
                       headers=auth(membre)).json()["resultat"] == "deja_valide"

    assert client.post(f"/seances/{sid}/pointage/fermer", headers=auth(admin)).json()["ouvert"] is False


def _seance_obj(sid):
    from app.database import SessionLocal
    from app.models import Seance
    with SessionLocal() as db:
        return db.get(Seance, sid)


def test_code_qr_change_et_tolere_la_periode_precedente(client, make_user, monkeypatch):
    admin = make_user("admin")
    sid = _seance(client, admin, _semestre(client, admin)["id"], jours=0)["id"]
    code = client.post(f"/seances/{sid}/pointage/ouvrir", headers=auth(admin)).json()["code"]
    s = _seance_obj(sid)
    f = vie.fenetre_courante()
    monkeypatch.setattr(vie, "fenetre_courante", lambda: f + 1)
    assert vie.code_valide(s, code)  # scanné juste avant le changement
    monkeypatch.setattr(vie, "fenetre_courante", lambda: f + 2)
    assert not vie.code_valide(s, code)  # trop vieux


# --- Bonus / malus ------------------------------------------------------------------------------------
def test_bonus_malus_dans_le_classement_et_le_profil(client, make_user):
    mod, a, b = make_user("moderator"), make_user(prenom="Ana"), make_user(prenom="Bob")
    admin = make_user("admin")
    sem = _semestre(client, admin)
    s = _seance(client, admin, sem["id"], jours=-1)
    client.put(f"/seances/{s['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": a.id}, {"utilisateur_id": b.id}]})

    r = client.post("/ajustements", headers=auth(mod), json={
        "utilisateur_id": b.id, "points": 3, "motif": "Aide à l'organisation", "categorie": "organisation"})
    assert r.status_code == 201 and r.json()["cree_par"].startswith("Test")
    client.post("/ajustements", headers=auth(mod), json={
        "utilisateur_id": a.id, "points": -0.5, "motif": "Retard", "categorie": "penalite"})
    assert client.post("/ajustements", headers=auth(mod), json={
        "utilisateur_id": a.id, "points": 0, "motif": "rien"}).status_code == 422
    assert client.post("/ajustements", headers=auth(a), json={
        "utilisateur_id": a.id, "points": 5, "motif": "triche"}).status_code == 403

    cl = client.get("/stats/classement", headers=auth(a)).json()["lignes"]
    assert [(l["prenom"], l["points"], l["bonus"]) for l in cl] == [("Bob", 5.0, 3.0), ("Ana", 1.5, -0.5)]
    stats = client.get("/me/stats", headers=auth(b)).json()
    assert stats["points"] == 5 and stats["evolution"][-1]["type"] == "ajustement"
    assert [x["motif"] for x in client.get("/me/ajustements", headers=auth(b)).json()] == ["Aide à l'organisation"]
    assert client.get("/me/points", headers=auth(a)).json()["total"] == 1.5

    aid = client.get(f"/ajustements?userId={b.id}", headers=auth(mod)).json()[0]["id"]
    assert client.delete(f"/ajustements/{aid}", headers=auth(mod)).status_code == 204
    assert client.get("/me/points", headers=auth(b)).json()["total"] == 2
    # un semestre avec des ajustements ne peut pas être supprimé
    assert client.delete(f"/semestres/{sem['id']}", headers=auth(admin)).status_code == 409


# --- Résultats de tournoi -----------------------------------------------------------------------------
def test_resultats_de_tournoi_generent_les_bonus(client, make_user):
    admin = make_user("admin")
    a, b, c = make_user(prenom="A"), make_user(prenom="B"), make_user(prenom="C")
    s = _seance(client, admin, _semestre(client, admin)["id"], jours=-1)
    r = client.put(f"/seances/{s['id']}/resultats", headers=auth(admin), json={
        "bareme": [5, 3, 1],
        "resultats": [
            {"utilisateur_id": b.id, "place": 1, "victoires": 4, "defaites": 0, "deck": "Dracaufeu ex"},
            {"utilisateur_id": a.id, "place": 2, "victoires": 3, "defaites": 1},
            {"utilisateur_id": c.id, "place": 4},
        ]})
    assert r.status_code == 200, r.text
    assert [(x["prenom"], x["place"], x["bonus"]) for x in r.json()] == [("B", 1, 5), ("A", 2, 3), ("C", 4, 0)]

    pub = client.get(f"/seances/{s['id']}/resultats", headers=auth(c)).json()
    assert pub[0]["nom"].endswith(".") and pub[2]["moi"] is True
    assert client.get("/me/points", headers=auth(b)).json()["total"] == 5

    # bonus de tournoi non supprimable directement
    aid = client.get(f"/ajustements?userId={b.id}", headers=auth(admin)).json()[0]["id"]
    assert client.delete(f"/ajustements/{aid}", headers=auth(admin)).status_code == 409

    # Correction des résultats : les bonus sont recalculés
    client.put(f"/seances/{s['id']}/resultats", headers=auth(admin), json={
        "bareme": [5, 3, 1], "resultats": [{"utilisateur_id": a.id, "place": 1}, {"utilisateur_id": b.id, "place": 2}]})
    assert client.get("/me/points", headers=auth(b)).json()["total"] == 3
    assert client.get("/me/points", headers=auth(a)).json()["total"] == 5

    annonces = client.get("/discord/annonces/en-attente", headers=BOT).json()
    res = next(x for x in annonces if x["type"] == "resultats")
    assert res["resultats"][0]["prenom"] == "A"
    client.post("/discord/annonces/ack", headers=BOT, json=[{"type": "resultats", "id": s["id"]}])
    assert not [x for x in client.get("/discord/annonces/en-attente", headers=BOT).json() if x["type"] == "resultats"]

    doublon = client.put(f"/seances/{s['id']}/resultats", headers=auth(admin), json={
        "resultats": [{"utilisateur_id": a.id, "place": 1}, {"utilisateur_id": a.id, "place": 2}]})
    assert doublon.status_code == 422


# --- Journal -------------------------------------------------------------------------------------------
def test_journal_trace_qui_a_fait_quoi(client, make_user):
    admin = make_user("admin", prenom="Ada", nom="Admin")
    membre = make_user(prenom="Max")
    s = _seance(client, admin, _semestre(client, admin)["id"], jours=-1)
    client.put(f"/seances/{s['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": membre.id, "present": True}]})
    client.put(f"/seances/{s['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": membre.id, "present": False}]})
    client.post("/ajustements", headers=auth(admin), json={"utilisateur_id": membre.id, "points": 1, "motif": "Rangement"})
    client.patch(f"/users/{membre.id}", headers=auth(admin), json={"role_utilisateur": "moderator"})

    j = client.get(f"/journal?membreId={membre.id}", headers=auth(admin))
    assert j.status_code == 200 and j.headers["X-Total-Count"] == "4"
    actions = [e["action"] for e in j.json()]
    assert actions == ["membre.role", "points.ajustement", "presence.modification", "presence.ajout"]
    assert all(e["auteur_nom"] == "Ada Admin" for e in j.json())
    assert "absent" in j.json()[2]["resume"]
    assert client.get("/journal?action=presence", headers=auth(admin)).headers["X-Total-Count"] == "2"
    assert client.get("/journal", headers=auth(make_user())).status_code == 403


# --- Emails ------------------------------------------------------------------------------------------------
def test_mot_de_passe_oublie(client, make_user, emails):
    u = make_user(email="oubli@ex.com")
    r = client.post("/auth/mot-de-passe-oublie", json={"email": "OUBLI@ex.com"})
    assert r.status_code == 202
    assert client.post("/auth/mot-de-passe-oublie", json={"email": "inconnu@ex.com"}).status_code == 202  # pas d'énumération
    assert len(emails) == 1 and emails[0]["to"] == u.adresse_mail
    lien = emails[0]["kw"]["bouton"][1] if "bouton" in emails[0]["kw"] else emails[0]["args"][2][1]
    jeton = lien.split("jeton=")[1]
    assert client.post("/auth/definir-mot-de-passe", json={"jeton": jeton, "mot_de_passe": "nouveau-mdp"}).status_code == 200
    assert client.post("/auth/login", json={"email": "oubli@ex.com", "password": "nouveau-mdp"}).status_code == 200


def test_sans_smtp(client, make_user):
    assert config.SMTP_ACTIF is False
    assert client.get("/config").json() == {"smtp": False, "qr_periode_s": 30}
    assert client.post("/auth/mot-de-passe-oublie", json={"email": "x@ex.com"}).status_code == 503
    admin = make_user("admin")
    r = client.post("/users", headers=auth(admin), json={"nom": "N", "prenom": "P", "adresse_mail": "n@ex.com",
                                                         "classe": "1A", "envoyer_invitation": True})
    assert r.status_code == 409


def test_invitation_par_email(client, make_user, emails):
    admin = make_user("admin", prenom="Ada", nom="Admin")
    r = client.post("/users", headers=auth(admin), json={"nom": "Neuf", "prenom": "Nina", "adresse_mail": "nina@ex.com",
                                                         "classe": "1A", "envoyer_invitation": True})
    assert r.status_code == 201 and r.json()["doit_changer_mdp"] is True
    assert emails[0]["to"] == "nina@ex.com" and "Bienvenue" in emails[0]["sujet"]
    r = client.post(f"/users/{r.json()['id']}/lien-mot-de-passe?envoyer=true", headers=auth(admin))
    assert r.json()["email_envoye"] is True and len(emails) == 2


def test_gabarit_email_echappe_et_texte(monkeypatch):
    html = mail._gabarit("Titre <b>", ["Bonjour"], ("Ouvrir", "https://x.fr/?a=1&b=2"), None)
    assert "Titre &lt;b&gt;" in html and "a=1&amp;b=2" in html
    texte = mail._texte("Titre", ["<strong>Gras</strong>"], ("Ouvrir", "https://x.fr"), None)
    assert "Gras" in texte and "<strong>" not in texte and "Ouvrir : https://x.fr" in texte


# --- Discord -------------------------------------------------------------------------------------------------
def test_discord_inscription_bouton_ajustement_et_roles(client, make_user):
    admin = make_user("admin", discord_id="1")
    a = make_user(discord_id="2", prenom="A")
    b = make_user(discord_id="3", prenom="B")
    make_user(prenom="SansDiscord")
    s = _seance(client, admin, _semestre(client, admin)["id"], places_max=1)
    r = client.post(f"/discord/seances/{s['id']}/inscription", headers=BOT, json={"discord_id": "2", "action": "in"}).json()
    assert r["statut"] == "inscrit" and r["seance"]["nb_inscrits"] == 1
    r = client.post(f"/discord/seances/{s['id']}/inscription", headers=BOT, json={"discord_id": "3", "action": "in"}).json()
    assert r["statut"] == "attente"
    r = client.post(f"/discord/seances/{s['id']}/inscription", headers=BOT, json={"discord_id": "2", "action": "out"}).json()
    assert r["statut"] is None and r["promus"] == ["3"]
    assert client.post(f"/discord/seances/{s['id']}/inscription", headers=BOT,
                       json={"discord_id": "999", "action": "in"}).status_code == 404

    assert client.post("/discord/ajustements", headers=BOT, json={
        "auteur_discord_id": "2", "discord_id": "3", "points": 2, "motif": "Aide"}).status_code == 403
    r = client.post("/discord/ajustements", headers=BOT, json={
        "auteur_discord_id": "1", "discord_id": "3", "points": 2, "motif": "Aide au rangement", "categorie": "organisation"})
    assert r.status_code == 201 and r.json()["points"] == 2

    roles = client.get("/discord/roles", headers=BOT).json()
    assert set(roles["membres"]) == {"1", "2", "3"} and roles["top3"] == ["3"]
