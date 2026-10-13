"use client";

import { useState } from "react";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MeApi } from "@/lib/api";
import { errorMessage } from "@/lib/swr";

export function PasswordInput(props: React.ComponentProps<typeof Input>) {
    const [visible, setVisible] = useState(false);
    return (
        <div className="relative">
            <Input {...props} type={visible ? "text" : "password"} className="pr-11" />
            <button
                type="button"
                onClick={() => setVisible((v) => !v)}
                className="text-muted-foreground hover:text-foreground absolute inset-y-0 right-0 grid w-11 place-items-center"
                aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            >
                {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
        </div>
    );
}

/** Changement de mot de passe (avec ou sans l'ancien). */
export function PasswordForm({
    requireCurrent = true,
    onDone,
    submitLabel = "Mettre à jour le mot de passe",
}: {
    requireCurrent?: boolean;
    onDone?: () => void;
    submitLabel?: string;
}) {
    const [current, setCurrent] = useState("");
    const [next, setNext] = useState("");
    const [confirm, setConfirm] = useState("");
    const [loading, setLoading] = useState(false);
    const mismatch = confirm.length > 0 && next !== confirm;

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (next !== confirm) return;
        setLoading(true);
        try {
            await MeApi.changePassword(next, requireCurrent ? current : undefined);
            toast.success("Mot de passe mis à jour");
            setCurrent("");
            setNext("");
            setConfirm("");
            onDone?.();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-3">
            {requireCurrent && (
                <div className="space-y-1.5">
                    <Label htmlFor="pwd-current">Mot de passe actuel</Label>
                    <PasswordInput id="pwd-current" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" />
                </div>
            )}
            <div className="space-y-1.5">
                <Label htmlFor="pwd-new">Nouveau mot de passe</Label>
                <PasswordInput id="pwd-new" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} autoComplete="new-password" />
                <p className="text-muted-foreground text-xs">8 caractères minimum.</p>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="pwd-confirm">Confirmation</Label>
                <PasswordInput
                    id="pwd-confirm"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    aria-invalid={mismatch}
                />
                {mismatch && <p className="text-destructive text-xs">Les mots de passe ne correspondent pas.</p>}
            </div>
            <Button type="submit" className="w-full" disabled={loading || mismatch || next.length < 8}>
                {loading && <Loader2 className="animate-spin" />} {submitLabel}
            </Button>
        </form>
    );
}
