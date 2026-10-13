// src/components/seances/SeanceForm.tsx — création et édition d'une séance
"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SeancesApi } from "@/lib/api";
import { JEUX, todayIso } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { Seance, SeanceInput } from "@/lib/types";
import { SemestreSelect, useSemestres } from "@/components/semestres/SemestreSelect";

export default function SeanceForm({ seance, onSuccess }: { seance?: Seance; onSuccess: (s: Seance) => void }) {
    const { actif } = useSemestres();
    const [form, setForm] = useState({
        nom: seance?.nom ?? "",
        date_seance: seance?.date_seance ?? todayIso(),
        heure_debut: seance?.heure_debut?.slice(0, 5) ?? "",
        lieu: seance?.lieu ?? "",
        jeu: seance?.jeu ?? "",
        description: seance?.description ?? "",
        nb_point: String(seance?.nb_point ?? 1),
    });
    const [semestreId, setSemestreId] = useState<number | undefined>(seance?.semestre_id);
    const [loading, setLoading] = useState(false);
    const semestre = semestreId ?? actif?.id;
    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setForm((f) => ({ ...f, [k]: e.target.value }));

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!semestre) return toast.error("Créez d'abord un semestre.");
        const body: SeanceInput = {
            nom: form.nom.trim(),
            date_seance: form.date_seance,
            heure_debut: form.heure_debut || null,
            lieu: form.lieu.trim() || null,
            jeu: form.jeu || null,
            description: form.description.trim() || null,
            nb_point: Number(form.nb_point.replace(",", ".")),
            semestre_id: semestre,
        };
        setLoading(true);
        try {
            const saved = seance ? await SeancesApi.update(seance.id, body) : await SeancesApi.create(body);
            toast.success(seance ? "Séance mise à jour" : "Séance créée — elle sera annoncée sur Discord");
            onSuccess(saved);
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
                <Label htmlFor="s-nom">Nom</Label>
                <Input id="s-nom" value={form.nom} onChange={set("nom")} placeholder="Tournoi Pokémon, soirée draft…" required maxLength={150} />
            </div>
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="s-date">Date</Label>
                    <Input id="s-date" type="date" value={form.date_seance} onChange={set("date_seance")} required />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="s-heure">Heure</Label>
                    <Input id="s-heure" type="time" value={form.heure_debut} onChange={set("heure_debut")} />
                </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="s-jeu">Jeu</Label>
                    <Select value={form.jeu || "aucun"} onValueChange={(v) => setForm((f) => ({ ...f, jeu: v === "aucun" ? "" : v }))}>
                        <SelectTrigger id="s-jeu"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="aucun">Non précisé</SelectItem>
                            {JEUX.map((j) => <SelectItem key={j.value} value={j.value}>{j.label}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="s-pts">Points</Label>
                    <Input id="s-pts" type="number" inputMode="decimal" min={0} max={9999} step={0.5} value={form.nb_point} onChange={set("nb_point")} required />
                </div>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="s-lieu">Lieu</Label>
                <Input id="s-lieu" value={form.lieu} onChange={set("lieu")} placeholder="Salle B204" maxLength={150} />
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="s-sem">Semestre</Label>
                <SemestreSelect id="s-sem" value={semestre} onChange={setSemestreId} className="sm:w-full" />
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="s-desc">Description</Label>
                <Textarea id="s-desc" value={form.description} onChange={set("description")} rows={3} maxLength={4000} placeholder="Format, matériel à apporter, inscriptions…" />
            </div>
            <Button type="submit" className="w-full" disabled={loading || !form.nom.trim() || !semestre}>
                {loading && <Loader2 className="animate-spin" />} {seance ? "Enregistrer" : "Créer la séance"}
            </Button>
        </form>
    );
}
