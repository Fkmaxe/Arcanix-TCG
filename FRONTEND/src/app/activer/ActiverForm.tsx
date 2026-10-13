"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { KeyRound, Loader2, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { PasswordInput } from "@/components/common/PasswordForm";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { AuthApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { errorMessage } from "@/lib/swr";

export default function ActiverForm() {
    const jeton = useSearchParams().get("jeton") ?? "";
    const { setSession } = useAuth();
    const router = useRouter();
    const [pwd, setPwd] = useState("");
    const [confirm, setConfirm] = useState("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const mismatch = confirm.length > 0 && pwd !== confirm;

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (pwd !== confirm) return;
        setErr(null);
        setLoading(true);
        try {
            const { access_token } = await AuthApi.definirMotDePasse(jeton, pwd);
            const me = await setSession(access_token);
            toast.success(me ? `Bienvenue ${me.prenom} ! Ton compte est prêt.` : "Mot de passe enregistré");
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
                {!jeton ? (
                    <div className="text-center">
                        <TriangleAlert className="text-ember mx-auto mb-3 size-10" />
                        <h1 className="text-gilded text-xl font-bold">Lien incomplet</h1>
                        <p className="text-muted-foreground mt-2 text-sm">
                            Ouvre le lien reçu sur Discord en entier, ou demande-en un nouveau avec <code className="text-gold">/reinitialiser</code>.
                        </p>
                        <Button asChild variant="outline" className="mt-6"><Link href="/login">Retour à la connexion</Link></Button>
                    </div>
                ) : (
                    <>
                        <div className="mb-6 flex flex-col items-center text-center">
                            <KeyRound className="text-gold mb-2 size-8" />
                            <h1 className="text-gilded text-2xl font-bold">Choisis ton mot de passe</h1>
                            <p className="text-muted-foreground mt-1 text-sm">Il te servira à te connecter sur le site.</p>
                        </div>
                        <form onSubmit={submit} className="space-y-4">
                            <div className="space-y-1.5">
                                <Label htmlFor="pwd">Mot de passe</Label>
                                <PasswordInput id="pwd" value={pwd} onChange={(e) => setPwd(e.target.value)} required minLength={8} autoComplete="new-password" autoFocus />
                                <p className="text-muted-foreground text-xs">8 caractères minimum.</p>
                            </div>
                            <div className="space-y-1.5">
                                <Label htmlFor="confirm">Confirmation</Label>
                                <PasswordInput id="confirm" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} autoComplete="new-password" aria-invalid={mismatch} />
                                {mismatch && <p className="text-destructive text-xs">Les mots de passe ne correspondent pas.</p>}
                            </div>
                            {err && <p className="text-destructive text-sm" role="alert">{err}</p>}
                            <Button type="submit" className="w-full" disabled={loading || mismatch || pwd.length < 8}>
                                {loading && <Loader2 className="animate-spin" />} Valider
                            </Button>
                        </form>
                    </>
                )}
            </OrnateCard>
        </div>
    );
}
