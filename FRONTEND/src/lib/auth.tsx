// src/lib/auth.ts
"use client";

import useSWR, { useSWRConfig, SWRResponse } from "swr";
import { fetcher } from "./swr";
import { Token } from "./types";
import { atom, useAtom } from "jotai";
import { useRouter } from "next/navigation";

/**
 * Token global (initialisé depuis localStorage côté client)
 */
export const tokenAtom = atom<string | null>(
    typeof window !== "undefined" ? localStorage.getItem("token") : null
);
export const meAtom = atom<any | null>(null);

/**
 * Fetcher qui prend une clé tuple [url, token] pour attacher l'Authorization
 */
async function fetcherAuth([url, token]: [string, string]) {
    return fetcher(url, {
        headers: { Authorization: `Bearer ${token}` },
    });
}

/**
 * Hook de login
 */
export function useLogin() {
    const { mutate } = useSWRConfig();
    const [, setToken] = useAtom(tokenAtom);

    const login = async (email: string, password: string) => {
        const data = await fetcher("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        const parsed = Token.parse(data);
        // Persiste + met à jour l’état global
        localStorage.setItem("token", parsed.access_token);
        setToken(parsed.access_token);

        // Revalide immédiatement /auth/me
        await mutate(["/auth/me", parsed.access_token]);

        // Optionnel : navigation ici ou dans la page
        // router.replace("/");

        return parsed;
    };

    return { login };
}

/**
 * Récupération du profil, réactive au token
 */
export function useMe(): {
    me: any | null;
    isLoading: boolean;
    error: unknown;
    refresh: SWRResponse["mutate"];
} {
    const [token] = useAtom(tokenAtom);

    // Pas de token -> pas d’appel
    const { data, error, isLoading, mutate } = useSWR(
        token ? ["/auth/me", token] : null,
        fetcherAuth,
        { revalidateOnFocus: false }
    );

    return { me: data ?? null, isLoading, error, refresh: mutate };
}

/**
 * Déconnexion propre : nettoie token + cache SWR
 */
export function useAuth() {
    const router = useRouter();
    const { mutate } = useSWRConfig();
    const [, setToken] = useAtom(tokenAtom);

    const logout = async () => {
        // Retire token
        localStorage.removeItem("token");
        setToken(null);

        // Vide /auth/me côté cache (immédiat pour l’UI)
        await mutate(["/auth/me", undefined as unknown as string], null, false);
        await mutate("/auth/me", null, false); // au cas où d’autres endroits l’aient utilisé sans tuple

        // Navigation
        router.replace("/login");
    };

    return { logout };
}

/**
 * Gate simple sur les rôles
 */
export function RoleGate({
                             allow,
                             children,
                         }: {
    allow: ("user" | "moderator" | "admin")[];
    children: React.ReactNode;
}) {
    const { me, isLoading } = useMe();
    if (isLoading) return null;
    if (!me || !allow.includes(me.role_utilisateur)) return null;
    return <>{children}</>;
}