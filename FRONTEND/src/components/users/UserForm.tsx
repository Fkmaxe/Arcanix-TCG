// src/components/users/UserForm.tsx — création / édition d'un membre (modération)
"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PasswordInput } from "@/components/common/PasswordForm";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfig } from "@/lib/useConfig";
import { UsersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { Role, User } from "@/lib/types";

export default function UserForm({ user, onSuccess }: { user?: User; onSuccess: () => void }) {
    const { me } = useAuth();
    const admin = me?.role_utilisateur === "admin";
    const [form, setForm] = useState({
        nom: user?.nom ?? "",
        prenom: user?.prenom ?? "",
        adresse_mail: user?.adresse_mail ?? "",
        classe: user?.classe ?? "",
        role_utilisateur: (user?.role_utilisateur ?? "user") as Role,
        password: "",
    });
    const [loading, setLoading] = useState(false);
    const { smtp } = useConfig();
    const [invitation, setInvitation] = useState(true);
    const parEmail = !user && smtp && invitation;
    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const { password, ...profil } = form;
            if (user) {
                await UsersApi.update(user.id, admin ? profil : { ...profil, role_utilisateur: undefined });
                if (password) await UsersApi.setPassword(user.id, password);
                toast.success("Membre mis à jour");
            } else {
                if (parEmail) {
                    await UsersApi.create({ ...profil, envoyer_invitation: true });
                    toast.success(`Invitation envoyée à ${profil.adresse_mail}`);
                } else {
                    await UsersApi.create({ ...profil, password });
                    toast.success("Membre créé — il devra choisir son mot de passe à la première connexion");
                }
            }
            onSuccess();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="u-prenom">Prénom</Label>
                    <Input id="u-prenom" value={form.prenom} onChange={set("prenom")} required maxLength={100} autoComplete="off" />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="u-nom">Nom</Label>
                    <Input id="u-nom" value={form.nom} onChange={set("nom")} required maxLength={100} autoComplete="off" />
                </div>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="u-mail">Email</Label>
                <Input id="u-mail" type="email" value={form.adresse_mail} onChange={set("adresse_mail")} required autoComplete="off" />
            </div>
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="u-classe">Classe</Label>
                    <Input id="u-classe" value={form.classe} onChange={set("classe")} required maxLength={50} placeholder="3A-INFO" />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="u-role">Rôle</Label>
                    <Select
                        value={form.role_utilisateur}
                        onValueChange={(v) => setForm((f) => ({ ...f, role_utilisateur: v as Role }))}
                        disabled={!admin}
                    >
                        <SelectTrigger id="u-role"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {(["user", "moderator", "admin"] as Role[]).map((r) => (
                                <SelectItem key={r} value={r}>{ROLE_LABELS[r]}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>
            {!user && smtp && (
                <label className="bg-surface/60 flex items-start gap-3 rounded-lg border p-3 text-sm">
                    <Checkbox checked={invitation} onCheckedChange={(v) => setInvitation(!!v)} className="mt-0.5" />
                    <span>
                        <span className="font-medium">Envoyer une invitation par email</span>
                        <span className="text-muted-foreground block text-xs">Le membre choisira lui-même son mot de passe (lien valable 48 h).</span>
                    </span>
                </label>
            )}
            {!parEmail && (
            <div className="space-y-1.5">
                <Label htmlFor="u-pwd">{user ? "Nouveau mot de passe provisoire" : "Mot de passe provisoire"}</Label>
                <PasswordInput
                    id="u-pwd"
                    value={form.password}
                    onChange={set("password")}
                    required={!user && !parEmail}
                    minLength={8}
                    autoComplete="new-password"
                    placeholder={user ? "Laisser vide pour ne pas changer" : "8 caractères minimum"}
                />
                <p className="text-muted-foreground text-xs">Le membre devra le remplacer à sa prochaine connexion.</p>
            </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
                {loading && <Loader2 className="animate-spin" />} {user ? "Enregistrer" : "Créer le membre"}
            </Button>
        </form>
    );
}
