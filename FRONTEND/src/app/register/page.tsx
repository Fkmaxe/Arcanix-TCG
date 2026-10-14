"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, MessageCircle } from "lucide-react";
import { toast } from "sonner";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { PasswordInput } from "@/components/common/PasswordForm";
import { SchoolEmailField, StatutChoix } from "@/components/common/SchoolEmailField";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { errorMessage } from "@/lib/swr";

export default function RegisterPage() {
    const router = useRouter();
    const { login } = useAuth();
    const [form, setForm] = useState({ prenom: "", nom: "", adresse_mail: "", classe: "", password: "" });
    const [externe, setExterne] = useState(false);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr(null);
        setLoading(true);
        try {
            await AuthApi.register({
                ...form,
                adresse_mail: form.adresse_mail.trim(),
                externe,
                classe: externe ? null : form.classe.trim(),
            });
            await login(form.adresse_mail.trim(), form.password);
            toast.success(`Bienvenue dans l'association, ${form.prenom} !`);
            router.replace("/dashboard");
        } catch (e) {
            setErr(errorMessage(e));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mx-auto flex min-h-[calc(100dvh-8rem)] max-w-md flex-col justify-center py-6">
            <OrnateCard>
                <div className="mb-6 text-center">
                    <h1 className="text-gilded text-2xl font-bold">Rejoindre Arcanix</h1>
                    <p className="text-muted-foreground mt-1 text-sm">Crée ton compte pour suivre tes points.</p>
                </div>
                <form onSubmit={onSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                            <Label htmlFor="prenom">Prénom</Label>
                            <Input id="prenom" value={form.prenom} onChange={set("prenom")} required maxLength={100} autoComplete="given-name" />
                        </div>
                        <div className="space-y-1.5">
                            <Label htmlFor="nom">Nom</Label>
                            <Input id="nom" value={form.nom} onChange={set("nom")} required maxLength={100} autoComplete="family-name" />
                        </div>
                    </div>
                    <div className="space-y-1.5">
                        <Label>Je suis…</Label>
                        <StatutChoix
                            externe={externe}
                            onChange={(v) => {
                                setExterne(v);
                                setForm((f) => ({ ...f, adresse_mail: "" }));
                            }}
                        />
                    </div>
                    {externe ? (
                        <div className="space-y-1.5">
                            <Label htmlFor="mail">Email</Label>
                            <Input id="mail" type="email" inputMode="email" value={form.adresse_mail} onChange={set("adresse_mail")} required autoComplete="email" placeholder="ton.adresse@exemple.fr" />
                            <p className="text-muted-foreground text-xs">Membre extérieur à l&apos;école : n&apos;importe quelle adresse, pas de classe.</p>
                        </div>
                    ) : (
                        <>
                            <div className="space-y-1.5">
                                <Label htmlFor="mail">Adresse de l&apos;école</Label>
                                <SchoolEmailField id="mail" value={form.adresse_mail} onChange={(v) => setForm((f) => ({ ...f, adresse_mail: v }))} required />
                            </div>
                            <div className="space-y-1.5">
                                <Label htmlFor="classe">Classe</Label>
                                <Input id="classe" value={form.classe} onChange={set("classe")} required maxLength={50} placeholder="ex. 3A-INFO" />
                            </div>
                        </>
                    )}
                    <div className="space-y-1.5">
                        <Label htmlFor="pwd">Mot de passe</Label>
                        <PasswordInput id="pwd" value={form.password} onChange={set("password")} required minLength={8} autoComplete="new-password" />
                        <p className="text-muted-foreground text-xs">8 caractères minimum.</p>
                    </div>
                    {err && <p className="text-destructive text-sm" role="alert">{err}</p>}
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading && <Loader2 className="animate-spin" />} Créer mon compte
                    </Button>
                </form>
                <div className="bg-muted/60 mt-6 flex gap-3 rounded-lg p-3 text-sm">
                    <MessageCircle className="text-gold mt-0.5 size-4 shrink-0" />
                    <p className="text-muted-foreground">
                        Tu es sur le Discord ? Tape <code className="text-gold">/register</code> : ton compte sera lié automatiquement.
                    </p>
                </div>
                <p className="text-muted-foreground mt-4 text-center text-sm">
                    Déjà un compte ? <Link href="/login" className="text-gold font-medium hover:underline">Se connecter</Link>
                </p>
            </OrnateCard>
        </div>
    );
}
