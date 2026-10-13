# Polices auto-hébergées

Embarquées dans le projet pour que le build fonctionne **sans accès à Google Fonts** (serveur filtré, pas d'IPv6, hors ligne…).

| Fichier | Police | Version | Licence |
|---|---|---|---|
| `inter-variable-latin.woff2` | Inter (variable, graisses 100–900), sous-ensemble latin | @fontsource-variable/inter 5.3.0 | SIL OFL 1.1 — `LICENSE-Inter.txt` |
| `cinzel-variable-latin.woff2` | Cinzel (variable, graisses 400–900), sous-ensemble latin | @fontsource-variable/cinzel 5.3.0 | SIL OFL 1.1 — `LICENSE-Cinzel.txt` |

Le sous-ensemble latin couvre le français (é, è, à, ç, ô, œ…). Chargées par `next/font/local` dans `src/app/layout.tsx`.
