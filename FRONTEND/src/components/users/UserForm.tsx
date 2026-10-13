// src/components/users/UserForm.tsx
"use client";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UsersApi } from "@/lib/api";

export default function UserForm({ onSuccess }: { onSuccess: () => void }) {
    const [form, setForm] = useState({
        nom: "",
        prenom: "",
        adresse_mail: "",
        classe: "",
        role_utilisateur: "user",
        password: "",               // <-- NEW
    });
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErr(null);
        setLoading(true);
        try {
            // L’API hash le mot de passe côté serveur
            await UsersApi.create(form as any); // POST /users : { ..., password }
            setForm({...form, password: ""});
            onSuccess();
        } catch (e:any) {
            setErr("Impossible de créer l’utilisateur");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-3">
            <Input placeholder="Nom" value={form.nom} onChange={e=>setForm({...form, nom:e.target.value})} required minLength={1}/>
            <Input placeholder="Prénom" value={form.prenom} onChange={e=>setForm({...form, prenom:e.target.value})} required minLength={1}/>
            <Input type="email" placeholder="Email" value={form.adresse_mail} onChange={e=>setForm({...form, adresse_mail:e.target.value})} required/>
            <Input placeholder="Classe" value={form.classe} onChange={e=>setForm({...form, classe:e.target.value})} required minLength={1}/>
            <Select value={form.role_utilisateur} onValueChange={(v)=>setForm({...form, role_utilisateur:v})} required>
                <SelectTrigger><SelectValue placeholder="Rôle" /></SelectTrigger>
                <SelectContent>
                    <SelectItem value="user">user</SelectItem>
                    <SelectItem value="moderator">moderator</SelectItem>
                    <SelectItem value="admin">admin</SelectItem>
                </SelectContent>
            </Select>
            <Input
                type="password"
                placeholder="Mot de passe initial"
                value={form.password}
                onChange={e=>setForm({...form, password:e.target.value})}
                required
                minLength={8}
                autoComplete="new-password"
            />
            {err && <p className="text-sm text-red-600">{err}</p>}
            <Button type="submit" className="w-full" disabled={loading || form.password.length < 8}>
                {loading ? "Création…" : "Enregistrer"}
            </Button>
        </form>
    );
}