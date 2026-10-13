import asyncio
from datetime import date

import pytest

from cogs.annonces import construire
from cogs.moderation import parse_date, parse_heure
from utils import embeds

SEANCE = {
    "id": 7, "nom": "Draft Magic", "date_seance": "2026-10-14", "heure_debut": "18:30:00", "lieu": "Foyer",
    "jeu": "magic", "description": "Decks fournis", "nb_point": 1.5,
}


@pytest.mark.parametrize("txt,attendu", [
    ("25/10/2026", "2026-10-25"),
    ("25-10-26", "2026-10-25"),
    ("2026-10-25", "2026-10-25"),
    ("3/11", f"{date.today().year}-11-03"),
])
def test_parse_date(txt, attendu):
    assert parse_date(txt) == attendu


@pytest.mark.parametrize("txt", ["31/02/2026", "demain", "2026/13/01"])
def test_parse_date_invalide(txt):
    with pytest.raises(ValueError):
        parse_date(txt)


@pytest.mark.parametrize("txt,attendu", [("18h30", "18:30"), ("9h", "09:00"), ("09:05", "09:05"), ("", None)])
def test_parse_heure(txt, attendu):
    assert parse_heure(txt) == attendu


@pytest.mark.parametrize("txt", ["25h", "18h75", "midi"])
def test_parse_heure_invalide(txt):
    with pytest.raises(ValueError):
        parse_heure(txt)


def test_formats():
    assert embeds.pts(1.5) == "1,5" and embeds.pts(3.0) == "3"
    assert embeds.rang(1) == "🥇" and embeds.rang(12) == "`#12`"
    assert embeds.date_longue("2026-10-14") == "mercredi 14 octobre"
    assert embeds.heure("18:30:00") == "18h30"


def construire_sync(annonce):
    """Les View discord.py exigent une boucle asyncio active (toujours le cas dans le bot)."""
    async def _run():
        return construire(annonce)
    return asyncio.run(_run())


def test_annonce_nouvelle_seance():
    e, view = construire_sync({"type": "nouvelle_seance", "id": 7, "seance": SEANCE})
    assert e.title == "🔥 Nouvelle séance : Draft Magic"
    champs = {f.name: f.value for f in e.fields}
    assert champs["🃏 Jeu"] == "Magic" and champs["🔥 Points"] == "+1,5"
    # Boutons « Je viens » / « Je ne viens plus » persistants, puis le lien
    ids = [c.item.custom_id for c in view.children[:2]]
    assert ids == ["arcanix:inscr:in:7", "arcanix:inscr:out:7"]
    assert view.children[2].url == "https://arcanix.example/seances/7"
    assert view.timeout is None


def test_annonce_rappel_et_podium():
    e, _ = construire_sync({"type": "rappel", "id": 7, "seance": SEANCE})
    assert e.title.startswith("⏰ C'est demain")
    podium = [{"rang": 1, "prenom": "Zoé", "nom": "G.", "points": 13.0},
              {"rang": 2, "prenom": "Enzo", "nom": "M.", "points": 11.5}]
    e, view = construire_sync({"type": "podium", "id": 1, "semestre": {"annee": 2026, "numero": 1}, "podium": podium})
    assert "2026 · S1" in e.title and "🥇 **Zoé G.** — 13 pts" in e.description
    assert view.children[0].url.endswith("/classement")
