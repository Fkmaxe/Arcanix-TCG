"""Envoi des emails d'annonce de séance à l'heure programmée.

Une tâche de fond démarre avec l'API et vérifie régulièrement les séances dont l'email est dû.
La réservation se fait par un UPDATE … RETURNING : même avec plusieurs processus, chaque annonce
part une seule fois.
"""
import asyncio
import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from . import config, mail
from .database import SessionLocal
from .journal import journaliser
from .models import Seance, Utilisateur
from .security import lien_desabonnement
from .vie import nb_inscrits

log = logging.getLogger("arcanix.planificateur")

JEUX = {"pokemon": "Pokémon", "magic": "Magic", "yugioh": "Yu-Gi-Oh!", "lorcana": "Lorcana",
        "onepiece": "One Piece", "fab": "Flesh and Blood", "autre": "Autre"}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]


def _date_longue(d: date) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}".capitalize()


def _infos_seance(db: Session, s: Seance) -> dict:
    places = None
    if s.places_max:
        restantes = max(0, s.places_max - nb_inscrits(db, s.id))
        places = f"{restantes} place{'s' if restantes > 1 else ''} restante{'s' if restantes > 1 else ''} sur {s.places_max}"
    return {
        "nom": s.nom, "date_txt": _date_longue(s.date_seance),
        "heure": s.heure_debut.strftime("%Hh%M") if s.heure_debut else None,
        "lieu": s.lieu, "jeu": JEUX.get(s.jeu or "", s.jeu), "points": f"{float(s.nb_point):g}".replace(".", ","),
        "places": places, "description": s.description, "url": f"{config.FRONTEND_URL}/seances/{s.id}",
    }


def reserver_annonces_dues(db: Session) -> list[int]:
    ids = db.execute(text(
        "UPDATE seance SET email_envoye = true "
        "WHERE email_envoye = false AND email_publier_le IS NOT NULL AND email_publier_le <= now() "
        "AND date_seance >= current_date RETURNING id"
    )).scalars().all()
    db.commit()
    return list(ids)


def envoyer_annonces_dues() -> int:
    """Envoie les annonces dues ; retourne le nombre de séances traitées."""
    if not config.SMTP_ACTIF:
        return 0
    with SessionLocal() as db:
        ids = reserver_annonces_dues(db)
        for sid in ids:
            s = db.get(Seance, sid)
            destinataires = [
                (u.adresse_mail, u.prenom, lien_desabonnement(u.id))
                for u in db.query(Utilisateur).filter(Utilisateur.annonces_email.is_(True)).order_by(Utilisateur.id)
            ]
            envoyes = mail.mail_annonce_seance(_infos_seance(db, s), destinataires)
            journaliser(db, None, "seance.annonce_email",
                        f"Annonce de « {s.nom} » envoyée par email à {envoyes}/{len(destinataires)} membre(s)",
                        seance_id=s.id, details={"envoyes": envoyes, "destinataires": len(destinataires)})
            db.commit()
            log.info("Annonce email de « %s » : %d/%d envoyés", s.nom, envoyes, len(destinataires))
        return len(ids)


async def boucle() -> None:
    log.info("Planificateur des annonces par email démarré (toutes les %d s)", config.PLANIFICATEUR_INTERVALLE_S)
    while True:
        try:
            await asyncio.to_thread(envoyer_annonces_dues)
        except Exception:  # la boucle ne doit jamais s'arrêter
            log.exception("Erreur du planificateur d'emails")
        await asyncio.sleep(config.PLANIFICATEUR_INTERVALLE_S)
