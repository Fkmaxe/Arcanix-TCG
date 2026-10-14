# Configurer le fichier `.env`

Ce guide explique, variable par variable, ce qu'il faut mettre dans `.env`, où trouver chaque valeur et ce qui casse si elle est fausse.

Le fichier `.env` se trouve à la racine du projet, à côté de `docker-compose.yml`. Pour le créer :

```bash
cp .env.example .env
```

> 🔒 `.env` contient des secrets : il est ignoré par git et ne doit jamais être envoyé sur un dépôt, un Discord ou par email.

---

## Sommaire

1. [Règles d'écriture du fichier](#1-règles-décriture-du-fichier)
2. [Tableau récapitulatif](#2-tableau-récapitulatif)
3. [Base de données](#3-base-de-données)
4. [API : sécurité et adresses](#4-api--sécurité-et-adresses)
5. [Site web (frontend)](#5-site-web-frontend)
6. [Emails (SMTP)](#6-emails-smtp)
7. [Discord](#7-discord)
8. [Réglages avancés](#8-réglages-avancés)
9. [Exemples complets](#9-exemples-complets)
10. [Appliquer une modification](#10-appliquer-une-modification)
11. [Dépannage](#11-dépannage)

---

## 1. Règles d'écriture du fichier

- **Une variable par ligne**, au format `NOM=valeur`, sans espace autour du `=`.
- Les lignes qui commencent par `#` sont des commentaires.
- **Pas de guillemets** dans le cas général : `CORS_ORIGINS=https://arcanix.fr`.
- **Valeur avec des espaces** : mets-la entre guillemets doubles, par exemple `SMTP_FROM="Arcanix <no-reply@arcanix.fr>"`.
- **Valeur contenant un `$`** (fréquent dans les mots de passe) : mets-la entre **guillemets simples**, par exemple `SMTP_PASSWORD='ab$cd'`. Sans eux, Docker Compose remplace `$cd` par une variable vide et le mot de passe devient faux.
- **Variable optionnelle non utilisée** : laisse-la vide (`DISCORD_ROLE_TOP3_ID=`) plutôt que de la supprimer.
- **Adresses (URL)** : toujours avec `https://` ou `http://`, et **sans `/` à la fin**.

### Générer un secret aléatoire

Plusieurs variables attendent une valeur longue et imprévisible. Pour en générer une :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# ou
openssl rand -base64 48
```

Génère une valeur **différente** pour chaque variable secrète.

---

## 2. Tableau récapitulatif

| Variable | Obligatoire ? | Exemple | Utilisée par |
|---|---|---|---|
| `POSTGRES_USER` | non (défaut `admin`) | `arcanix` | base, API |
| `POSTGRES_PASSWORD` | **oui** | *(secret)* | base, API |
| `POSTGRES_DB` | non (défaut `pointsdb`) | `pointsdb` | base, API |
| `JWT_SECRET` | **oui** | *(secret)* | API |
| `JWT_EXPIRE_DAYS` | non (défaut `7`) | `7` | API |
| `CORS_ORIGINS` | **oui en prod** | `https://arcanix.fr` | API |
| `FRONTEND_URL` | **oui en prod** | `https://arcanix.fr` | API, bot |
| `DEBUG` | non (défaut `false`) | `false` | API |
| `EMAIL_DOMAINE_ECOLE` | non (défaut `myskolae.fr`) | `myskolae.fr` | API, bot, site |
| `FORWARDED_ALLOW_IPS` | **oui derrière Nginx** | `192.168.1.10` (IP de la VM Nginx) | API |
| `NEXT_PUBLIC_API_BASE` | **oui en prod** | `https://api.arcanix.fr` | site (au build) |
| `NEXT_PUBLIC_SITE_URL` | **oui en prod** | `https://arcanix.fr` | site (au build) |
| `SMTP_HOST` | non (vide = pas d'emails) | `smtp-relay.brevo.com` | API |
| `SMTP_PORT` | si SMTP | `587` | API |
| `SMTP_USER` | si SMTP | `contact@arcanix.fr` | API |
| `SMTP_PASSWORD` | si SMTP | *(secret)* | API |
| `SMTP_FROM` | si SMTP | `"Arcanix <no-reply@arcanix.fr>"` | API |
| `SMTP_SECURITE` | si SMTP | `starttls` | API |
| `DISCORD_TOKEN` | **oui** | *(secret Discord)* | bot |
| `DISCORD_BOT_TOKEN` | **oui** | *(secret)* | API **et** bot |
| `DISCORD_GUILD_ID` | fortement conseillé | `1234567890123456789` | bot |
| `DISCORD_ANNONCES_CHANNEL_ID` | non (vide = pas d'annonces) | `1234567890123456789` | bot |
| `DISCORD_ANNONCES_ROLE_ID` | non | `1234567890123456789` | bot |
| `DISCORD_ROLE_MEMBRE_ID` | non | `1234567890123456789` | bot |
| `DISCORD_ROLE_TOP3_ID` | non | `1234567890123456789` | bot |
| `DISCORD_SYNC_ROLES` | non (défaut `false`) | `false` | bot |
| `DISCORD_WEBHOOK_URL` | non | `https://discord.com/api/webhooks/…` | API |
| Réglages avancés (§8) | non | – | API, bot |

---

## 3. Base de données

PostgreSQL tourne dans le conteneur `db`. Ces trois valeurs servent à la fois à **créer** la base et à permettre à l'API de **s'y connecter**.

### `POSTGRES_USER`
Nom de l'utilisateur PostgreSQL.
- **Valeur conseillée** : `arcanix`, ou garder `admin`.
- Lettres minuscules, chiffres et `_` uniquement.

### `POSTGRES_PASSWORD` — obligatoire
Mot de passe de cet utilisateur.
- **Valeur** : un secret généré (voir §1). Une valeur générée avec `token_urlsafe` ne contient pas de `$`.
- La base n'est pas exposée sur Internet, mais un mot de passe faible reste une mauvaise idée.

> ⚠️ **Piège majeur** : ces trois valeurs ne sont prises en compte **qu'à la toute première création** de la base, c'est-à-dire quand le volume Docker `postgres_data` est vide. Si tu changes `POSTGRES_PASSWORD` ensuite, la base garde l'ancien mot de passe, l'API n'arrive plus à se connecter et ses logs affichent `password authentication failed`.
>
> Pour changer le mot de passe après coup, change-le aussi dans PostgreSQL, puis mets à jour `.env` :
> ```bash
> docker compose exec db psql -U admin -d pointsdb -c "ALTER USER admin PASSWORD 'nouveau-mot-de-passe';"
> ```

### `POSTGRES_DB`
Nom de la base. **Valeur conseillée** : `pointsdb`, la valeur par défaut. Même règle que ci-dessus : ne la change pas après la première installation.

---

## 4. API : sécurité et adresses

### `JWT_SECRET` — obligatoire
Clé qui signe les sessions de connexion.
- **Valeur** : un secret généré d'au moins 48 caractères (voir §1).
- Quiconque connaît cette valeur peut se fabriquer une session admin : garde-la secrète.
- **La changer déconnecte tout le monde**, ce qui est utile en cas de fuite.
- Sans elle, l'API refuse de démarrer, sauf si `DEBUG=true`.

### `JWT_EXPIRE_DAYS`
Durée d'une session avant de devoir se reconnecter.
- **Défaut** : `7` jours. Entre `1` et `30` est raisonnable.

### `CORS_ORIGINS` — obligatoire en production
Liste des adresses de site autorisées à appeler l'API depuis un navigateur.
- **Valeur** : l'adresse **exacte** du site, telle qu'elle apparaît dans la barre d'adresse : protocole compris, sans `/` final, sans chemin.
- Plusieurs adresses se séparent par des virgules, sans espace.
- Exemples :
  - production : `CORS_ORIGINS=https://arcanix.fr`
  - avec et sans www : `CORS_ORIGINS=https://arcanix.fr,https://www.arcanix.fr`
  - local : `CORS_ORIGINS=http://localhost:3000`
- **Symptôme si c'est faux** : le site s'affiche, mais la connexion et les données échouent (« Impossible de joindre le serveur »). La console du navigateur (F12) affiche une erreur `CORS`.

### `FRONTEND_URL` — obligatoire en production
Adresse publique du site, utilisée pour construire les liens :
- liens d'activation et de mot de passe envoyés par Discord ou par email ;
- QR codes de pointage ;
- boutons « Détails » des annonces Discord ;
- logo affiché dans les emails et les messages Discord.

Indications :
- **Valeur** : `https://arcanix.fr`, sans `/` final.
- Elle doit être **accessible depuis Internet**, sinon les membres ne pourront pas ouvrir les liens ni scanner le QR depuis leur téléphone.
- Discord n'affiche le logo que si l'adresse est en `https://`.

### `EMAIL_DOMAINE_ECOLE`
Domaine des adresses de l'école. Il distingue les deux types de membres :
- **élève (interne)** : adresse `…@<domaine>` et classe obligatoire. À l'inscription, on ne tape que
  l'identifiant (`j.dupont`), le suffixe est affiché et ajouté automatiquement ;
- **externe** : n'importe quelle adresse, pas de classe.
- **Valeur** : `myskolae.fr` (défaut), sans `@`. Le site le lit via l'API et le bot via sa propre copie :
  il est transmis aux deux par `docker-compose.yml`.
- Au passage à cette version, les comptes existants dont l'adresse n'est pas de ce domaine sont marqués externes.

### `DEBUG`
- **En production : `false`, toujours.**
- `true` sert uniquement en développement : l'API accepte un `JWT_SECRET` vide (secret temporaire) et affiche des journaux plus bavards.

### `FORWARDED_ALLOW_IPS` — obligatoire derrière ton Nginx

**Ton installation** : Nginx tourne sur **une VM**, et le site, l'API, le bot et la base sur **une autre VM** (celle de Docker), les deux sur le même réseau local.

```
Internet ──► VM Nginx (ex. 192.168.1.10) ──► VM Docker (ex. 192.168.1.20) : site :3000, API :8000, bot, base
```

C'est Nginx qui contacte l'API : sans réglage, l'API croit que **tous les visiteurs ont l'IP de la VM Nginx**. Cette variable lui dit de faire confiance à l'en-tête `X-Forwarded-For` que Nginx ajoute, pour retrouver la vraie IP du visiteur.

- **Valeur** : l'**IP locale de la VM Nginx**, celle qui arrive sur la VM Docker. Avec l'exemple ci-dessus : `FORWARDED_ALLOW_IPS=192.168.1.10`.
- ❌ **Pas** l'IP de la VM Docker, ni `127.0.0.1`, ni `*`. Avec `*`, n'importe quelle machine du réseau pourrait se faire passer pour une autre IP.
- **Le bot n'est pas concerné** : il parle à l'API directement par le réseau interne Docker (`http://api:8000`), sans passer par Nginx.
- **Pourquoi c'est important** : après 10 échecs en un quart d'heure pour un même couple *IP + email*, la connexion à ce compte est bloquée. Avec une mauvaise valeur, tous les visiteurs ont l'IP du Nginx : n'importe qui peut alors bloquer le compte d'un membre en tapant de faux mots de passe sur son email, et le membre est bloqué même depuis son propre téléphone.

**Trouver la bonne IP à coup sûr** (rien à deviner) :
1. Laisse `FORWARDED_ALLOW_IPS` vide et lance la stack.
2. Ouvre le site **via Nginx** (adresse publique), puis connecte-toi.
3. Sur la VM Docker, lance `docker compose logs api --tail 10`. Les lignes ressemblent à `INFO: 192.168.1.10:51234 - "POST /auth/login HTTP/1.1" 200`.
4. L'IP au début de la ligne (`192.168.1.10`) est celle à mettre dans `FORWARDED_ALLOW_IPS`.
5. Applique le changement avec `docker compose up -d api` et refais une connexion : les logs affichent maintenant l'IP de ton téléphone ou de ta box, et non plus celle de la VM Nginx. C'est réglé.

**Côté Nginx** : il faut `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`, déjà présent dans [nginx-arcanix.conf](nginx-arcanix.conf). Les `proxy_pass` pointent vers l'IP locale de la VM Docker, par exemple `http://192.168.1.20:8000`.

**Recommandé** : sur la VM Docker, n'autorise les ports 3000 et 8000 **que depuis la VM Nginx**. Personne ne peut ainsi contourner Nginx, ni le HTTPS. Par exemple avec `ufw` :
```bash
sudo ufw allow from 192.168.1.10 to any port 3000,8000 proto tcp
sudo ufw deny 3000,8000/tcp
```
Attention : Docker publie ses ports en contournant `ufw` par défaut. Pour un vrai filtrage, publie plutôt les ports sur l'IP locale de la VM Docker (`"192.168.1.20:8000:8000"` dans `docker-compose.yml`), ou filtre au niveau de l'hyperviseur ou du routeur.

---

## 5. Site web (frontend)

> ⚠️ Ces deux variables sont **figées dans le site au moment de sa construction** (`docker compose build`). Après les avoir modifiées, il faut **reconstruire** le site (voir §10). Un simple redémarrage ne suffit pas.

### `NEXT_PUBLIC_API_BASE` — obligatoire en production
Adresse publique de l'API, **vue depuis le navigateur des membres** : le site appelle l'API directement, sans passer par le serveur du site.
- **Valeur** : l'adresse configurée dans ton Nginx pour l'API, par exemple `https://api.arcanix.fr`, sans `/` final.
- Si le site est en `https://`, l'API doit l'être aussi : un navigateur bloque les appels `http://` depuis une page `https://`.
- **Ne mets pas** `http://api:8000` : ce nom n'existe qu'à l'intérieur de Docker, le téléphone d'un membre ne le connaît pas.
- **Vérifier** : ouvre `https://api.arcanix.fr/health` dans un navigateur ; tu dois voir `{"status":"ok"}`.

### `NEXT_PUBLIC_SITE_URL`
Adresse publique du site, utilisée pour l'aperçu des liens partagés (image et titre sur Discord, WhatsApp…).
- **Valeur** : la même que `FRONTEND_URL`, par exemple `https://arcanix.fr`.

---

## 6. Emails (SMTP)

Les emails servent à :
- **annoncer les séances** : envoyés à l'heure choisie dans le formulaire de séance, à tous les membres
  abonnés. Un planificateur intégré à l'API vérifie toutes les `PLANIFICATEUR_INTERVALLE_S` secondes
  (60 par défaut). Chaque email contient un lien de désinscription en un clic, et chacun peut se réabonner
  dans son profil (section Notifications) ;
- **mot de passe oublié** sur le site ;
- **invitation** quand la modération crée un compte ;
- **envoi du lien de mot de passe** depuis la fiche d'un membre ;
- **place libérée** quand un membre sort de la liste d'attente.

**Pour désactiver les emails** : laisse `SMTP_HOST` vide. Tout le reste fonctionne ; la réinitialisation passe alors par `/reinitialiser` sur Discord ou par un lien copié par la modération.

### `SMTP_HOST`
Adresse du serveur d'envoi de ton fournisseur, par exemple `smtp-relay.brevo.com` (voir les exemples plus bas).

### `SMTP_PORT`
- `587` avec `SMTP_SECURITE=starttls`, le cas le plus courant ;
- `465` avec `SMTP_SECURITE=ssl` ;
- `25` ou `1025` avec `SMTP_SECURITE=aucune`, seulement pour un relais local ou Mailpit.

### `SMTP_USER`
Identifiant de connexion au serveur SMTP. Selon le fournisseur, c'est l'adresse email du compte ou un identifiant spécifique. Laisse vide si le serveur ne demande pas d'authentification (relais local).

### `SMTP_PASSWORD`
Mot de passe ou **clé SMTP** fournie par le fournisseur. Ce n'est souvent **pas** le mot de passe de connexion du compte (voir les exemples).
- S'il contient un `$`, mets-le entre guillemets simples (voir §1).

### `SMTP_FROM`
Expéditeur affiché dans la boîte de réception.
- **Format** : `"Nom affiché <adresse@domaine>"`, **entre guillemets doubles** à cause des espaces.
- Exemple : `SMTP_FROM="Arcanix <no-reply@arcanix.fr>"`.
- L'adresse doit être **autorisée par ton fournisseur** (domaine vérifié chez lui), sinon les emails sont refusés ou classés en spam. Gmail remplace d'office l'expéditeur par l'adresse du compte.

### `SMTP_SECURITE`
- `starttls` : port 587, le cas le plus courant ;
- `ssl` : port 465 ;
- `aucune` : aucun chiffrement, **uniquement** pour un relais sur la même machine ou Mailpit en développement.

### Exemples par fournisseur

**Brevo** (gratuit jusqu'à 300 emails par jour, adapté à une association) : crée un compte, puis va dans *SMTP & API → SMTP* pour obtenir l'identifiant et générer une **clé SMTP**. Vérifie ton domaine ou ton adresse d'expéditeur dans *Expéditeurs*.
```dotenv
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=identifiant-affiché-par-brevo@smtp-brevo.com
SMTP_PASSWORD=la-clé-smtp-générée
SMTP_FROM="Arcanix <no-reply@arcanix.fr>"
SMTP_SECURITE=starttls
```

**Gmail** (pour un petit volume) : active la validation en deux étapes sur le compte Google, puis crée un **mot de passe d'application** sur <https://myaccount.google.com/apppasswords>. Le mot de passe normal du compte ne fonctionne pas.
```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=asso.arcanix@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM="Arcanix <asso.arcanix@gmail.com>"
SMTP_SECURITE=starttls
```
Colle le mot de passe d'application de 16 lettres **sans les espaces**.

**OVH** (adresse email d'un domaine OVH) :
```dotenv
SMTP_HOST=ssl0.ovh.net
SMTP_PORT=465
SMTP_USER=contact@arcanix.fr
SMTP_PASSWORD=mot-de-passe-de-la-boîte-mail
SMTP_FROM="Arcanix <contact@arcanix.fr>"
SMTP_SECURITE=ssl
```

> 💡 Pour éviter les spams avec ton propre domaine, ajoute les enregistrements **SPF** et **DKIM** indiqués par ton fournisseur dans la zone DNS du domaine.

**Tester** : sur le site, ouvre *Mot de passe oublié* et saisis ton email. En cas de problème, `docker compose logs api | grep -i email` affiche « Email … envoyé » ou la cause de l'échec : authentification, port, certificat…

---

## 7. Discord

### Avant de commencer : récupérer des identifiants

Les variables `…_ID` sont des **identifiants Discord**, des nombres de 17 à 20 chiffres. Pour les copier :
1. Active le **mode développeur** dans Discord : *Paramètres utilisateur → Avancés → Mode développeur*.
2. Fais un clic droit (ou un appui long sur mobile) sur le serveur, le salon ou le rôle, puis **Copier l'identifiant**.

Pour les rôles : *Paramètres du serveur → Rôles*, clic droit sur le rôle, *Copier l'identifiant du rôle*.

### `DISCORD_TOKEN` — obligatoire
Le **jeton du bot**, qui lui permet de se connecter à Discord.
1. Sur <https://discord.com/developers/applications>, ouvre ton application, puis l'onglet **Bot**.
2. Clique sur **Reset Token** et copie la valeur (environ 70 caractères, avec des points).

À savoir :
- Ce jeton donne le contrôle total du bot. **L'ancien jeton a circulé en clair** dans l'ancien `docker-compose.yml` : régénère-le.
- Discord ne l'affiche qu'une fois : si tu le perds, régénère-en un autre.

**Inviter le bot sur le serveur** : onglet *OAuth2 → URL Generator*.
- Scopes : coche `bot` et `applications.commands`.
- Permissions du bot :
  - *Envoyer des messages*
  - *Intégrer des liens*
  - *Voir les salons*
  - *Lire l'historique des messages*
  - si tu utilises les rôles automatiques : *Gérer les rôles*
  - si tu mentionnes un rôle dans les annonces : *Mentionner @everyone, @here et tous les rôles*

Ouvre ensuite l'URL générée et choisis le serveur.

### `DISCORD_BOT_TOKEN` — obligatoire
⚠️ **Ce n'est pas le jeton Discord**, malgré son nom. C'est un **mot de passe partagé entre l'API et le bot** : le bot le présente à chaque appel pour prouver à l'API que c'est bien lui.
- **Valeur** : un secret généré (voir §1). Tu n'as rien à faire de plus : Docker Compose transmet automatiquement la même valeur à l'API et au bot.
- **Symptôme si ça cloche** : toutes les commandes du bot répondent « Le bot n'est pas autorisé par l'API ».

### `DISCORD_GUILD_ID` — fortement conseillé
Identifiant du **serveur Discord de l'association** (clic droit sur l'icône du serveur, *Copier l'identifiant du serveur*).
- **Avec** : les commandes apparaissent **immédiatement** sur ce serveur.
- **Sans** : elles sont publiées globalement et peuvent mettre **jusqu'à une heure** à apparaître.
- **Requis** pour la synchronisation des rôles (`DISCORD_ROLE_TOP3_ID`, `DISCORD_SYNC_ROLES`).
- Au démarrage, le bot **supprime les commandes globales** restées de l'ancienne version (l'ancien `/register` à 4 champs). Sans ça, Discord afficherait chaque commande en double.

### `DISCORD_ANNONCES_CHANNEL_ID`
Salon où le bot publie automatiquement, toutes les 5 minutes s'il y a du nouveau :
- les **nouvelles séances**, avec les boutons « Je viens » et « Je ne viens plus » ;
- un **rappel la veille** ;
- les **résultats de tournoi** ;
- le **podium** à la fin d'un semestre.

Indications :
- **Valeur** : identifiant du salon, par exemple `#annonces` ou `#séances`.
- Vide = annonces désactivées.
- Le bot doit pouvoir **voir** ce salon et y **écrire**, ce qui se règle dans les permissions du salon.

### `DISCORD_ANNONCES_ROLE_ID`
Rôle **mentionné** dans les annonces de nouvelle séance, de résultats et de podium, mais pas dans les rappels.
- **Valeur** : identifiant d'un rôle comme `@Joueurs`. Vide = pas de mention.
- Pour que la mention notifie vraiment : rends le rôle mentionnable (*Paramètres du rôle → Autoriser tout le monde à mentionner ce rôle*), ou donne au bot la permission *Mentionner tous les rôles*.

### `DISCORD_ROLE_MEMBRE_ID`
Rôle donné automatiquement dès qu'un membre fait `/register` ou `/lier`.
- **Valeur** : identifiant d'un rôle comme `@Membre Arcanix`. Vide = désactivé.
- Le bot a besoin de la permission **Gérer les rôles**, et son propre rôle doit être **placé au-dessus** de ce rôle dans *Paramètres du serveur → Rôles* : glisse le rôle du bot vers le haut. Sinon les logs affichent « Permission Gérer les rôles manquante ».

### `DISCORD_ROLE_TOP3_ID`
Rôle attribué aux **3 premiers du classement du semestre en cours** et retiré à ceux qui en sortent. La vérification a lieu toutes les 15 minutes.
- **Valeur** : identifiant d'un rôle comme `@Champion`. Vide = désactivé.
- Mêmes conditions que le rôle Membre (permission et position).
- **Exige `DISCORD_GUILD_ID`** et l'**intent « Server Members »** :
  1. Ouvre *Developer Portal → ton application → Bot → Privileged Gateway Intents*.
  2. Active **Server Members Intent**, puis enregistre.

  Sans cet intent, le bot **ne démarre pas** et ses logs affichent `PrivilegedIntentsRequired`.

### `DISCORD_SYNC_ROLES`
- `false` (défaut) ou `true`.
- Mets `true` uniquement si tu utilises le rôle Membre **sans** le rôle Top 3 et que tu veux aussi l'attribuer aux comptes déjà liés avant sa mise en place.
- Mêmes exigences que le Top 3 : `DISCORD_GUILD_ID` et l'intent *Server Members*.
- Si `DISCORD_ROLE_TOP3_ID` est rempli, la synchronisation est activée automatiquement, quelle que soit cette valeur.

### `DISCORD_WEBHOOK_URL`
Optionnel et indépendant du bot : un message est posté quand des présences sont validées depuis le site.
- **Valeur** : *Paramètres du salon → Intégrations → Webhooks → Nouveau webhook → Copier l'URL du webhook*.
- Vide = désactivé. Il fait un peu doublon avec les annonces du bot : à toi de voir.
- ⚠️ L'ancien webhook a circulé en clair : **supprime-le** dans Discord et crée-en un nouveau si tu veux garder la fonction.

---

## 8. Réglages avancés

Facultatifs : les valeurs par défaut conviennent dans la plupart des cas. Ajoute la ligne dans `.env` seulement si tu veux changer la valeur.

| Variable | Défaut | Rôle |
|---|---|---|
| `JETON_MDP_HEURES` | `48` | Validité (en heures) des liens d'activation et de réinitialisation du mot de passe |
| `JETON_DISCORD_MINUTES` | `15` | Validité (en minutes) du code affiché sur le profil pour `/lier` |
| `QR_PERIODE_S` | `30` | Fréquence (en secondes) de changement du QR code de pointage. Plus court = plus sûr, mais plus de « QR expiré » sur les téléphones lents |
| `POINTAGE_DUREE_H` | `4` | Durée (en heures) pendant laquelle un pointage QR reste ouvert, s'il n'est pas fermé à la main |
| `ANNONCES_INTERVALLE_MIN` | `5` | Fréquence (en minutes) à laquelle le bot vérifie s'il y a des annonces à publier |
| `ROLES_INTERVALLE_MIN` | `15` | Fréquence (en minutes) de synchronisation des rôles Discord |
| `PLANIFICATEUR_INTERVALLE_S` | `60` | Fréquence (en secondes) à laquelle l'API vérifie les emails d'annonce de séance à envoyer |

---

## 9. Exemples complets

### Production (site `arcanix.fr`, API `api.arcanix.fr`, VM Nginx `192.168.1.10`, VM Docker `192.168.1.20`)

```dotenv
# --- Base de données ---
POSTGRES_USER=arcanix
POSTGRES_PASSWORD=Vq3n8xY2kLmP0tRw7zA4sBc9dEf1gHj6
POSTGRES_DB=pointsdb

# --- API ---
JWT_SECRET=kQ9fZ2mW7xR4tY8uN1pL6vB3cD0eA5sG2hJ9kM4nQ7rT1wX8yZ3bV6cF0dS5aE2
JWT_EXPIRE_DAYS=7
CORS_ORIGINS=https://arcanix.fr
FRONTEND_URL=https://arcanix.fr
DEBUG=false
FORWARDED_ALLOW_IPS=192.168.1.10

# --- Site (figé au build) ---
NEXT_PUBLIC_API_BASE=https://api.arcanix.fr
NEXT_PUBLIC_SITE_URL=https://arcanix.fr

# --- Emails ---
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=8a1b2c001@smtp-brevo.com
SMTP_PASSWORD=xsmtpsib-0123456789abcdef
SMTP_FROM="Arcanix <no-reply@arcanix.fr>"
SMTP_SECURITE=starttls

# --- Discord ---
DISCORD_TOKEN=MTMx…(jeton régénéré dans le Developer Portal)
DISCORD_BOT_TOKEN=P4nW8qZ1xC6vB3mL9kJ2hG5fD7sA0tR
DISCORD_GUILD_ID=1102345678901234567
DISCORD_ANNONCES_CHANNEL_ID=1102345678901234999
DISCORD_ANNONCES_ROLE_ID=
DISCORD_ROLE_MEMBRE_ID=1102345678901235111
DISCORD_ROLE_TOP3_ID=1102345678901235222
DISCORD_SYNC_ROLES=false
DISCORD_WEBHOOK_URL=
```

> Les valeurs ci-dessus sont des **exemples** : génère tes propres secrets.

### Développement en local

```dotenv
POSTGRES_PASSWORD=dev
JWT_SECRET=dev-secret-local-uniquement
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
DEBUG=true
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
DISCORD_TOKEN=jeton-d-un-bot-de-test
DISCORD_BOT_TOKEN=dev-bot
DISCORD_GUILD_ID=identifiant-de-ton-serveur-de-test
```

Lance ensuite `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`. Les emails sont automatiquement redirigés vers Mailpit, visible sur <http://localhost:8025>, donc pas besoin de `SMTP_*`.

---

## 10. Appliquer une modification

| Tu as modifié… | Commande |
|---|---|
| Une variable de l'API (`JWT_*`, `CORS_ORIGINS`, `SMTP_*`, `FRONTEND_URL`, `FORWARDED_ALLOW_IPS`…) | `docker compose up -d api` |
| Une variable du bot (`DISCORD_*`) | `docker compose up -d discordbot` |
| `DISCORD_BOT_TOKEN` (API **et** bot) | `docker compose up -d api discordbot` |
| `NEXT_PUBLIC_API_BASE` ou `NEXT_PUBLIC_SITE_URL` | `docker compose up -d --build frontend` (reconstruction obligatoire) |
| `POSTGRES_*` après la première installation | voir l'avertissement du §3 |
| Plusieurs choses, ou en cas de doute | `docker compose up -d --build` |

`docker compose up -d` recrée automatiquement les conteneurs dont la configuration a changé ; `restart` ne relit **pas** le `.env`.

Pour vérifier ce que Docker va réellement utiliser, la commande suivante affiche la configuration avec les valeurs remplacées (attention, secrets compris) :

```bash
docker compose config
```

---

## 11. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `docker compose up` s'arrête sur « définir … dans .env » | Une variable obligatoire est vide | Remplir `POSTGRES_PASSWORD`, `JWT_SECRET`, `DISCORD_BOT_TOKEN` ou `DISCORD_TOKEN` |
| L'API redémarre en boucle, logs `password authentication failed` | `POSTGRES_PASSWORD` modifié après la création de la base | §3 : remettre l'ancien mot de passe ou le changer dans PostgreSQL |
| Le site s'affiche mais « Impossible de joindre le serveur » | `NEXT_PUBLIC_API_BASE` faux ou API inaccessible | Tester `https://api…/health`, corriger, puis `docker compose up -d --build frontend` |
| Erreur `CORS` dans la console du navigateur (F12) | `CORS_ORIGINS` ne correspond pas exactement à l'adresse du site | Copier l'adresse de la barre du navigateur, sans `/` final |
| Un membre bloqué par « Trop de tentatives » sans s'être trompé | `FORWARDED_ALLOW_IPS` absent ou faux (tout le monde a l'IP du Nginx) | §4, puis attendre 15 minutes ou redémarrer l'API |
| Les liens reçus sur Discord ou par email mènent à `localhost` | `FRONTEND_URL` non renseigné | Mettre l'adresse publique, puis `docker compose up -d api discordbot` |
| Le bot répond « Le bot n'est pas autorisé par l'API » | `DISCORD_BOT_TOKEN` différent entre API et bot, ou un seul conteneur relancé | `docker compose up -d api discordbot` |
| Les commandes du bot n'apparaissent pas | Pas de `DISCORD_GUILD_ID` (délai d'1 h), ou bot invité sans le scope `applications.commands` | Renseigner `DISCORD_GUILD_ID`, ou réinviter le bot (§7) |
| Commandes en double, ou `/register` qui demande les infos avant le formulaire | 1) **L'ancien bot tourne encore** avec le même jeton (il réenregistre ses commandes à chaque démarrage). 2) Anciennes commandes globales ou d'un autre serveur | 1) `docker ps -a` : supprimer les anciens conteneurs (`discord_bot`, `fastapi_app`, `nextjs_app`, `postgres_db`) avec `docker rm -f …`, ou `docker compose up -d --remove-orphans`. 2) Renseigner `DISCORD_GUILD_ID` et redémarrer le bot : il supprime les commandes en trop au démarrage. Puis recharger Discord (Ctrl+R) |
| `/register` reste sur « … réfléchit » | Ancienne version du bot : bouton refusé par Discord car `FRONTEND_URL` vaut `localhost` | Mettre à jour (le lien est désormais écrit en texte si l'adresse n'est pas publique) et renseigner l'adresse publique du site dans `FRONTEND_URL` |
| Le bot ne démarre pas, logs `PrivilegedIntentsRequired` | Rôle Top 3 ou synchro activés sans l'intent | Activer *Server Members Intent* (§7) |
| Les rôles ne sont pas attribués | Permission *Gérer les rôles* manquante ou rôle du bot trop bas | Remonter le rôle du bot au-dessus des rôles gérés |
| Aucune annonce publiée | Salon vide ou mauvais identifiant, ou bot sans accès au salon | Vérifier `DISCORD_ANNONCES_CHANNEL_ID` et les permissions du salon ; logs : `docker compose logs discordbot` |
| « L'envoi d'emails n'est pas configuré » | `SMTP_HOST` vide | §6 |
| Les emails ne partent pas | Identifiants, port ou sécurité incorrects | `docker compose logs api \| grep -i email` donne la cause |
| Les emails arrivent en spam | Domaine non vérifié chez le fournisseur | Vérifier l'expéditeur et ajouter SPF/DKIM (§6) |
| Tout le monde est déconnecté | `JWT_SECRET` modifié | Normal : chacun se reconnecte |
