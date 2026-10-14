"use client";

import Link from "next/link";
import { useState } from "react";
import { Loader2, MailCheck, MessageCircle } from "lucide-react";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthApi } from "@/lib/api";
import { completerEmail } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import { useConfig } from "@/lib/useConfig";

export default function MotDePasseOubliePage() {
    const { smtp, charge, domaine } = useConfig();
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [envoye, setEnvoye] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr(null);
        setLoading(true);
        try {
            const adresse = completerEmail(email, domaine);
            setEmail(adresse);
            await AuthApi.motDePasseOublie(adresse);
            setEnvoye(true);
        } catch (e) {
            setErr(errorMessage(e));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mx-auto flex min-h-[calc(100dvh-8rem)] max-w-md flex-col justify-center py-6">
            <OrnateCard>
                <h1 className="text-gilded mb-2 text-center text-2xl font-bold">Mot de passe oublié</h1>
                {envoye ? (
                    <div className="space-y-3 text-center">
                        <MailCheck className="text-success mx-auto size-12" />
                        <p>Si un compte existe pour <strong>{email}</strong>, un lien vient d&apos;y être envoyé.</p>
                        <p className="text-muted-foreground text-sm">Pense à regarder dans les spams. Le lien est valable 48 h.</p>
                        <Button asChild variant="outline" className="mt-2"><Link href="/login">Retour à la connexion</Link></Button>
                    </div>
                ) : charge && !smtp ? (
                    <div className="text-muted-foreground space-y-3 text-center text-sm">
                        <MessageCircle className="text-gold mx-auto size-10" />
                        <p>Sur le Discord de l&apos;association, tape <code className="text-gold">/reinitialiser</code> : le bot t&apos;enverra un lien privé.</p>
                        <p>Pas de Discord ? Demande un lien à un membre de la modération.</p>
                        <Button asChild variant="outline" className="mt-2"><Link href="/login">Retour à la connexion</Link></Button>
                    </div>
                ) : (
                    <form onSubmit={submit} className="space-y-4">
                        <p className="text-muted-foreground text-center text-sm">Indique ton email : tu recevras un lien pour choisir un nouveau mot de passe.</p>
                        <div className="space-y-1.5">
                            <Label htmlFor="email">Email</Label>
                            <Input id="email" type="text" inputMode="email" autoCapitalize="none" spellCheck={false} value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" autoFocus placeholder="j.dupont ou ton email" />
                        </div>
                        {err && <p className="text-destructive text-sm" role="alert">{err}</p>}
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading && <Loader2 className="animate-spin" />} Envoyer le lien
                        </Button>
                        <p className="text-muted-foreground text-center text-xs">
                            Aussi possible sur Discord avec <code className="text-gold">/reinitialiser</code>.
                        </p>
                    </form>
                )}
            </OrnateCard>
        </div>
    );
}
