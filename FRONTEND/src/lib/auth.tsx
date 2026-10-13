// src/lib/auth.tsx — session utilisateur (jeton + profil /auth/me)
"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { AuthApi } from "./api";
import { tokenStore } from "./swr";
import type { Me, Role } from "./types";

type AuthState = {
    /** false tant que le jeton n'a pas été relu depuis le stockage (évite les erreurs d'hydratation) */
    ready: boolean;
    token: string | null;
    me: Me | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<Me>;
    setSession: (token: string) => Promise<Me | undefined>;
    logout: () => void;
    refresh: () => Promise<Me | undefined>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [ready, setReady] = useState(false);
    const [token, setToken] = useState<string | null>(null);
    const { mutate: globalMutate } = useSWRConfig();

    useEffect(() => {
        setToken(tokenStore.get());
        setReady(true);
        const unsubscribe = tokenStore.subscribe(setToken);
        // Synchronise les onglets (connexion / déconnexion ailleurs)
        const onStorage = (e: StorageEvent) => e.key === "token" && setToken(e.newValue);
        window.addEventListener("storage", onStorage);
        return () => {
            unsubscribe();
            window.removeEventListener("storage", onStorage);
        };
    }, []);

    const { data, isLoading, mutate } = useSWR<Me>(token ? ["/auth/me", token] : null, () => AuthApi.me(), {
        revalidateOnFocus: true,
        shouldRetryOnError: false,
    });

    const setSession = useCallback(
        async (t: string) => {
            tokenStore.set(t);
            return mutate(AuthApi.me(), { revalidate: false });
        },
        [mutate],
    );

    const login = useCallback(
        async (email: string, password: string) => {
            const { access_token } = await AuthApi.login(email, password);
            tokenStore.set(access_token);
            const me = await AuthApi.me();
            await mutate(me, { revalidate: false });
            return me;
        },
        [mutate],
    );

    const logout = useCallback(() => {
        tokenStore.set(null);
        // Vide tout le cache SWR (données de l'ancien compte)
        globalMutate(() => true, undefined, { revalidate: false });
    }, [globalMutate]);

    const value = useMemo<AuthState>(
        () => ({
            ready,
            token,
            me: token ? (data ?? null) : null,
            isLoading: !ready || (!!token && isLoading && !data),
            login,
            setSession,
            logout,
            refresh: () => mutate(),
        }),
        [ready, token, data, isLoading, login, setSession, logout, mutate],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth doit être utilisé dans <AuthProvider>");
    return ctx;
}

/** Compatibilité avec l'ancien hook. */
export function useMe() {
    const { me, isLoading, refresh } = useAuth();
    return { me, isLoading, refresh };
}

export const isStaff = (me?: Pick<Me, "role_utilisateur"> | null) =>
    !!me && (me.role_utilisateur === "admin" || me.role_utilisateur === "moderator");

export const hasRole = (me: Me | null, allow: Role[]) => !!me && allow.includes(me.role_utilisateur);
