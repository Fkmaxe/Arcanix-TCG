"use client";

import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useLogin, useMe } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const { login } = useLogin();
    const { me, isLoading } = useMe();           // 👈 état d’auth
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    // 🔒 Déjà connecté ? -> on renvoie vers l’accueil
    useEffect(() => {
        if (!isLoading && me) {
            router.replace("/");
        }
    }, [isLoading, me, router]);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (loading) return;
        setErr(null);
        setLoading(true);
        try {
            await login(email, password);
            setPassword("");
            router.push("/");          // ✅ après login -> accueil
        } catch {
            setErr("Email ou mot de passe incorrect.");
        } finally {
            setLoading(false);
        }
    };

    // Évite le flash si on est en train de déterminer l’état d’auth
    if (isLoading || me) return null;

    return (
        <div className="min-h-dvh grid place-items-center p-6">
            <Card className="w-full max-w-md">
                <CardHeader>Connexion</CardHeader>
                <CardContent>
                    <form onSubmit={onSubmit} className="space-y-3">
                        <Input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoComplete="username"
                        />
                        <Input
                            type="password"
                            placeholder="Mot de passe"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                        />
                        {err && <p className="text-sm text-red-600">{err}</p>}
                        <Button className="w-full" type="submit" disabled={loading}>
                            {loading ? "Connexion..." : "Se connecter"}
                        </Button>
                    </form>

                    <p className="mt-4 text-sm text-center text-muted-foreground">
                        Pas encore de compte ?{" "}
                        <Link href="/register" className="underline text-primary hover:text-primary/80">
                            Créer un compte
                        </Link>
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}