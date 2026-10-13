"""Logique métier : inscriptions (« Je viens »), pointage par QR code, résultats de tournoi."""
import hashlib
import hmac
import secrets
import time
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import config
from .journal import journaliser
from .models import Ajustement, Inscription, Participation, Pointage, Resultat, Seance, Utilisateur
from .security import utcnow


# --- Inscriptions ------------------------------------------------------------------------
def nb_inscrits(db: Session, seance_id: int) -> int:
    return db.query(func.count()).select_from(Inscription).filter(
        Inscription.seance_id == seance_id, Inscription.statut == "inscrit").scalar() or 0


def inscrire(db: Session, seance: Seance, user: Utilisateur) -> str:
    """Inscrit le membre (ou le place en liste d'attente si complet). Retourne le statut."""
    if seance.date_seance < date.today():
        raise HTTPException(409, "Cette séance est déjà passée")
    existante = db.get(Inscription, {"utilisateur_id": user.id, "seance_id": seance.id})
    if existante:
        return existante.statut
    complet = seance.places_max is not None and nb_inscrits(db, seance.id) >= seance.places_max
    statut = "attente" if complet else "inscrit"
    db.add(Inscription(utilisateur_id=user.id, seance_id=seance.id, statut=statut))
    db.flush()
    return statut


def desinscrire(db: Session, seance: Seance, user: Utilisateur) -> list[Utilisateur]:
    """Désinscrit le membre ; retourne les membres promus depuis la liste d'attente."""
    ins = db.get(Inscription, {"utilisateur_id": user.id, "seance_id": seance.id})
    if not ins:
        return []
    db.delete(ins)
    db.flush()
    return reequilibrer(db, seance)


def reequilibrer(db: Session, seance: Seance) -> list[Utilisateur]:
    """Fait monter la liste d'attente tant qu'il reste des places (ordre d'arrivée)."""
    attente = (db.query(Inscription).filter(Inscription.seance_id == seance.id, Inscription.statut == "attente")
               .order_by(Inscription.cree_le).all())
    if not attente:
        return []
    libres = len(attente) if seance.places_max is None else max(0, seance.places_max - nb_inscrits(db, seance.id))
    promus = []
    for ins in attente[:libres]:
        ins.statut = "inscrit"
        promus.append(ins.utilisateur)
    db.flush()
    return promus


# --- Pointage par QR code ----------------------------------------------------------------
def _code(secret: str, fenetre: int) -> str:
    digest = hmac.new(secret.encode(), str(fenetre).encode(), hashlib.sha256).hexdigest()
    return f"{int(digest[:12], 16) % 10**8:08d}"


def fenetre_courante() -> int:
    return int(time.time() // config.QR_PERIODE_S)


def pointage_ouvert(seance: Seance) -> bool:
    return bool(seance.pointage_secret and seance.pointage_expire_le and seance.pointage_expire_le > utcnow())


def ouvrir_pointage(seance: Seance, heures: int | None = None) -> None:
    if not pointage_ouvert(seance):
        seance.pointage_secret = secrets.token_hex(32)
    seance.pointage_expire_le = utcnow() + timedelta(hours=heures or config.POINTAGE_DUREE_H)


def fermer_pointage(seance: Seance) -> None:
    seance.pointage_secret = None
    seance.pointage_expire_le = None


def code_courant(seance: Seance) -> tuple[str, int]:
    """Code du QR et secondes avant le prochain changement."""
    f = fenetre_courante()
    restant = int(config.QR_PERIODE_S - (time.time() % config.QR_PERIODE_S))
    return _code(seance.pointage_secret, f), restant


def code_valide(seance: Seance, code: str) -> bool:
    """Accepte le code courant et le précédent (scan juste avant le changement)."""
    if not pointage_ouvert(seance):
        return False
    f = fenetre_courante()
    return any(hmac.compare_digest(_code(seance.pointage_secret, w), code.strip()) for w in (f, f - 1))


def pointer(db: Session, seance: Seance, user: Utilisateur) -> str:
    """Enregistre la présence déclarée. Retourne 'pointe', 'deja_pointe' ou 'deja_valide'."""
    p = db.get(Participation, {"utilisateur_id": user.id, "seance_id": seance.id})
    if p and p.present:
        return "deja_valide"
    if db.get(Pointage, {"utilisateur_id": user.id, "seance_id": seance.id}):
        return "deja_pointe"
    db.add(Pointage(utilisateur_id=user.id, seance_id=seance.id))
    journaliser(db, user, "pointage.qr", f"{user.prenom} {user.nom} a pointé via QR code à « {seance.nom} »",
                membre_id=user.id, seance_id=seance.id)
    db.flush()
    return "pointe"


# --- Résultats de tournoi ---------------------------------------------------------------
def libelle_place(place: int) -> str:
    return "1re place" if place == 1 else f"{place}e place"


def enregistrer_resultats(db: Session, seance: Seance, lignes: list[dict], bareme: list[float],
                          auteur: Utilisateur) -> None:
    """Remplace le classement du tournoi et régénère les bonus de podium."""
    ids = [l["utilisateur_id"] for l in lignes]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Un membre apparaît deux fois dans les résultats")
    membres = {u.id: u for u in db.query(Utilisateur).filter(Utilisateur.id.in_(ids))} if ids else {}
    if set(ids) - set(membres):
        raise HTTPException(404, "Membre introuvable dans les résultats")

    db.query(Resultat).filter(Resultat.seance_id == seance.id).delete()
    anciens = db.query(Ajustement).filter(Ajustement.seance_id == seance.id, Ajustement.categorie == "tournoi").all()
    for a in anciens:
        db.delete(a)
    db.flush()

    for l in lignes:
        db.add(Resultat(seance_id=seance.id, **l))
        place = l["place"]
        bonus = bareme[place - 1] if place - 1 < len(bareme) else 0
        u = membres[l["utilisateur_id"]]
        if bonus:
            db.add(Ajustement(
                utilisateur_id=u.id, semestre_id=seance.semestre_id, seance_id=seance.id, points=bonus,
                categorie="tournoi", motif=f"Tournoi « {seance.nom} » : {libelle_place(place)}", cree_par_id=auteur.id,
            ))
        journaliser(db, auteur, "tournoi.resultat",
                    f"{u.prenom} {u.nom} classé·e {libelle_place(place)} à « {seance.nom} »"
                    + (f" (+{bonus:g} pts)" if bonus else ""),
                    membre_id=u.id, seance_id=seance.id, details={"place": place, "bonus": bonus})
    seance.resultats_a_annoncer = bool(lignes)
    db.flush()
