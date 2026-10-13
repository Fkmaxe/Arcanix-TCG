from datetime import date, timedelta

from jose import jwt

from app import config
from tests.conftest import BOT, auth


def _semestre(client, admin, annee=2025, numero=1):
    r = client.post("/semestres", json={"annee": annee, "numero": numero}, headers=auth(admin))
    assert r.status_code == 201, r.text
    return r.json()


def _seance(client, staff, semestre_id, points=1.5, jours=0, **extra):
    body = {"nom": "Tournoi", "date_seance": (date.today() + timedelta(days=jours)).isoformat(),
            "nb_point": points, "semestre_id": semestre_id, **extra}
    r = client.post("/seances", json=body, headers=auth(staff))
    assert r.status_code == 201, r.text
    return r.json()


# --- Auth -------------------------------------------------------------------------------
def test_login_insensible_a_la_casse_et_jwt_expirant(client, make_user):
    make_user(email="alice@ex.com", password="secret123")
    r = client.post("/auth/login", json={"email": "Alice@EX.com ", "password": "secret123"})
    assert r.status_code == 200
    data = jwt.decode(r.json()["access_token"], config.JWT_SECRET, algorithms=["HS256"])
    assert "exp" in data
    assert client.post("/auth/login", json={"email": "alice@ex.com", "password": "mauvais!"}).status_code == 401


def test_token_expire_refuse(client, make_user):
    u = make_user()
    expire = jwt.encode({"sub": str(u.id), "exp": 1}, config.JWT_SECRET, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expire}"}).status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_inscription_publique_force_role_user(client):
    r = client.post("/users", json={"nom": "N", "prenom": "P", "adresse_mail": "X@ex.com",
                                    "classe": "1A", "role_utilisateur": "admin", "password": "12345678"})
    assert r.status_code == 201
    assert r.json()["role_utilisateur"] == "user"
    assert r.json()["adresse_mail"] == "x@ex.com"
    assert r.json()["discord_id"] is None
    # doublon insensible à la casse
    r = client.post("/users", json={"nom": "N", "prenom": "P", "adresse_mail": "x@EX.com",
                                    "classe": "1A", "password": "12345678"})
    assert r.status_code == 409


def test_liste_users_avec_compte_web(client, make_user):
    """Régression : discord_id texte faisait planter /users en 500."""
    admin = make_user("admin", discord_id="web_old@ex.com")
    r = client.get("/users", headers=auth(admin))
    assert r.status_code == 200
    assert r.headers["X-Total-Count"] == "1"


# --- Permissions --------------------------------------------------------------------------
def test_moderateur_ne_peut_pas_promouvoir_admin(client, make_user):
    mod = make_user("moderator")
    membre = make_user("user")
    r = client.patch(f"/users/{membre.id}", json={"role_utilisateur": "admin"}, headers=auth(mod))
    assert r.status_code == 403
    r = client.post("/users", json={"nom": "N", "prenom": "P", "adresse_mail": "n@ex.com", "classe": "1A",
                                    "role_utilisateur": "admin", "password": "12345678"}, headers=auth(mod))
    assert r.status_code == 403
    r = client.patch(f"/users/{membre.id}", json={"classe": "4B"}, headers=auth(mod))
    assert r.status_code == 200 and r.json()["classe"] == "4B"


def test_dernier_admin_protege(client, make_user):
    admin = make_user("admin")
    assert client.patch(f"/users/{admin.id}", json={"role_utilisateur": "user"}, headers=auth(admin)).status_code == 409
    assert client.delete(f"/users/{admin.id}", headers=auth(admin)).status_code == 409


def test_membre_ne_gere_pas_les_seances(client, make_user):
    admin, membre = make_user("admin"), make_user("user")
    sem = _semestre(client, admin)
    r = client.post("/seances", json={"nom": "X", "date_seance": "2025-01-01", "nb_point": 1,
                                      "semestre_id": sem["id"]}, headers=auth(membre))
    assert r.status_code == 403


# --- Points, classement -----------------------------------------------------------------------
def test_points_decimaux_et_classement(client, make_user):
    admin = make_user("admin", prenom="Ada", nom="Admin")
    a, b, c = make_user(prenom="Alice", nom="Zed"), make_user(prenom="Bob", nom="Yon"), make_user(prenom="Cid", nom="Xu")
    sem = _semestre(client, admin)
    s1 = _seance(client, admin, sem["id"], points=1.5)
    s2 = _seance(client, admin, sem["id"], points=2)
    r = client.put(f"/seances/{s1['id']}/participants", headers=auth(admin), json={"participants": [
        {"utilisateur_id": a.id, "present": True}, {"utilisateur_id": b.id, "present": True},
        {"utilisateur_id": c.id, "present": False}]})
    assert r.status_code == 200, r.text
    assert r.json()["nb_presents"] == 2
    client.put(f"/seances/{s2['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": a.id, "present": True}]})

    me = client.get("/me/points", headers=auth(a)).json()
    assert me["total"] == 3.5  # plus de troncature int()

    cl = client.get("/stats/classement", headers=auth(b)).json()
    assert [l["prenom"] for l in cl["lignes"]] == ["Alice", "Bob"]
    assert cl["lignes"][0]["nom"] == "Z."  # nom abrégé pour un membre
    assert cl["lignes"][1]["moi"] is True

    # vue modération : tout le monde, y compris à 0 point
    pts = client.get(f"/stats/points?semestreId={sem['id']}", headers=auth(admin)).json()
    assert {p["prenom"] for p in pts} == {"Ada", "Alice", "Bob", "Cid"}

    stats = client.get("/me/stats", headers=auth(a)).json()
    assert stats["rang"] == 1 and stats["points"] == 3.5 and stats["evolution"][-1]["cumul"] == 3.5


