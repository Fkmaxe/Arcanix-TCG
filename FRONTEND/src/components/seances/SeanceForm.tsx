// src/components/seances/SeanceForm.tsx — création et édition d'une séance
"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, Mail, MessageCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SeancesApi } from "@/lib/api";
import { formatDateHeure, JEUX, todayIso } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { ModePublication, Seance, SeanceInput } from "@/lib/types";
import { useConfig } from "@/lib/useConfig";
import { cn } from "@/lib/utils";
import { SemestreSelect, useSemestres } from "@/components/semestres/SemestreSelect";

type Canal = "discord" | "email";
type Choix = { mode: ModePublication; le: string }; // le : valeur d'un <input type="datetime-local">

/** ISO -> valeur locale « AAAA-MM-JJTHH:MM » pour un champ datetime-local. */
const versLocal = (iso: string) => {
    const d = new Date(iso);
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
};

/** État initial d'un canal à partir de la séance existante. */
function choixInitial(seance: Seance | undefined, canal: Canal, actifParDefaut: boolean): Choix {
    if (!seance) return { mode: actifParDefaut ? "immediat" : "jamais", le: "" };
    const le = canal === "discord" ? seance.discord_publier_le : seance.email_publier_le;
    if (!le) return { mode: "jamais", le: "" };
    if (new Date(le).getTime() > Date.now()) return { mode: "programme", le: versLocal(le) };
    return { mode: "immediat", le: "" };
}

const MODES: { value: ModePublication; label: string; labelEdition: string }[] = [
    { value: "immediat", label: "Dès la création", labelEdition: "Maintenant" },
    { value: "programme", label: "Programmer", labelEdition: "Programmer" },
    { value: "jamais", label: "Ne pas publier", labelEdition: "Ne pas publier" },
];

function LignePublication({
    canal, choix, onChange, publieLe, desactive, raison, edition,
}: {
    canal: Canal;
    choix: Choix;
    onChange: (c: Choix) => void;
    publieLe: string | null; // déjà publiée : verrouillée
    desactive?: boolean;
    raison?: string;
    edition: boolean;
}) {
    const Icon = canal === "discord" ? MessageCircle : Mail;
    const titre = canal === "discord" ? "Annonce Discord" : "Email aux membres";
    return (
        <div className="space-y-2">
            <p className="flex items-center gap-2 text-sm font-medium"><Icon className="text-gold size-4" /> {titre}</p>
            {publieLe ? (
                <p className="text-success flex items-center gap-1.5 text-sm"><CheckCircle2 className="size-4" /> Publiée le {formatDateHeure(publieLe)}</p>
            ) : desactive ? (
                <p className="text-muted-foreground text-xs">{raison}</p>
            ) : (
                <>
                    <div className="bg-muted grid grid-cols-3 rounded-lg p-1" role="radiogroup" aria-label={titre}>
                        {MODES.map((m) => (
                            <button
                                key={m.value}
                                type="button"
                                role="radio"
                                aria-checked={choix.mode === m.value}
                                onClick={() => onChange({ ...choix, mode: m.value })}
                                className={cn(
                                    "min-h-10 rounded-md px-1 text-xs font-medium transition sm:text-sm",
                                    choix.mode === m.value ? "bg-card text-gold shadow-sm" : "text-muted-foreground hover:text-foreground",
                                )}
                            >
                                {edition ? m.labelEdition : m.label}
                            </button>
                        ))}
                    </div>
                    {choix.mode === "programme" && (
                        <Input
                            type="datetime-local"
                            aria-label={`Date et heure de publication (${titre})`}
                            value={choix.le}
                            min={versLocal(new Date().toISOString())}
                            onChange={(e) => onChange({ ...choix, le: e.target.value })}
                            required
                        />
                    )}
                </>
            )}
        </div>
    );
}

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
        places_max: seance?.places_max ? String(seance.places_max) : "",
    });
    const [semestreId, setSemestreId] = useState<number | undefined>(seance?.semestre_id);
    const { smtp } = useConfig();
    const initial = { discord: choixInitial(seance, "discord", true), email: choixInitial(seance, "email", true) };
    const [publication, setPublication] = useState(initial);
    const discordPublie = seance?.annonce_envoyee ? seance.discord_publier_le : null;
    const emailPublie = seance?.email_envoye ? seance.email_publier_le : null;
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
            places_max: form.places_max ? Number(form.places_max) : null,
        };
        // Publication : en création on envoie tout ; en modification, seulement les canaux changés et non publiés
        for (const canal of ["discord", "email"] as const) {
            const c = publication[canal];
            const verrouille = canal === "discord" ? !!discordPublie : !!emailPublie || !smtp;
            const change = c.mode !== initial[canal].mode || c.le !== initial[canal].le;
            if (canal === "email" && !smtp) continue;
            if (seance && (verrouille || !change)) continue;
            body[`${canal}_mode`] = c.mode;
            body[`${canal}_le`] = c.mode === "programme" && c.le ? new Date(c.le).toISOString() : null;
        }
        setLoading(true);
        try {
            const saved = seance ? await SeancesApi.update(seance.id, body) : await SeancesApi.create(body);
            toast.success(seance ? "Séance mise à jour" : "Séance créée");
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
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="s-lieu">Lieu</Label>
                    <Input id="s-lieu" value={form.lieu} onChange={set("lieu")} placeholder="Salle B204" maxLength={150} />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="s-places">Places max</Label>
                    <Input id="s-places" type="number" inputMode="numeric" min={1} max={1000} value={form.places_max} onChange={set("places_max")} placeholder="Illimité" />
                </div>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="s-sem">Semestre</Label>
                <SemestreSelect id="s-sem" value={semestre} onChange={setSemestreId} className="sm:w-full" />
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="s-desc">Description</Label>
                <Textarea id="s-desc" value={form.description} onChange={set("description")} rows={3} maxLength={4000} placeholder="Format, matériel à apporter, inscriptions…" />
            </div>
            <fieldset className="bg-surface/60 space-y-4 rounded-lg border p-3">
                <legend className="font-display px-1 text-sm font-semibold">Publication</legend>
                <LignePublication
                    canal="discord"
                    choix={publication.discord}
                    onChange={(c) => setPublication((p) => ({ ...p, discord: c }))}
                    publieLe={discordPublie}
                    edition={!!seance}
                />
                <LignePublication
                    canal="email"
                    choix={publication.email}
                    onChange={(c) => setPublication((p) => ({ ...p, email: c }))}
                    publieLe={emailPublie}
                    desactive={!smtp}
                    raison="L'envoi d'emails n'est pas configuré sur le serveur (SMTP) : pas d'annonce par email."
                    edition={!!seance}
                />
            </fieldset>
            <Button type="submit" className="w-full" disabled={loading || !form.nom.trim() || !semestre}>
                {loading && <Loader2 className="animate-spin" />} {seance ? "Enregistrer" : "Créer la séance"}
            </Button>
        </form>
    );
}
