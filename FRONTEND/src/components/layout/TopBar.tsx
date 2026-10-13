"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth, useMe } from "@/lib/auth";
import { useEffect, useState } from "react";

export default function TopBar() {
    const { logout } = useAuth();
    const { me, isLoading } = useMe();

    const [mounted, setMounted] = useState(false);
    useEffect(() => setMounted(true), []);

    const handleLogout = async () => {
        await logout(); // Redirection déjà gérée dans useAuth()
    };

    const GuestLinks = () => (
        <>
            <Link href="/login" className="text-sm text-zinc-700 hover:text-indigo-600 transition">Connexion</Link>
            <Link href="/register" className="text-sm text-zinc-700 hover:text-indigo-600 transition">Créer un compte</Link>
        </>
    );

    const rightContent =
        !mounted || isLoading ? (
            <GuestLinks />
        ) : me ? (
            <>
        <span className="text-sm text-zinc-700">
            <strong>{me.prenom}</strong>
        </span>
                <Button
                    onClick={handleLogout}
                    className="bg-red-500 text-white text-sm hover:bg-red-600 px-3 py-1 rounded-md"
                >
                    Déconnexion
                </Button>
            </>
        ) : (
            <GuestLinks />
        );

    return (
        <header className="fixed top-0 inset-x-0 z-50 bg-white/70 backdrop-blur border-b border-zinc-200">
            <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
                <Link href="/" className="text-lg font-semibold text-zinc-800 hover:text-indigo-600 transition">
                    Arcanix
                </Link>

                <nav className="flex items-center gap-4">
                    <Link href="/dashboard" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                        Dashboard
                    </Link>
                    <Link href="/me" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                        Mon espace
                    </Link>

                    {(me?.role_utilisateur === "moderator" || me?.role_utilisateur === "admin") && (
                        <Link href="/mod/seances" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                            Séances
                        </Link>
                    )}
                    {me?.role_utilisateur === "admin" && (
                        <>
                            <Link href="/admin/users" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                                Utilisateurs
                            </Link>
                            <Link href="/admin/semestres" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                                Semestres
                            </Link>
                        </>
                    )}
                    {(me?.role_utilisateur === "moderator" || me?.role_utilisateur === "admin") && (
                        <Link href="/exports" className="text-sm text-zinc-700 hover:text-indigo-600 transition">
                            Exports
                        </Link>
                    )}

                    <div className="flex items-center gap-3">{rightContent}</div>
                </nav>
            </div>
        </header>
    );
}