def test_appel_remplace_les_participants(client, make_user):
    admin, a, b = make_user("admin"), make_user(), make_user()
    sem = _semestre(client, admin)
    s = _seance(client, admin, sem["id"])
    client.put(f"/seances/{s['id']}/participants", headers=auth(admin),
               json={"participants": [{"utilisateur_id": a.id}, {"utilisateur_id": b.id}]})
    r = client.put(f"/seances/{s['id']}/participants", headers=auth(admin),
                   json={"participants": [{"utilisateur_id": b.id, "present": False}]})
    det = r.json()
    assert [p["utilisateur_id"] for p in det["participants"]] == [b.id]
    assert det["participants"][0]["present"] is False


# --- Semestres ----------------------------------------------------------------------------------
def test_semestre_actif_et_suppression_protegee(client, make_user):
    admin = make_user("admin")
    s1 = _semestre(client, admin, 2025, 1)
    assert s1["actif"] is True  # premier semestre activé automatiquement
    s2 = _semestre(client, admin, 2025, 2)
    assert client.post("/semestres", json={"annee": 2025, "numero": 2}, headers=auth(admin)).status_code == 409
    _seance(client, admin, s1["id"])
    assert client.delete(f"/semestres/{s1['id']}", headers=auth(admin)).status_code == 409
    r = client.post(f"/semestres/{s2['id']}/activer", headers=auth(admin))
    assert r.json()["actif"] is True
    assert client.get("/semestres/actif").json()["id"] == s2["id"]
    # l'ancien semestre a un podium à annoncer
    annonces = client.get("/discord/annonces/en-attente", headers=BOT).json()
    assert any(a["type"] == "podium" and a["id"] == s1["id"] for a in annonces)


# --- Discord ------------------------------------------------------------------------------------
def test_routes_discord_protegees(client):
    assert client.get("/discord/points/discord/1").status_code == 401
    assert client.get("/discord/classement", headers={"x-bot-token": "faux"}).status_code == 401


def test_inscription_discord_puis_activation(client):
    r = client.post("/discord/inscription", headers=BOT, json={
        "discord_id": "42", "nom": "Doe", "prenom": "Jane", "adresse_mail": "Jane@ex.com", "classe": "2B"})
    assert r.status_code == 201, r.text
    url = r.json()["url"]
    assert url.startswith("https://arcanix.test/activer?jeton=")
    jeton = url.split("jeton=")[1]

    # pas de mot de passe par défaut connu
    assert client.post("/auth/login", json={"email": "jane@ex.com", "password": "default1234"}).status_code == 401

    r = client.post("/auth/definir-mot-de-passe", json={"jeton": jeton, "mot_de_passe": "nouveau-mdp"})
    assert r.status_code == 200
    tok = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert me["doit_changer_mdp"] is False and me["discord_lie"] is True
    # jeton à usage unique
    assert client.post("/auth/definir-mot-de-passe", json={"jeton": jeton, "mot_de_passe": "autre-mdp"}).status_code == 400
    assert client.post("/auth/login", json={"email": "jane@ex.com", "password": "nouveau-mdp"}).status_code == 200


def test_lier_discord_par_code(client, make_user):
    u = make_user()
    code = client.post("/me/code-discord", headers=auth(u)).json()["code"]
    r = client.post("/discord/lier", headers=BOT, json={"discord_id": "777", "code": code.lower()})
    assert r.status_code == 200, r.text
    assert client.get("/discord/membres/777", headers=BOT).status_code == 200
    assert client.post("/discord/lier", headers=BOT, json={"discord_id": "777", "code": code}).status_code == 400


def test_presences_discord_reservees_moderation(client, make_user):
    admin = make_user("admin", discord_id="1")
    membre = make_user("user", discord_id="2")
    sem = _semestre(client, admin)
    s = _seance(client, admin, sem["id"])
    r = client.post(f"/discord/seances/{s['id']}/presences", headers=BOT,
                    json={"auteur_discord_id": "2", "discord_ids": ["2"]})
    assert r.status_code == 403
    r = client.post(f"/discord/seances/{s['id']}/presences", headers=BOT,
                    json={"auteur_discord_id": "1", "discord_ids": ["2", "999"]})
    assert r.json()["ajoutes"] == ["2"] and r.json()["non_lies"] == ["999"]
    assert client.get("/discord/membres/2", headers=BOT).json()["points"] == 1.5


def test_annonces_nouvelle_seance_et_rappel(client, make_user):
    admin = make_user("admin")
    sem = _semestre(client, admin)
    s = _seance(client, admin, sem["id"], jours=1)
    annonces = client.get("/discord/annonces/en-attente", headers=BOT).json()
    assert [(a["type"], a["id"]) for a in annonces] == [("nouvelle_seance", s["id"])]
    client.post("/discord/annonces/ack", headers=BOT, json=[{"type": "nouvelle_seance", "id": s["id"]}])
    # annoncée la veille : pas de rappel en double
    assert client.get("/discord/annonces/en-attente", headers=BOT).json() == []


def test_limitation_des_tentatives_de_connexion(client, make_user):
    make_user(email="cible@ex.com", password="bon-mot-de-passe")
    for _ in range(10):
        assert client.post("/auth/login", json={"email": "cible@ex.com", "password": "faux"}).status_code == 401
    r = client.post("/auth/login", json={"email": "cible@ex.com", "password": "bon-mot-de-passe"})
    assert r.status_code == 429 and "Retry-After" in r.headers
    # un autre compte n'est pas bloqué
    make_user(email="autre@ex.com", password="bon-mot-de-passe")
    assert client.post("/auth/login", json={"email": "autre@ex.com", "password": "bon-mot-de-passe"}).status_code == 200
