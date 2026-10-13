"use client";

import Link from "next/link";
import { useMe } from "@/lib/auth";
import { useMounted } from "@/lib/useMounted";

export default function HomeCta() {
    const mounted = useMounted();
    const { me, isLoading } = useMe();

    if (!mounted || isLoading) {
        return (
            <div className="flex items-center justify-center gap-2">
                <span className="text-sm text-zinc-500">Chargement…</span>
            </div>
        );
    }

    if (!me) {
        return (
            <div className="flex items-center justify-center gap-4 flex-wrap">
                <Link href="/login">
                    <button className="bg-indigo-600 text-white font-medium py-2 px-5 rounded-md shadow hover:bg-indigo-700 transition">
                        Connexion
                    </button>
                </Link>
                <Link href="/register">
                    <button className="border border-zinc-300 text-zinc-700 font-medium py-2 px-5 rounded-md hover:bg-zinc-100 transition">
                        Créer un compte
                    </button>
                </Link>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center gap-3 flex-wrap text-sm text-zinc-600">
            <Link href="/dashboard">
                <button className="bg-indigo-600 text-white font-medium py-2 px-5 rounded-md shadow hover:bg-indigo-700 transition">
                    Aller au dashboard
                </button>
            </Link>
        </div>
    );
}