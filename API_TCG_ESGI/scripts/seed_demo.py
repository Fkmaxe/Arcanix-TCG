"""Remplit une base VIDE avec des données de démonstration (développement uniquement).

Usage : python -m scripts.seed_demo
Comptes créés (mot de passe « arcanix123 ») : admin@arcanix.fr, modo@arcanix.fr, membre@arcanix.fr
"""
import random
from datetime import date, time, timedelta

from app.database import SessionLocal
from app.models import Ajustement, Inscription, Participation, Resultat, Seance, Semestre, Utilisateur
from app.security import hash_password

PRENOMS = ["Léa", "Hugo", "Chloé", "Lucas", "Inès", "Nathan", "Manon", "Théo", "Camille", "Enzo",
           "Sarah", "Louis", "Jade", "Gabriel", "Zoé", "Raphaël", "Lina", "Arthur"]
NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy",
        "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux"]
SEANCES = [("Tournoi Pokémon", "pokemon"), ("Draft Magic", "magic"), ("Initiation Lorcana", "lorcana"),
           ("Soirée Yu-Gi-Oh!", "yugioh"), ("Ligue One Piece", "onepiece"), ("Commander night", "magic")]


def main() -> None:
    db = SessionLocal()
    if db.query(Utilisateur).count():
        raise SystemExit("La base n'est pas vide : seed annulé.")
    random.seed(42)
    pwd = hash_password("arcanix123")
    staff = [
        Utilisateur(nom="Grados", prenom="Maxence", adresse_mail="admin@arcanix.fr", role_utilisateur="admin", classe="5A-INFO", mot_de_passe_hash=pwd, discord_id="100"),
        Utilisateur(nom="Lambert", prenom="Elise", adresse_mail="modo@arcanix.fr", role_utilisateur="moderator", classe="4A-INFO", mot_de_passe_hash=pwd),
        Utilisateur(nom="Fontaine", prenom="Jules", adresse_mail="membre@arcanix.fr", role_utilisateur="user", classe="3A-INFO", mot_de_passe_hash=pwd),
    ]
    membres = [
        Utilisateur(nom=n, prenom=p, adresse_mail=f"{p.lower()}.{n.lower()}@exemple.fr".replace("é", "e").replace("è", "e").replace("ï", "i"),
                    role_utilisateur="user", classe=random.choice(["1A", "2A", "3A-INFO", "4A-SEC"]), mot_de_passe_hash=pwd,
                    discord_id=str(1000 + i) if i % 3 else None)
        for i, (p, n) in enumerate(zip(PRENOMS, NOMS))
    ]
    db.add_all(staff + membres)
    s1 = Semestre(annee=2026, numero=1, actif=False)
    s2 = Semestre(annee=2026, numero=2, actif=True)
    db.add_all([s1, s2])
    db.flush()

    today = date.today()
    seances = []
    for i in range(14):
        nom, jeu = SEANCES[i % len(SEANCES)]
        jour = today + timedelta(days=7 * (i - 9))
        seances.append(Seance(
            nom=nom, jeu=jeu, date_seance=jour, heure_debut=time(18, 30), lieu=random.choice(["Salle B204", "Foyer", "Amphi C"]),
            description="Decks fournis pour les débutants. Venez nombreux !" if i % 2 else None,
            nb_point=random.choice([1, 1.5, 2, 3]), semestre_id=(s1 if i < 3 else s2).id,
            annonce_envoyee=True, rappel_envoye=jour < today,
        ))
    db.add_all(seances)
    db.flush()
    tous = staff + membres
    for s in seances:
        if s.date_seance > today:
            continue
        for u in random.sample(tous, k=random.randint(6, 14)):
            db.add(Participation(utilisateur_id=u.id, seance_id=s.id, present=random.random() > 0.12))
    # Inscriptions aux séances à venir (la première est presque complète)
    a_venir = [s for s in seances if s.date_seance >= today]
    a_venir[0].places_max = 12
    if len(a_venir) > 1:
        a_venir[1].places_max = 16
    for s, n in zip(a_venir, (11, 6, 3)):
        for u in random.sample(membres, k=n):
            db.add(Inscription(utilisateur_id=u.id, seance_id=s.id, statut="inscrit"))

    # Résultats du dernier tournoi passé + bonus de podium
    tournoi = next(s for s in reversed(seances) if s.date_seance < today and s.nom.startswith("Tournoi"))
    db.flush()
    presents = [p.utilisateur_id for p in db.query(Participation).filter_by(seance_id=tournoi.id, present=True)]
    for place, uid in enumerate(presents[:6], start=1):
        db.add(Resultat(seance_id=tournoi.id, utilisateur_id=uid, place=place, victoires=max(0, 5 - place), defaites=place - 1,
                        deck=random.choice(["Dracaufeu ex", "Gardevoir ex", "Lugia VSTAR", None])))
        bonus = {1: 3, 2: 2, 3: 1}.get(place)
        if bonus:
            db.add(Ajustement(utilisateur_id=uid, semestre_id=s2.id, seance_id=tournoi.id, points=bonus, categorie="tournoi",
                              motif=f"Tournoi « {tournoi.nom} » : {'1re' if place == 1 else f'{place}e'} place", cree_par_id=staff[0].id))
    db.add(Ajustement(utilisateur_id=membres[0].id, semestre_id=s2.id, points=2, categorie="organisation",
                      motif="Aide à l'installation du tournoi", cree_par_id=staff[1].id))
    db.add(Ajustement(utilisateur_id=membres[1].id, semestre_id=s2.id, points=-1, categorie="penalite",
                      motif="Absence non excusée à un tournoi inscrit", cree_par_id=staff[1].id))
    db.commit()
    print(f"✅ {len(tous)} membres, 2 semestres, {len(seances)} séances, inscriptions, résultats et bonus")


if __name__ == "__main__":
    main()
