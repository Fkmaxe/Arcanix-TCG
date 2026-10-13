// src/components/points/AjustementForm.tsx — bonus / malus de points motivé
"use client";

import { useState } from "react";
import { Loader2, Minus, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MembrePicker, type MembreChoisi } from "@/components/users/MembrePicker";
import { SemestreSelect, useSemestres } from "@/components/semestres/SemestreSelect";
import { AjustementsApi } from "@/lib/api";
import { CATEGORIES, formatSigne } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { Categorie } from "@/lib/types";
import { cn } from "@/lib/utils";

export function AjustementForm({ membre, onSuccess }: { membre?: MembreChoisi; onSuccess: () => void }) {
    const { actif } = useSemestres();
    const [cible, setCible] = useState<MembreChoisi | null>(membre ?? null);
    const [sens, setSens] = useState<1 | -1>(1);
    const [valeur, setValeur] = useState("1");
    const [motif, setMotif] = useState("");
    const [categorie, setCategorie] = useState<Categorie>("organisation");
    const [semestreId, setSemestreId] = useState<number | undefined>();
    const [loading, setLoading] = useState(false);
    const points = sens * Number(valeur.replace(",", "."));

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!cible) return toast.error("Choisis un membre");
        setLoading(true);
        try {
            await AjustementsApi.create({ utilisateur_id: cible.id, points, motif: motif.trim(), categorie, semestre_id: semestreId ?? actif?.id });
            toast.success(`${formatSigne(points)} pts pour ${cible.prenom} ${cible.nom}`);
            onSuccess();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
                <Label htmlFor="aj-membre">Membre</Label>
                <MembrePicker id="aj-membre" value={cible} onChange={setCible} />
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="aj-points">Points</Label>
                <div className="flex gap-2">
                    <div className="bg-muted inline-flex shrink-0 rounded-lg p-1" role="radiogroup" aria-label="Type">
                        {([[1, "Bonus", Plus], [-1, "Malus", Minus]] as const).map(([v, label, Icon]) => (
                            <button
                                key={label}
                                type="button"
                                role="radio"
                                aria-checked={sens === v}
                                onClick={() => {
                                    setSens(v);
                                    if (v === -1 && categorie === "organisation") setCategorie("penalite");
                                    if (v === 1 && categorie === "penalite") setCategorie("organisation");
                                }}
                                className={cn(
                                    "flex items-center gap-1 rounded-md px-3 text-sm font-medium transition",
                                    sens === v ? (v === 1 ? "bg-success text-white" : "bg-destructive text-white") : "text-muted-foreground",
                                )}
                            >
                                <Icon className="size-4" /> {label}
                            </button>
                        ))}
                    </div>
                    <Input id="aj-points" type="number" inputMode="decimal" min={0.5} max={100} step={0.5} value={valeur} onChange={(e) => setValeur(e.target.value)} required />
                </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                    <Label htmlFor="aj-cat">Catégorie</Label>
                    <Select value={categorie} onValueChange={(v) => setCategorie(v as Categorie)}>
                        <SelectTrigger id="aj-cat"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {Object.entries(CATEGORIES).map(([v, c]) => <SelectItem key={v} value={v}>{c.emoji} {c.label}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="aj-sem">Semestre</Label>
                    <SemestreSelect id="aj-sem" value={semestreId ?? actif?.id} onChange={setSemestreId} className="sm:w-full" />
                </div>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="aj-motif">Motif</Label>
                <Textarea id="aj-motif" value={motif} onChange={(e) => setMotif(e.target.value)} required minLength={3} maxLength={300} rows={2}
                    placeholder={sens === 1 ? "Aide au rangement après le tournoi" : "Absence non excusée à un tournoi inscrit"} />
                <p className="text-muted-foreground text-xs">Visible par le membre sur son profil et inscrit au journal.</p>
            </div>
            <Button type="submit" className="w-full" disabled={loading || !cible || !(points !== 0) || motif.trim().length < 3}>
                {loading && <Loader2 className="animate-spin" />} {Number.isFinite(points) && points !== 0 ? `Appliquer ${formatSigne(points)} pts` : "Appliquer"}
            </Button>
        </form>
    );
}
