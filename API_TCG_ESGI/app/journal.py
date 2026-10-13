"""Historique des actions sensibles (qui a fait quoi, quand)."""
from sqlalchemy.orm import Session

from .models import Journal, Utilisateur


def nom_complet(u: Utilisateur | None) -> str:
    return f"{u.prenom} {u.nom}" if u else "Système"


def journaliser(
    db: Session,
    auteur: Utilisateur | None,
    action: str,
    resume: str,
    *,
    membre_id: int | None = None,
    seance_id: int | None = None,
    details: dict | None = None,
) -> None:
    """Ajoute une entrée ; elle est enregistrée avec la transaction de l'action (même commit)."""
    db.add(Journal(
        auteur_id=auteur.id if auteur else None, auteur_nom=nom_complet(auteur), action=action,
        resume=resume[:500], membre_id=membre_id, seance_id=seance_id, details=details,
    ))
