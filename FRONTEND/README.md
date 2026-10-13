# Arcanix — Frontend

Next.js 15 (App Router) + Tailwind v4 + SWR. Voir le [README principal](../README.md).

```bash
npm ci
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

- Thème et tokens : `src/app/globals.css` (Obsidienne par défaut, Parchemin en clair)
- Composants de marque : `src/components/brand/` (logo, cadres enluminés, braises)
- Accès API typé : `src/lib/api.ts` ; session : `src/lib/auth.tsx`
