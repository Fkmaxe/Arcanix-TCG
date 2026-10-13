// src/components/seances/ResultatsTournoi.tsx — classement final d'un tournoi (+ saisie par la modération)
"use client";

import { useMemo, useState } from "react";
import { Loader2, Medal, Pencil, Plus, Trash2, Trophy } from "lucide-react";
import { toast } from "sonner";
import { SectionTitle } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SeancesApi } from "@/lib/api";
import { isStaff, useAuth } from "@/lib/auth";
import { formatPoints, libellePlace } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { ResultatInput, SeanceDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

const MEDAILLE: Record<number, string> = { 1: "text-gold", 2: "text-[#6f6f6f] dark:text-[#c9c9c9]", 3: "text-[#9a5420] dark:text-[#d9925a]" };

type Ligne = { utilisateur_id: number; nom: string; place: string; victoires: string; defaites: string; nuls: string; deck: string };

const bilan = (v: number | null, d: number | null, n: number | null) =>
    [v, d, n].some((x) => x !== null) ? [v ?? 0, d ?? 0, n].filter((x) => x !== null).join("-") : null;

function Editeur({ seance, onSaved }: { seance: SeanceDetail; onSaved: () => void }) {
    // Candidats : présents, inscrits et pointés de la séance (sans doublon)
    const candidats = useMemo(() => {
        const m = new Map<number, string>();
        seance.participants.filter((p) => p.present).forEach((p) => m.set(p.utilisateur_id, `${p.prenom} ${p.nom}`));
        seance.inscrits.forEach((i) => m.set(i.utilisateur_id, `${i.prenom} ${i.nom}`));
        seance.pointages.forEach((p) => m.set(p.utilisateur_id, `${p.prenom} ${p.nom}`));
        seance.resultats.forEach((r) => m.set(r.utilisateur_id, `${r.prenom} ${r.nom}`));
        return m;
    }, [seance]);

    const [lignes, setLignes] = useState<Ligne[]>(() =>
        seance.resultats.length
            ? seance.resultats.map((r) => ({
                  utilisateur_id: r.utilisateur_id, nom: `${r.prenom} ${r.nom}`, place: String(r.place),
                  victoires: r.victoires?.toString() ?? "", defaites: r.defaites?.toString() ?? "", nuls: r.nuls?.toString() ?? "",
                  deck: r.deck ?? "",
              }))
            : [...candidats].map(([id, nom]) => ({ utilisateur_id: id, nom, place: "", victoires: "", defaites: "", nuls: "", deck: "" })),
    );
    const [bareme, setBareme] = useState("3, 2, 1");
    const [annoncer, setAnnoncer] = useState(true);
    const [saving, setSaving] = useState(false);
    const absents = [...candidats].filter(([id]) => !lignes.some((l) => l.utilisateur_id === id));
    const maj = (i: number, k: keyof Ligne, v: string) => setLignes((ls) => ls.map((l, j) => (j === i ? { ...l, [k]: v } : l)));
    const num = (v: string) => (v.trim() === "" ? null : Number(v));

    const enregistrer = async () => {
        const resultats: ResultatInput[] = lignes
            .filter((l) => l.place.trim() !== "")
            .map((l) => ({
                utilisateur_id: l.utilisateur_id, place: Number(l.place), victoires: num(l.victoires), defaites: num(l.defaites),
                nuls: num(l.nuls), deck: l.deck.trim() || null,
            }));
        const points = bareme.split(/[,;\s]+/).filter(Boolean).map((x) => Number(x.replace(",", ".")));
        if (points.some((x) => Number.isNaN(x) || x < 0)) return toast.error("Barème invalide : ex. « 3, 2, 1 »");
        setSaving(true);
        try {
            await SeancesApi.enregistrerResultats(seance.id, resultats, points, annoncer);
            toast.success(resultats.length ? "Résultats enregistrés — bonus de podium attribués" : "Résultats effacés");
            onSaved();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-4">
            <p className="text-muted-foreground text-sm">Renseigne la place finale (vide = non classé). Les ex æquo peuvent partager une place.</p>
            <ul className="space-y-2">
                {lignes.map((l, i) => (
                    <li key={l.utilisateur_id} className="bg-surface/60 rounded-lg border p-3">
                        <div className="mb-2 flex items-center justify-between gap-2">
                            <span className="truncate text-sm font-medium">{l.nom}</span>
                            <Button size="icon-sm" variant="ghost" aria-label={`Retirer ${l.nom}`} onClick={() => setLignes((ls) => ls.filter((_, j) => j !== i))}>
                                <Trash2 />
                            </Button>
                        </div>
                        <div className="text-muted-foreground mb-1 grid grid-cols-4 gap-2 text-[11px] font-semibold uppercase" aria-hidden>
                            <span>Place</span><span>Victoires</span><span>Défaites</span><span>Nuls</span>
                        </div>
                        <div className="grid grid-cols-4 gap-2">
                            <Input aria-label="Place" placeholder="–" type="number" inputMode="numeric" min={1} value={l.place} onChange={(e) => maj(i, "place", e.target.value)} />
                            <Input aria-label="Victoires" placeholder="–" type="number" inputMode="numeric" min={0} value={l.victoires} onChange={(e) => maj(i, "victoires", e.target.value)} />
                            <Input aria-label="Défaites" placeholder="–" type="number" inputMode="numeric" min={0} value={l.defaites} onChange={(e) => maj(i, "defaites", e.target.value)} />
                            <Input aria-label="Nuls" placeholder="–" type="number" inputMode="numeric" min={0} value={l.nuls} onChange={(e) => maj(i, "nuls", e.target.value)} />
                        </div>
                        <Input className="mt-2" aria-label="Deck" placeholder="Deck joué (optionnel)" maxLength={120} value={l.deck} onChange={(e) => maj(i, "deck", e.target.value)} />
                    </li>
                ))}
            </ul>
            {absents.length > 0 && (
                <Select
                    value=""
                    onValueChange={(v) => {
                        const id = Number(v);
                        setLignes((ls) => [...ls, { utilisateur_id: id, nom: candidats.get(id) ?? `#${id}`, place: "", victoires: "", defaites: "", nuls: "", deck: "" }]);
                    }}
                >
                    <SelectTrigger aria-label="Ajouter un joueur"><Plus className="size-4" /><SelectValue placeholder="Ajouter un joueur" /></SelectTrigger>
                    <SelectContent>
                        {absents.map(([id, nom]) => <SelectItem key={id} value={String(id)}>{nom}</SelectItem>)}
                    </SelectContent>
                </Select>
            )}
            <div className="space-y-1.5">
                <Label htmlFor="bareme">Bonus par place (1re, 2e, 3e…)</Label>
                <Input id="bareme" value={bareme} onChange={(e) => setBareme(e.target.value)} placeholder="3, 2, 1" />
                <p className="text-muted-foreground text-xs">Ajoutés automatiquement au classement du semestre, recalculés à chaque modification.</p>
            </div>
            <label className="flex items-center gap-2 text-sm">
                <Checkbox checked={annoncer} onCheckedChange={(v) => setAnnoncer(!!v)} /> Annoncer les résultats sur Discord
            </label>
            <Button className="w-full" onClick={enregistrer} disabled={saving}>
                {saving && <Loader2 className="animate-spin" />} Enregistrer les résultats
            </Button>
        </div>
    );
}

export function ResultatsTournoi({ seance, onSaved }: { seance: SeanceDetail; onSaved: () => void }) {
    const { me } = useAuth();
    const [edition, setEdition] = useState(false);
    const staff = isStaff(me);
    if (!seance.resultats.length && !staff) return null;

    return (
        <section>
            <SectionTitle
                action={staff && (
                    <Button size="sm" variant="outline" onClick={() => setEdition(true)}>
                        {seance.resultats.length ? <><Pencil /> Modifier les résultats</> : <><Trophy /> Saisir les résultats</>}
                    </Button>
                )}
            >
                Résultats
            </SectionTitle>
            {seance.resultats.length ? (
                <ol className="bg-card divide-y overflow-hidden rounded-xl border">
                    {seance.resultats.map((r) => (
                        <li key={r.utilisateur_id} className={cn("flex items-center gap-3 px-3 py-3 sm:px-4", r.moi && "bg-ember/10")}>
                            <span className={cn("font-display w-10 shrink-0 text-center text-lg font-bold", MEDAILLE[r.place] ?? "text-muted-foreground")}>
                                {r.place <= 3 ? <Medal className="mx-auto size-6" aria-label={libellePlace(r.place)} /> : libellePlace(r.place)}
                            </span>
                            <div className="min-w-0 flex-1">
                                <p className="truncate text-sm font-medium">{r.prenom} {r.nom} {r.moi && <span className="text-ember text-xs">(toi)</span>}</p>
                                <p className="text-muted-foreground truncate text-xs">
                                    {[bilan(r.victoires, r.defaites, r.nuls), r.deck].filter(Boolean).join(" · ") || "—"}
                                </p>
                            </div>
                            {r.bonus > 0 && <span className="text-gold font-display text-sm font-bold">+{formatPoints(r.bonus)}</span>}
                        </li>
                    ))}
                </ol>
            ) : (
                <p className="text-muted-foreground text-sm">Aucun résultat saisi. Pour un tournoi, saisis le classement final : les bonus de podium seront attribués automatiquement.</p>
            )}
            <Dialog open={edition} onOpenChange={setEdition}>
                <DialogContent className="sm:max-w-xl">
                    <DialogHeader>
                        <DialogTitle>Résultats du tournoi</DialogTitle>
                        <DialogDescription>{seance.nom}</DialogDescription>
                    </DialogHeader>
                    {edition && <Editeur seance={seance} onSaved={() => { setEdition(false); onSaved(); }} />}
                </DialogContent>
            </Dialog>
        </section>
    );
}
