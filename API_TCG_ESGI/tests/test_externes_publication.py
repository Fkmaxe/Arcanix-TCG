"""Membres internes/externes, publication programmée des séances, staff hors classement."""
from datetime import UTC, date, datetime, timedelta

import pytest
from app import config, mail, planificateur
from app.database import engine
from app.security import signature_desabonnement
from sqlalchemy import text

from tests.conftest import BOT, auth

DOMAINE = "ex.com"  # domaine « école » des tests (conftest)


def _inscription(client, **extra):
    body = {"nom": "Dupont", "prenom": "Jean", "password": "motdepasse", **extra}
    return client.post("/users", json=body)


# --- Interne / externe --------------------------------------------------------------------------------
def test_interne_exige_adresse_ecole_et_classe(client):
    r = _inscription(client, adresse_mail=f"j.dupont@{DOMAINE}")
    assert r.status_code == 422 and "classe" in r.text
    r = _inscription(client, adresse_mail="jean@gmail.com", classe="3A")
    assert r.status_code == 422 and "adresse de l'école" in r.text
    r = _inscription(client, adresse_mail=f"J.Dupont@{DOMAINE}", classe=" 3A ")
    assert r.status_code == 201
    assert (r.json()["externe"], r.json()["classe"], r.json()["adresse_mail"]) == (False, "3A", f"j.dupont@{DOMAINE}")


def test_externe_sans_classe_et_email_libre(client):
    r = _inscription(client, adresse_mail="fan.tcg@gmail.com", externe=True, classe="ignorée")
    assert r.status_code == 201
    assert r.json()["externe"] is True and r.json()["classe"] is None
    tok = client.post("/auth/login", json={"email": "fan.tcg@gmail.com", "password": "motdepasse"}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert me["externe"] and me["classe"] is None and me["annonces_email"] is True
    # un externe n'a pas de classe à modifier
    r = client.patch("/me", json={"classe": "1A"}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 422


def test_inscription_discord_interne_et_externe(client):
    r = client.post("/discord/inscription", headers=BOT, json={
        "discord_id": "11", "nom": "N", "prenom": "P", "adresse_mail": f"p.n@{DOMAINE}", "classe": "2A"})
    assert r.status_code == 201
    r = client.post("/discord/inscription", headers=BOT, json={
        "discord_id": "12", "nom": "N", "prenom": "P", "adresse_mail": f"p.m@{DOMAINE}"})
    assert r.status_code == 422  # interne sans classe
    r = client.post("/discord/inscription", headers=BOT, json={
        "discord_id": "13", "nom": "N", "prenom": "Q", "adresse_mail": "q@outlook.fr", "externe": True})
    assert r.status_code == 201
    assert client.get("/discord/membres/13", headers=BOT).json()["externe"] is True


def test_moderation_bascule_interne_externe(client, make_user):
    admin = make_user("admin")
    membre = make_user(email=f"m@{DOMAINE}", classe="1A")
    r = client.patch(f"/users/{membre.id}", json={"externe": True}, headers=auth(admin))
    assert r.status_code == 200 and r.json()["externe"] and r.json()["classe"] is None
    r = client.patch(f"/users/{membre.id}", json={"externe": False}, headers=auth(admin))
    assert r.status_code == 422  # redevenir interne demande une classe
    r = client.patch(f"/users/{membre.id}", json={"externe": False, "classe": "2B"}, headers=auth(admin))
    assert r.status_code == 200 and r.json()["classe"] == "2B"


# --- Staff hors classement ---------------------------------------------------------------------------
def test_staff_exclu_du_classement(client, make_user):
    admin = make_user("admin", prenom="Ada", discord_id="1")
    mod = make_user("moderator", prenom="Mo", discord_id="2")
    a, b = make_user(prenom="Ana", discord_id="3"), make_user(prenom="Bob", discord_id="4")
    sem = client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()
    s = client.post("/seances", headers=auth(admin), json={
        "nom": "T", "date_seance": date.today().isoformat(), "nb_point": 3, "semestre_id": sem["id"]}).json()
    client.put(f"/seances/{s['id']}/participants", headers=auth(admin), json={"participants": [
        {"utilisateur_id": u.id} for u in (admin, mod, a, b)]})
    client.post("/ajustements", headers=auth(admin), json={"utilisateur_id": a.id, "points": 1, "motif": "Aide"})

    lignes = client.get("/stats/classement", headers=auth(b)).json()["lignes"]
    assert [(l["prenom"], l["rang"]) for l in lignes] == [("Ana", 1), ("Bob", 2)]
    assert client.get("/discord/classement", headers=BOT).json()["lignes"][0]["prenom"] == "Ana"
    assert client.get("/discord/roles", headers=BOT).json()["top3"] == ["3", "4"]

    # le staff garde ses points mais n'a pas de rang
    stats = client.get("/me/stats", headers=auth(mod)).json()
    assert stats["points"] == 3 and stats["rang"] is None and stats["hors_classement"] is True
    assert client.get("/discord/membres/1", headers=BOT).json()["hors_classement"] is True
    assert client.get("/me/stats", headers=auth(a)).json()["hors_classement"] is False

    # exports : tout le monde, rang vide pour le staff
    pts = {p["prenom"]: p for p in client.get(f"/stats/points?semestreId={sem['id']}", headers=auth(admin)).json()}
    assert pts["Ada"]["rang"] is None and pts["Mo"]["role"] == "moderator" and pts["Ana"]["rang"] == 1
    csv = client.get(f"/exports/points.csv?semestreId={sem['id']}", headers=auth(admin)).text
    assert "rang;nom;prenom;role" in csv and ";admin;" in csv


def test_podium_sans_staff(client, make_user):
    admin = make_user("admin", prenom="Ada")
    a = make_user(prenom="Ana")
    s1 = client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()
    s2 = client.post("/semestres", json={"annee": 2026, "numero": 2}, headers=auth(admin)).json()
    seance = client.post("/seances", headers=auth(admin), json={
        "nom": "T", "date_seance": date.today().isoformat(), "nb_point": 9, "semestre_id": s1["id"]}).json()
    client.put(f"/seances/{seance['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": admin.id}, {"utilisateur_id": a.id}]})
    client.post(f"/semestres/{s2['id']}/activer", headers=auth(admin))
    podium = next(x for x in client.get("/discord/annonces/en-attente", headers=BOT).json() if x["type"] == "podium")
    assert [l["prenom"] for l in podium["podium"]] == ["Ana"]


