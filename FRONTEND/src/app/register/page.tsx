"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useState } from "react";
import { fetcher } from "@/lib/swr";

export default function RegisterPage() {
    const [form, setForm] = useState({
        nom: "",
        prenom: "",
        adresse_mail: "",
        classe: "",
        password: "",
    });
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr(null);
        setLoading(true);
        try {
            // Ici on force le rôle "user" car le backend hash déjà le mot de passe
            const payload = { ...form, role_utilisateur: "user" };

            await fetcher("/users", {
                method: "POST",
                body: JSON.stringify(payload),
            });

            setSuccess(true);
            setForm({ nom: "", prenom: "", adresse_mail: "", classe: "", password: "" });
        } catch (e: any) {
            setErr("Erreur : impossible de créer le compte (email déjà utilisé ?)");
        } finally {
            setLoading(false);
        }
    };

    if (success)
        return (
            <div className="min-h-dvh grid place-items-center p-6">
                <Card className="w-full max-w-md text-center space-y-3 p-6">
                    <h2 className="text-2xl font-semibold">Compte créé avec succès 🎉</h2>
                    <p className="text-sm text-muted-foreground">
                        Vous pouvez maintenant vous connecter avec votre adresse email et votre mot de passe.
                    </p>
                    <Button asChild className="mt-4">
                        <Link href="/login">Se connecter</Link>
                    </Button>
                </Card>
            </div>
        );

    return (
        <div className="min-h-dvh grid place-items-center p-6">
            <Card className="w-full max-w-md">
                <CardHeader>Créer un compte</CardHeader>
                <CardContent>
                    <form onSubmit={onSubmit} className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                            <Input
                                placeholder="Prénom"
                                value={form.prenom}
                                onChange={(e) => setForm({ ...form, prenom: e.target.value })}
                                required
                            />
                            <Input
                                placeholder="Nom"
                                value={form.nom}
                                onChange={(e) => setForm({ ...form, nom: e.target.value })}
                                required
                            />
                        </div>

                        <Input
                            type="email"
                            placeholder="Email"
                            value={form.adresse_mail}
                            onChange={(e) => setForm({ ...form, adresse_mail: e.target.value })}
                            required
                        />

                        <Input
                            placeholder="Classe (ex: L3-INFO-A)"
                            value={form.classe}
                            onChange={(e) => setForm({ ...form, classe: e.target.value })}
                            required
                        />

                        <Input
                            type="password"
                            placeholder="Mot de passe"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            required
                        />

                        {err && <p className="text-sm text-red-600">{err}</p>}

                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? "Création..." : "Créer le compte"}
                        </Button>
                    </form>

                    <p className="mt-3 text-sm text-muted-foreground">
                        Déjà un compte ?{" "}
                        <Link href="/login" className="underline">
                            Se connecter
                        </Link>
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}