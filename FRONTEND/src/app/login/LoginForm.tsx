"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { PasswordInput } from "@/components/common/PasswordForm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { errorMessage } from "@/lib/swr";

/** N'autorise que les redirections internes (pas d'open redirect). */
export const safeNext = (n: string | null) => (n && n.startsWith("/") && !n.startsWith("//") ? n : "/dashboard");

export default function LoginForm() {
    const { login, me, ready } = useAuth();
    const router = useRouter();
    const next = safeNext(useSearchParams().get("next"));
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        if (ready && me) router.replace(next);
    }, [ready, me, router, next]);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (loading) return;
        setErr(null);
        setLoading(true);
        try {
            await login(email.trim(), password);
            router.replace(next);
        } catch (e) {
            setErr(errorMessage(e));
            setPassword("");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mx-auto flex min-h-[calc(100dvh-8rem)] max-w-md flex-col justify-center py-6">
            <OrnateCard>
                <div className="mb-6 flex flex-col items-center text-center">
                    <Image src="/brand/carte-192.png" alt="" width={56} height={56} className="animate-flicker" />
                    <h1 className="text-gilded mt-3 text-2xl font-bold">Connexion</h1>
                    <p className="text-muted-foreground mt-1 text-sm">Heureux de te revoir, aventurier.</p>
                </div>
                <form onSubmit={onSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" inputMode="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" autoFocus />
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="password">Mot de passe</Label>
                        <PasswordInput id="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
                    </div>
                    {err && <p className="text-destructive text-sm" role="alert">{err}</p>}
                    <Button className="w-full" type="submit" disabled={loading}>
                        {loading && <Loader2 className="animate-spin" />} Se connecter
                    </Button>
                </form>
                <div className="text-muted-foreground mt-6 space-y-2 text-center text-sm">
                    <p>
                        Pas encore de compte ? <Link href="/register" className="text-gold font-medium hover:underline">Créer un compte</Link>
                    </p>
                    <p className="text-xs">
                        Mot de passe oublié ? Sur le Discord, tape <code className="text-gold">/reinitialiser</code> ou demande à la modération.
                    </p>
                </div>
            </OrnateCard>
        </div>
    );
}
