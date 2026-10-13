"""Crée le premier compte admin, ou promeut un compte existant.

Sur une base neuve, personne ne peut gérer le site : l'inscription publique donne le rôle « membre »
et seul un admin peut nommer un admin. Cette commande règle ce premier pas.

    # Promouvoir un compte déjà créé (inscription sur le site ou /register sur Discord)
    docker compose exec api python -m scripts.creer_admin --email toi@exemple.fr

    # Créer le compte (mot de passe demandé au clavier, jamais en argument)
    docker compose exec -it api python -m scripts.creer_admin --email toi@exemple.fr --prenom Prénom --nom Nom --classe 5A

    # Sans saisie : affiche un lien à usage unique pour choisir le mot de passe sur le site
    docker compose exec api python -m scripts.creer_admin --email toi@exemple.fr --prenom Prénom --nom Nom --classe 5A --lien
"""
import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.journal import journaliser
from app.models import Utilisateur
from app.security import hash_password, lien_mot_de_passe, unusable_password_hash


def creer_ou_promouvoir(db: Session, email: str, prenom: str | None = None, nom: str | None = None,
                        classe: str | None = None, mot_de_passe: str | None = None) -> tuple[Utilisateur, bool, str | None]:
    """Retourne (utilisateur, créé ?, lien d'activation éventuel). Ne commite pas."""
    email = email.strip().lower()
    user = db.query(Utilisateur).filter(Utilisateur.adresse_mail == email).first()
    if user:
        ancien = user.role_utilisateur
        user.role_utilisateur = "admin"
        if ancien != "admin":
            journaliser(db, None, "membre.role", f"Rôle de {user.prenom} {user.nom} : {ancien} → admin (ligne de commande)",
                        membre_id=user.id, details={"avant": ancien, "apres": "admin"})
        return user, False, None

    if not (prenom and nom and classe):
        raise ValueError("Aucun compte avec cet email : --prenom, --nom et --classe sont nécessaires pour le créer")
    if mot_de_passe is not None and len(mot_de_passe) < 8:
        raise ValueError("Le mot de passe doit faire au moins 8 caractères")
    user = Utilisateur(
        nom=nom.strip(), prenom=prenom.strip(), classe=classe.strip(), adresse_mail=email, role_utilisateur="admin",
        mot_de_passe_hash=hash_password(mot_de_passe) if mot_de_passe else unusable_password_hash(),
        doit_changer_mdp=mot_de_passe is None,
    )
    db.add(user)
    db.flush()
    journaliser(db, None, "membre.creation", f"Compte admin de {user.prenom} {user.nom} créé (ligne de commande)",
                membre_id=user.id)
    lien = None if mot_de_passe else lien_mot_de_passe(db, user)[0]
    return user, True, lien


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Crée le premier admin ou promeut un compte existant.")
    p.add_argument("--email", required=True)
    p.add_argument("--prenom")
    p.add_argument("--nom")
    p.add_argument("--classe")
    p.add_argument("--lien", action="store_true", help="ne pas saisir de mot de passe : afficher un lien d'activation")
    args = p.parse_args(argv)

    with SessionLocal() as db:
        existe = db.query(Utilisateur).filter(Utilisateur.adresse_mail == args.email.strip().lower()).first()
        mot_de_passe = None
        if not existe and not (args.prenom and args.nom and args.classe):
            print("❌ Aucun compte avec cet email : ajoute --prenom, --nom et --classe pour le créer.")
            return 1
        if not existe and not args.lien:
            if not sys.stdin.isatty():
                print("Pas de terminal interactif : relance avec « docker compose exec -it … » ou ajoute --lien.")
                return 1
            mot_de_passe = getpass.getpass("Mot de passe (8 caractères min.) : ")
            if mot_de_passe != getpass.getpass("Confirmation : "):
                print("❌ Les mots de passe ne correspondent pas.")
                return 1
        try:
            user, cree, lien = creer_ou_promouvoir(db, args.email, args.prenom, args.nom, args.classe, mot_de_passe)
        except ValueError as e:
            print(f"❌ {e}")
            return 1
        db.commit()
        print(f"✅ {user.prenom} {user.nom} <{user.adresse_mail}> est {'créé·e et ' if cree else ''}admin.")
        if lien:
            print(f"🔑 Lien pour choisir le mot de passe (48 h, usage unique) :\n   {lien}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
