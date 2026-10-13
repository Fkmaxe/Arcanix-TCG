// src/components/users/UserEditForm.tsx
"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UsersApi } from "@/lib/api";

export default function UserEditForm({
                                         user,
                                         onSuccess,
                                     }: {
    user: any;
    onSuccess: () => void;
}) {
    const [form, setForm] = useState({
        nom: user.nom ?? "",
        prenom: user.prenom ?? "",
        adresse_mail: user.adresse_mail ?? "",
        classe: user.classe ?? "",
        role_utilisateur: user.role_utilisateur ?? "user",
        new_password: "", // optionnel : si rempli, on fera un call password
    });
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr(null);
        setLoading(true);
        try {
            // 1) PATCH /users/{id} pour les champs “profil”
            await UsersApi.update(user.id, {
                nom: form.nom,
                prenom: form.prenom,
                adresse_mail: form.adresse_mail,
                classe: form.classe,
                role_utilisateur: form.role_utilisateur,
            });

            // 2) Changer le MDP si saisi
            if (form.new_password.trim().length > 0) {
                await UsersApi.changePassword(user.id, form.new_password.trim());
            }

            onSuccess();
        } catch (e: any) {
            setErr("Impossible de mettre à jour l’utilisateur");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
                <Input placeholder="Nom" value={form.nom} onChange={e=>setForm({...form, nom:e.target.value})}/>
                <Input placeholder="Prénom" value={form.prenom} onChange={e=>setForm({...form, prenom:e.target.value})}/>
            </div>
            <Input type="email" placeholder="Email" value={form.adresse_mail} onChange={e=>setForm({...form, adresse_mail:e.target.value})}/>
            <div className="grid grid-cols-2 gap-3">
                <Input placeholder="Classe" value={form.classe} onChange={e=>setForm({...form, classe:e.target.value})}/>
                <Select value={form.role_utilisateur} onValueChange={(v)=>setForm({...form, role_utilisateur:v})}>
                    <SelectTrigger><SelectValue placeholder="Rôle" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="user">user</SelectItem>
                        <SelectItem value="moderator">moderator</SelectItem>
                        <SelectItem value="admin">admin</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <Input
                type="password"
                placeholder="Nouveau mot de passe (laisser vide pour ne pas changer)"
                value={form.new_password}
                onChange={e=>setForm({...form, new_password:e.target.value})}
                autoComplete="new-password"
            />

            {err && <p className="text-sm text-red-600">{err}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Enregistrement…" : "Enregistrer"}
            </Button>
        </form>
    );
}