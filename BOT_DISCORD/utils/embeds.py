"""Mise en forme des messages aux couleurs d'Arcanix (or, braise, obsidienne)."""
from datetime import date

import discord

import config

OR = 0xF5C24B
BRAISE = 0xFF7A1A
FLAMME = 0xE8361F
SUCCES = 0x5AD07A

JEUX = {
    "pokemon": "Pokémon", "magic": "Magic", "yugioh": "Yu-Gi-Oh!", "lorcana": "Lorcana",
    "onepiece": "One Piece", "fab": "Flesh and Blood", "autre": "Autre",
}
MEDAILLES = {1: "🥇", 2: "🥈", 3: "🥉"}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
        "octobre", "novembre", "décembre"]


def logo_url() -> str | None:
    # Discord ne peut afficher que des images publiques (https)
    return f"{config.FRONTEND_URL}/brand/carte-192.png" if config.FRONTEND_URL.startswith("https://") else None


def site_url(path: str = "") -> str:
    return f"{config.FRONTEND_URL}{path}"


def lien_valide(url: str) -> bool:
    """Les boutons-liens Discord exigent une URL http(s) publique."""
    return url.startswith("https://") or url.startswith("http://")


def embed(title: str, description: str | None = None, color: int = OR, thumbnail: bool = True) -> discord.Embed:
    e = discord.Embed(title=title, description=description, color=color)
    if thumbnail and (url := logo_url()):
        e.set_thumbnail(url=url)
    e.set_footer(text="Arcanix · Association TCG")
    return e


def erreur(message: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {message}", color=FLAMME)


def succes(message: str) -> discord.Embed:
    return discord.Embed(description=f"✅ {message}", color=SUCCES)


def rang(r: int) -> str:
    return MEDAILLES.get(r, f"`#{r:>2}`")


def pts(n: float) -> str:
    return f"{n:g}".replace(".", ",")


def semestre(s: dict | None) -> str:
    return f"{s['annee']} · S{s['numero']}" if s else "—"


def date_longue(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


def heure(h: str | None) -> str | None:
    return h[:5].replace(":", "h") if h else None


def ligne_seance(s: dict) -> str:
    infos = [f"📅 {date_longue(s['date_seance']).capitalize()}"]
    if h := heure(s.get("heure_debut")):
        infos.append(f"🕕 {h}")
    if s.get("lieu"):
        infos.append(f"📍 {s['lieu']}")
    if s.get("jeu"):
        infos.append(f"🃏 {JEUX.get(s['jeu'], s['jeu'])}")
    infos.append(f"🔥 +{pts(s['nb_point'])} pts")
    return " · ".join(infos)


def seance_embed(s: dict, titre: str, color: int = BRAISE) -> discord.Embed:
    e = embed(titre, s.get("description"), color)
    e.add_field(name="📅 Date", value=date_longue(s["date_seance"]).capitalize(), inline=True)
    if h := heure(s.get("heure_debut")):
        e.add_field(name="🕕 Heure", value=h, inline=True)
    if s.get("lieu"):
        e.add_field(name="📍 Lieu", value=s["lieu"], inline=True)
    if s.get("jeu"):
        e.add_field(name="🃏 Jeu", value=JEUX.get(s["jeu"], s["jeu"]), inline=True)
    e.add_field(name="🔥 Points", value=f"+{pts(s['nb_point'])}", inline=True)
    e.add_field(name=CHAMP_INSCRITS, value=texte_inscrits(s), inline=True)
    return e


CHAMP_INSCRITS = "👥 Inscrits"


def texte_inscrits(s: dict) -> str:
    n, places, attente = s.get("nb_inscrits", 0), s.get("places_max"), s.get("nb_attente", 0)
    txt = f"{n}/{places}" if places else str(n)
    if places and n >= places:
        txt += " · complet"
    if attente:
        txt += f" · {attente} en attente"
    return txt


def maj_inscrits(e: discord.Embed, s: dict) -> discord.Embed:
    """Met à jour le compteur d'inscrits d'une annonce existante."""
    for i, f in enumerate(e.fields):
        if f.name == CHAMP_INSCRITS:
            e.set_field_at(i, name=CHAMP_INSCRITS, value=texte_inscrits(s), inline=True)
            return e
    e.add_field(name=CHAMP_INSCRITS, value=texte_inscrits(s), inline=True)
    return e


def bouton_lien(label: str, url: str, emoji: str | None = None) -> discord.ui.View | None:
    if not lien_valide(url):
        return None
    v = discord.ui.View()
    v.add_item(discord.ui.Button(label=label, url=url, emoji=emoji))
    return v
