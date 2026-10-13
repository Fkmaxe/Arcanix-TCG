// src/components/common/AuthGuard.tsx
"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { KeyRound, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { Button } from "@/components/ui/button";
import { hasRole, useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";
import { FullPageLoader } from "./States";
import { PasswordForm } from "./PasswordForm";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const { me, ready, token, isLoading, refresh } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (ready && !token) router.replace(`/login?next=${encodeURIComponent(pathname || "/dashboard")}`);
    }, [ready, token, router, pathname]);

    if (!ready || isLoading || (token && !me)) return <FullPageLoader label="Vérification de la session…" />;
    if (!me) return null;

    // Compte créé par la modération ou réinitialisé : mot de passe à choisir
    if (me.doit_changer_mdp) {
        return (
            <div className="mx-auto max-w-md py-6">
                <OrnateCard>
                    <div className="mb-4 flex items-center gap-3">
                        <KeyRound className="text-gold size-6" />
                        <h1 className="text-gilded text-xl font-bold">Choisissez votre mot de passe</h1>
                    </div>
                    <p className="text-muted-foreground mb-4 text-sm">
                        Bienvenue {me.prenom} ! Avant de continuer, définissez un mot de passe personnel.
                    </p>
                    <PasswordForm requireCurrent={false} submitLabel="Valider et continuer" onDone={() => refresh()} />
                </OrnateCard>
            </div>
        );
    }

    return <>{children}</>;
}

export function AccessDenied() {
    return (
        <div className="mx-auto max-w-md py-10 text-center">
            <ShieldAlert className="text-ember mx-auto mb-3 size-12" />
            <h1 className="text-gilded text-2xl font-bold">Accès réservé</h1>
            <p className="text-muted-foreground mt-2">Cette salle du château est réservée à la modération de l&apos;association.</p>
            <Button asChild variant="outline" className="mt-6">
                <Link href="/dashboard">Retour à l&apos;accueil</Link>
            </Button>
        </div>
    );
}

export function RequireRole({ allow, children }: { allow: Role[]; children: React.ReactNode }) {
    const { me, isLoading } = useAuth();
    if (isLoading) return <FullPageLoader />;
    if (!hasRole(me, allow)) return <AccessDenied />;
    return <>{children}</>;
}
