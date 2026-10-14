// src/components/seances/AppelPresence.tsx — appel de présence rapide (modération)
"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { Check, CheckCheck, Hourglass, Loader2, MessageCircle, QrCode, RotateCcw, Search, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SeancesApi, UsersApi } from "@/lib/api";
import { initials, classeOuExterne } from "@/lib/format";
import { useDebounced } from "@/lib/hooks";
import { errorMessage } from "@/lib/swr";
import type { SeanceDetail, User } from "@/lib/types";
import { cn } from "@/lib/utils";

type Etat = "present" | "absent";
type Membre = Pick<User, "id" | "nom" | "prenom" | "classe"> & { discord_lie?: boolean };

export function AppelPresence({ seance, onSaved }: { seance: SeanceDetail; onSaved: (s: SeanceDetail) => void }) {
    const initial = useMemo(
        () => new Map<number, Etat>(seance.participants.map((p) => [p.utilisateur_id, p.present ? "present" : "absent"])),
        [seance.participants],
    );
    // Inscrits (« Je viens ») et pointés par QR code : pré-remplis dans l'appel
    const inscrits = useMemo(() => new Map(seance.inscrits.map((i) => [i.utilisateur_id, i.statut])), [seance.inscrits]);
    const pointes = useMemo(() => new Set(seance.pointages.map((p) => p.utilisateur_id)), [seance.pointages]);
    // État de départ : l'appel enregistré + les pointés QR cochés présents (à valider)
    const depart = useMemo(() => {
        const m = new Map(initial);
        pointes.forEach((id) => {
            if (!m.has(id)) m.set(id, "present");
        });
        return m;
    }, [initial, pointes]);
    const aValider = [...pointes].filter((id) => !initial.has(id)).length;
    const concernes = useMemo(
        () => new Set([...initial.keys(), ...inscrits.keys(), ...pointes]),
        [initial, inscrits, pointes],
    );

    const [etats, setEtats] = useState(depart);
    const [query, setQuery] = useState("");
    const [filtre, setFiltre] = useState<"inscrits" | "tous">(concernes.size ? "inscrits" : "tous");
    const [saving, setSaving] = useState(false);
    const q = useDebounced(query.trim(), 250);

    useEffect(() => setEtats(depart), [depart]);

    // Annuaire des membres (recherche côté serveur, 200 max par page)
    const { data, isLoading } = useSWR(["/users", "appel", q], () => UsersApi.list({ q, limit: 200 }));
    const annuaire = useMemo(() => data?.items ?? [], [data]);

    const membres: Membre[] = useMemo(() => {
        const parId = new Map<number, Membre>();
        [...seance.participants, ...seance.inscrits, ...seance.pointages].forEach((p) =>
            parId.set(p.utilisateur_id, { id: p.utilisateur_id, nom: p.nom, prenom: p.prenom, classe: p.classe, discord_lie: p.discord_lie }),
        );
        annuaire.forEach((u) => parId.set(u.id, { ...parId.get(u.id), ...u, discord_lie: !!u.discord_id }));
        let liste = [...parId.values()];
        // Les inscrits d'origine restent affichés même décochés : un mauvais tap se corrige sur place
        if (filtre === "inscrits" && !q) liste = liste.filter((m) => etats.has(m.id) || concernes.has(m.id));
        if (q) {
            const needle = q.toLowerCase();
            liste = liste.filter((m) => `${m.prenom} ${m.nom} ${classeOuExterne(m)}`.toLowerCase().includes(needle));
        }
        return liste.sort((a, b) => a.prenom.localeCompare(b.prenom, "fr") || a.nom.localeCompare(b.nom, "fr"));
    }, [seance.participants, seance.inscrits, seance.pointages, annuaire, filtre, q, etats, concernes]);

    const presents = [...etats.values()].filter((e) => e === "present").length;
    const dirty =
        etats.size !== initial.size || [...etats].some(([id, e]) => initial.get(id) !== e);

    const setEtat = (id: number, e: Etat | null) =>
        setEtats((prev) => {
            const next = new Map(prev);
            if (e) next.set(id, e);
            else next.delete(id);
            return next;
        });

    const tousPresents = () =>
        setEtats((prev) => {
            const next = new Map(prev);
            membres.forEach((m) => next.set(m.id, "present"));
            return next;
        });

    const save = async () => {
        setSaving(true);
        try {
            const res = await SeancesApi.appel(
                seance.id,
                [...etats].map(([utilisateur_id, e]) => ({ utilisateur_id, present: e === "present" })),
            );
            toast.success(`Appel enregistré · ${res.nb_presents} présent${res.nb_presents > 1 ? "s" : ""}`);
            onSaved(res);
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-3">
            <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                    <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                    <Input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Chercher un membre, une classe…"
                        className="pl-9"
                        type="search"
                        enterKeyHint="search"
                    />
                </div>
                <div className="bg-muted inline-flex h-11 shrink-0 rounded-lg p-1 sm:h-10" role="tablist">
                    {(["inscrits", "tous"] as const).map((f) => (
                        <button
                            key={f}
                            role="tab"
                            aria-selected={filtre === f}
                            onClick={() => setFiltre(f)}
                            className={cn(
                                "flex-1 rounded-md px-3 text-sm font-medium transition",
                                filtre === f ? "bg-card text-gold shadow-sm" : "text-muted-foreground",
                            )}
                        >
                            {f === "inscrits" ? `Séance (${new Set([...concernes, ...etats.keys()]).size})` : "Tous les membres"}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex items-center justify-between gap-2 text-sm">
                <span className="text-muted-foreground">
                    <strong className="text-success">{presents}</strong> présent{presents > 1 ? "s" : ""} ·{" "}
                    <strong className="text-destructive">{etats.size - presents}</strong> absent{etats.size - presents > 1 ? "s" : ""}
                </span>
                <div className="flex gap-1">
                    {/* Jamais sur l'annuaire complet : seulement les inscrits ou le résultat d'une recherche */}
                    {(filtre === "inscrits" || q) && (
                        <Button variant="ghost" size="sm" onClick={tousPresents} disabled={!membres.length}>
                            <CheckCheck /> {q ? "Cocher la sélection" : "Tous présents"}
                        </Button>
                    )}
                    {dirty && (
                        <Button variant="ghost" size="icon-sm" onClick={() => setEtats(depart)} aria-label="Revenir à l'état de départ">
                            <RotateCcw />
                        </Button>
                    )}
                </div>
            </div>

            <ul className="bg-card divide-y overflow-hidden rounded-xl border">
                {isLoading && !membres.length && (
                    <li className="text-muted-foreground flex items-center gap-2 p-4 text-sm"><Loader2 className="size-4 animate-spin" /> Chargement des membres…</li>
                )}
                {!isLoading && !membres.length && (
                    <li className="text-muted-foreground p-6 text-center text-sm">
                        {filtre === "inscrits" && !q ? "Personne n'est encore inscrit : passez sur « Tous les membres »." : "Aucun membre trouvé."}
                    </li>
                )}
                {membres.map((m) => {
                    const etat = etats.get(m.id);
                    return (
                        <li key={m.id} className={cn("flex items-center gap-3 px-3 py-2.5 transition", etat === "present" && "bg-success/5")}>
                            <div
                                className={cn(
                                    "grid size-9 shrink-0 place-items-center rounded-full text-xs font-bold",
                                    etat === "present" ? "bg-success/20 text-success" : etat === "absent" ? "bg-destructive/15 text-destructive" : "bg-muted text-muted-foreground",
                                )}
                            >
                                {initials(m.prenom, m.nom)}
                            </div>
                            <div className="min-w-0 flex-1">
                                <p className="truncate text-sm font-medium">{m.prenom} {m.nom}</p>
                                <p className="text-muted-foreground flex items-center gap-1.5 truncate text-xs">
                                    {classeOuExterne(m)}
                                    {m.discord_lie && <MessageCircle className="size-3" aria-label="Discord lié" />}
                                    {!etat && initial.has(m.id) && <span className="text-destructive">· sera retiré de la séance</span>}
                                    {pointes.has(m.id) && (
                                        <span className="text-success inline-flex items-center gap-0.5" title="A pointé avec le QR code">
                                            <QrCode className="size-3" /> pointé
                                        </span>
                                    )}
                                    {inscrits.get(m.id) === "inscrit" && !pointes.has(m.id) && <span className="text-gold">· inscrit</span>}
                                    {inscrits.get(m.id) === "attente" && (
                                        <span className="text-muted-foreground inline-flex items-center gap-0.5"><Hourglass className="size-3" /> attente</span>
                                    )}
                                </p>
                            </div>
                            <div className="flex shrink-0 items-center gap-1" role="group" aria-label={`Présence de ${m.prenom} ${m.nom}`}>
                                <button
                                    onClick={() => setEtat(m.id, etat === "present" ? null : "present")}
                                    aria-pressed={etat === "present"}
                                    className={cn(
                                        "grid size-11 place-items-center rounded-lg border transition sm:size-10",
                                        etat === "present" ? "border-success bg-success text-white" : "hover:border-success/60 hover:text-success text-muted-foreground",
                                    )}
                                    aria-label="Présent"
                                    title="Présent"
                                >
                                    <Check className="size-5" />
                                </button>
                                <button
                                    onClick={() => setEtat(m.id, etat === "absent" ? null : "absent")}
                                    aria-pressed={etat === "absent"}
                                    className={cn(
                                        "grid size-11 place-items-center rounded-lg border transition sm:size-10",
                                        etat === "absent" ? "border-destructive bg-destructive text-white" : "hover:border-destructive/60 hover:text-destructive text-muted-foreground",
                                    )}
                                    aria-label="Absent"
                                    title="Absent (inscrit mais non venu)"
                                >
                                    <X className="size-5" />
                                </button>
                            </div>
                        </li>
                    );
                })}
            </ul>

            {/* Barre d'enregistrement collante, au-dessus de la barre d'onglets mobile */}
            <div
                className={cn(
                    "sticky bottom-[calc(4.5rem+env(safe-area-inset-bottom))] z-30 transition md:bottom-4",
                    dirty ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-2 opacity-0",
                )}
            >
                <div className="bg-popover/95 flex items-center justify-between gap-3 rounded-xl border p-2 pl-4 shadow-2xl backdrop-blur">
                    <span className="text-sm">
                        {aValider > 0 && [...pointes].some((id) => !initial.has(id) && etats.get(id) === "present")
                            ? `${aValider} pointage${aValider > 1 ? "s" : ""} QR à valider`
                            : "Modifications non enregistrées"}
                    </span>
                    <Button onClick={save} disabled={saving}>
                        {saving && <Loader2 className="animate-spin" />} Enregistrer l&apos;appel
                    </Button>
                </div>
            </div>
        </div>
    );
}