# --- Publication programmée -------------------------------------------------------------------------------
@pytest.fixture
def smtp(monkeypatch):
    """Faux SMTP : capture les lots d'emails."""
    lots = []
    monkeypatch.setattr(config, "SMTP_ACTIF", True)
    monkeypatch.setattr(mail, "envoyer_lot", lambda messages: lots.append(messages) or len(messages))
    return lots


def _seance(client, admin, sem_id, **extra):
    r = client.post("/seances", headers=auth(admin), json={
        "nom": "Draft", "date_seance": (date.today() + timedelta(days=3)).isoformat(), "nb_point": 2,
        "semestre_id": sem_id, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def _annonces(client):
    return [(a["type"], a["id"]) for a in client.get("/discord/annonces/en-attente", headers=BOT).json()]


def test_publication_discord_immediate_programmee_ou_jamais(client, make_user):
    admin = make_user("admin")
    sem = client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()
    tout_de_suite = _seance(client, admin, sem["id"])
    dans_une_heure = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    plus_tard = _seance(client, admin, sem["id"], discord_mode="programme", discord_le=dans_une_heure)
    jamais = _seance(client, admin, sem["id"], discord_mode="jamais")
    assert plus_tard["discord_publier_le"] is not None and jamais["discord_publier_le"] is None
    ids = [i for t, i in _annonces(client) if t == "nouvelle_seance"]
    assert ids == [tout_de_suite["id"]]

    # l'heure arrive : elle est publiée
    with engine.begin() as c:
        c.execute(text("UPDATE seance SET discord_publier_le = now() - interval '1 minute' WHERE id = :i"),
                  {"i": plus_tard["id"]})
    assert ("nouvelle_seance", plus_tard["id"]) in _annonces(client)

    # programmer sans date -> 422 ; reprogrammer une annonce déjà publiée -> 409
    assert client.post("/seances", headers=auth(admin), json={
        "nom": "X", "date_seance": "2030-01-01", "nb_point": 1, "semestre_id": sem["id"],
        "discord_mode": "programme"}).status_code == 422
    client.post("/discord/annonces/ack", headers=BOT, json=[{"type": "nouvelle_seance", "id": tout_de_suite["id"]}])
    r = client.patch(f"/seances/{tout_de_suite['id']}", headers=auth(admin), json={"discord_mode": "jamais"})
    assert r.status_code == 409
    # une date sans fuseau est comprise à l'heure de Paris
    r = client.patch(f"/seances/{jamais['id']}", headers=auth(admin),
                     json={"discord_mode": "programme", "discord_le": "2030-06-01T18:00:00"})
    publie = datetime.fromisoformat(r.json()["discord_publier_le"])
    assert publie == datetime(2030, 6, 1, 16, 0, tzinfo=UTC)  # 18 h à Paris = 16 h UTC en été


def test_email_programme_sans_smtp_refuse(client, make_user):
    admin = make_user("admin")
    sem = client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()
    s = _seance(client, admin, sem["id"])  # « dès la création » par défaut : sans SMTP, aucun email prévu
    assert s["email_publier_le"] is None
    r = client.post("/seances", headers=auth(admin), json={
        "nom": "X", "date_seance": "2030-01-01", "nb_point": 1, "semestre_id": sem["id"],
        "email_mode": "programme", "email_le": "2030-01-01T10:00:00Z"})
    assert r.status_code == 409


def test_planificateur_envoie_une_seule_fois_aux_abonnes(client, make_user, smtp):
    admin = make_user("admin", email=f"admin@{DOMAINE}", classe="5A")
    abonne = make_user(email=f"a@{DOMAINE}", prenom="Abo", classe="1A")
    desabonne = make_user(email=f"d@{DOMAINE}", prenom="Des", classe="1A")
    sem = client.post("/semestres", json={"annee": 2026, "numero": 1}, headers=auth(admin)).json()
    # désinscription en un clic (lien signé), puis signature falsifiée refusée
    assert client.post(f"/auth/desabonner?u={desabonne.id}&s={signature_desabonnement(desabonne.id)}").status_code == 200
    assert client.post(f"/auth/desabonner?u={abonne.id}&s=faux").status_code == 400

    maintenant = _seance(client, admin, sem["id"], places_max=12)
    programmee = _seance(client, admin, sem["id"], email_mode="programme",
                         email_le=(datetime.now(UTC) + timedelta(days=1)).isoformat())
    assert planificateur.envoyer_annonces_dues() == 1  # seule l'immédiate est due
    assert planificateur.envoyer_annonces_dues() == 0  # jamais deux fois
    (lot,) = smtp
    destinataires = sorted(m["To"] for m in lot)
    assert destinataires == sorted([f"admin@{DOMAINE}", f"a@{DOMAINE}"])
    msg = next(m for m in lot if m["To"] == f"a@{DOMAINE}")
    assert "Draft" in msg["Subject"] and "desabonnement?u=" in msg["List-Unsubscribe"]
    corps = msg.get_body(("html",)).get_content()
    assert "12 places restantes sur 12" in corps and f"/seances/{maintenant['id']}" in corps

    # l'email programmé part quand son heure arrive
    with engine.begin() as c:
        c.execute(text("UPDATE seance SET email_publier_le = now() WHERE id = :i"), {"i": programmee["id"]})
    assert planificateur.envoyer_annonces_dues() == 1 and len(smtp) == 2
    journal = client.get(f"/journal?seanceId={programmee['id']}&action=seance.annonce_email", headers=auth(admin)).json()
    assert "2/2" in journal[0]["resume"]
    # l'email déjà parti ne se reprogramme plus
    assert client.patch(f"/seances/{programmee['id']}", headers=auth(admin),
                        json={"email_mode": "jamais"}).status_code == 409


def test_preference_email_dans_le_profil(client, make_user):
    u = make_user(email=f"u@{DOMAINE}", classe="1A")
    r = client.patch("/me", json={"annonces_email": False}, headers=auth(u))
    assert r.status_code == 200 and r.json()["annonces_email"] is False
