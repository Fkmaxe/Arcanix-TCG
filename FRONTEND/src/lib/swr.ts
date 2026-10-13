// src/lib/swr.ts
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://api.arcanix-tcg.fr";

export function authHeaders() {
    if (typeof window === "undefined") return {};
    const t = localStorage.getItem("token");
    return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function fetcher(url: string, init: RequestInit = {}) {
    const base = API_BASE;
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const res = await fetch(`${base}${url}`, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(init.headers || {}),
        },
    });

    if (!res.ok) {
        const text = await res.text();
        // Log utile pour comprendre un 4xx/5xx
        console.error(`[API ERROR] ${res.status} ${url}`, text);
        throw new Error(text || `HTTP ${res.status}`);
    }
    // PATCH /users/:id/password renvoie 204 : pas de JSON à parser
    return res.status === 204 ? null : res.json();
}