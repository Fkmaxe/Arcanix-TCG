# Arcanix — gestion de l'association TCG

Séances, présences, points et classement de l'association, avec un site web et un bot Discord.

<p align="center"><img src="docs/parcours-mobile.gif" alt="Parcours mobile : accueil, connexion, tableau de bord, calendrier, appel, classement, profil" width="300"></p>

| Dossier | Rôle | Techno |
|---|---|---|
| `API_TCG_ESGI/` | API REST + migrations | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 |
| `FRONTEND/` | Site (mobile-first, thèmes Obsidienne / Parchemin) | Next.js 15, Tailwind v4, SWR |
| `BOT_DISCORD/` | Bot (inscription, points, appel, annonces) | discord.py 2.5 |

## Démarrage rapide

```bash
cp .env.example .env        # puis remplir (voir les commentaires)
docker compose up -d --build
```

- Site : http://localhost:3000 — API : http://localhost:8000 (doc interactive sur `/docs`)
- Développement avec rechargement à chaud : `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
- Données de démonstration (base **vide** uniquement) : `docker compose exec api python -m scripts.seed_demo`
  → comptes `admin@arcanix.fr`, `modo@arcanix.fr`, `membre@arcanix.fr` (mot de passe `arcanix123`)

## Base de données et migrations

Le schéma est géré par **Alembic** ; l'API applique les migrations à chaque démarrage (`app/migrate.py`).

- Base neuve : tout est créé automatiquement.
- **Base existante (ancien `init.sql`)** : elle est détectée, marquée sur la révision `0001`, puis migrée **sans perte**.
  La migration `0002` convertit les points en décimaux, remet à `NULL` les faux `discord_id` « web_… »,
  passe les emails en minuscules, active le semestre le plus récent et marque les séances existantes comme déjà annoncées.

**Avant de déployer en production :**

```bash
docker compose exec db pg_dump -U admin pointsdb > sauvegarde_$(date +%F).sql
```

Si deux comptes ont le même email à la casse près, la migration s'arrête et liste les emails à fusionner.

## Sécurité

- Sessions JWT signées par `JWT_SECRET`, valables `JWT_EXPIRE_DAYS` jours.
- Connexion limitée à 10 échecs par quart d'heure (par IP et email), réponse 429 au-delà.
- Liens de mot de passe et codes Discord à usage unique, stockés hachés, avec expiration.
- Routes du bot protégées par le secret partagé `DISCORD_BOT_TOKEN`.

## Rôles

| Rôle | Peut… |
|---|---|
| `user` | voir les séances, son profil, ses points, le classement ; lier son Discord |
| `moderator` | + créer/modifier/supprimer les séances, faire l'appel, gérer les membres (`user` uniquement), exports |
| `admin` | + rôles, suppression de comptes, semestres (dont « semestre en cours ») |

## Bot Discord

1. Dans le [portail développeur](https://discord.com/developers/applications), régénérer le token du bot et le mettre dans `DISCORD_TOKEN`.
2. Mettre la même valeur aléatoire dans `DISCORD_BOT_TOKEN` (secret partagé API ↔ bot).
3. Renseigner `DISCORD_GUILD_ID` (commandes disponibles immédiatement) et `DISCORD_ANNONCES_CHANNEL_ID`.
4. `FRONTEND_URL` doit être l'URL **publique https** du site pour que les liens et le logo s'affichent dans Discord.

| Commande | Effet |
|---|---|
| `/register` | Formulaire d'inscription → lien privé pour choisir son mot de passe |
| `/lier code` | Lie un compte créé sur le site (code généré sur la page Profil) |
| `/reinitialiser` | Nouveau lien de mot de passe |
| `/points` (`/mypoint`) | Points, rang et présences du semestre en cours |
| `/profil [membre]`, `/historique` | Fiche d'un membre, 10 dernières séances |
| `/classement [semestre]` | Top 10 (public) + ta position |
| `/seances` | Prochaines séances |
| `/mod seance [jeu]` | Créer une séance (formulaire) |
| `/mod presence seance` | Valider jusqu'à 25 présents d'un coup (sélecteur de membres) |

Les commandes `/mod` sont masquées par défaut aux membres sans la permission « Gérer les événements » ;
on peut les ouvrir à un rôle dans *Paramètres du serveur → Intégrations → Arcanix*. Dans tous les cas,
l'API vérifie que l'auteur est `moderator` ou `admin` sur le site (compte lié).

**Annonces automatiques** (toutes les 5 min) : nouvelle séance, rappel la veille, et podium du semestre
quand un admin définit un nouveau « semestre en cours ».

## Tests

```bash
# API (Postgres requis ; la base de test est recréée)
docker compose run --rm -e TEST_DATABASE_URL=postgresql+psycopg://admin:<mdp>@db:5432/arcanix_test api pytest -q
# Bot, sans Discord : chaque commande est exécutée avec de fausses interactions
cd BOT_DISCORD && pip install -r requirements-dev.txt && python -m pytest -q
# Bot de bout en bout contre une vraie API (base remplie avec scripts.seed_demo)
ARCANIX_E2E_API=http://localhost:8000 ARCANIX_E2E_BOT_TOKEN=<DISCORD_BOT_TOKEN> python -m pytest tests/test_e2e.py -v
# Frontend
cd FRONTEND && npm ci && npx tsc --noEmit && npm run lint && npm run build
```
