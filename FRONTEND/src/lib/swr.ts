// src/lib/swr.ts — accès HTTP à l'API + stockage du jeton de session
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "token";
type Listener = (token: string | null) => void;
const listeners = new Set<Listener>();

export const tokenStore = {
    get(): string | null {
        if (typeof window === "undefined") return null;
        try {
            return localStorage.getItem(TOKEN_KEY);
        } catch {
            return null;
        }
    },
    set(token: string | null) {
        try {
            if (token) localStorage.setItem(TOKEN_KEY, token);
            else localStorage.removeItem(TOKEN_KEY);
        } catch {
            /* stockage indisponible (navigation privée) */
        }
        listeners.forEach((l) => l(token));
    },
    subscribe(l: Listener) {
        listeners.add(l);
        return () => {
            listeners.delete(l);
        };
    },
};

export class ApiError extends Error {
    constructor(public status: number, message: string, public detail?: unknown) {
        super(message);
        this.name = "ApiError";
    }
}

const MESSAGES: Record<number, string> = {
    400: "Requête invalide.",
    401: "Votre session a expiré, reconnectez-vous.",
    403: "Vous n'avez pas les droits pour cette action.",
    404: "Élément introuvable.",
    409: "Conflit : cet élément existe déjà.",
    422: "Certains champs sont invalides.",
    500: "Erreur du serveur, réessayez plus tard.",
    503: "Service momentanément indisponible.",
};

function messageFrom(status: number, body: unknown): string {
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
        const first = detail[0] as { loc?: unknown[]; msg?: string };
        const champ = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "";
        return champ ? `Champ « ${champ} » : ${first.msg ?? "invalide"}` : MESSAGES[422];
    }
    return MESSAGES[status] ?? `Erreur ${status}`;
}

async function request(url: string, init: RequestInit = {}): Promise<Response> {
    const token = tokenStore.get();
    let res: Response;
    try {
        res = await fetch(`${API_BASE}${url}`, {
            ...init,
            headers: {
                ...(init.body ? { "Content-Type": "application/json" } : {}),
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...(init.headers || {}),
            },
        });
    } catch {
        throw new ApiError(0, "Impossible de joindre le serveur. Vérifiez votre connexion.");
    }
    if (!res.ok) {
        let body: unknown = null;
        try {
            body = await res.json();
        } catch {
            /* corps non JSON */
        }
        // Jeton expiré ou révoqué : on ferme la session
        if (res.status === 401 && token && !url.startsWith("/auth/login")) tokenStore.set(null);
        throw new ApiError(res.status, messageFrom(res.status, body), body);
    }
    return res;
}

export async function fetcher<T = unknown>(url: string, init: RequestInit = {}): Promise<T> {
    const res = await request(url, init);
    if (res.status === 204) return null as T;
    return (await res.json()) as T;
}

/** Variante qui renvoie aussi le total (en-tête X-Total-Count) pour la pagination. */
export async function fetchPage<T>(url: string): Promise<{ items: T[]; total: number }> {
    const res = await request(url);
    const items = (await res.json()) as T[];
    const total = Number(res.headers.get("X-Total-Count") ?? items.length);
    return { items, total };
}

/** Téléchargement authentifié (exports CSV/JSON). */
export async function download(url: string, fallbackName: string) {
    const res = await request(url);
    const blob = await res.blob();
    const dispo = res.headers.get("Content-Disposition") ?? "";
    const name = /filename="?([^"]+)"?/.exec(dispo)?.[1] ?? fallbackName;
    const href = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export function errorMessage(e: unknown): string {
    if (e instanceof ApiError) return e.message;
    if (e instanceof Error) return e.message;
    return "Une erreur est survenue.";
}
