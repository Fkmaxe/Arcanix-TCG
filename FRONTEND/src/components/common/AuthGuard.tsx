// src/components/common/AuthGuard.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMe } from "@/lib/auth";
import { Loader2 } from "lucide-react";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const { me, isLoading, error } = useMe();
    const router = useRouter();

    // si on n'est pas connecté et qu'on a fini de charger, on redirige
    useEffect(() => {
        if (!isLoading && !me) {
            router.replace("/login");
        }
    }, [isLoading, me, router]);

    if (isLoading) {
        return (
            <div className="min-h-dvh flex items-center justify-center text-muted-foreground">
                <Loader2 className="animate-spin mr-2" /> Vérification de la session…
            </div>
        );
    }

    // si pas connecté : retour vide le temps que la redirection se fasse
    if (!me) return null;

    return <>{children}</>;
}