// src/components/seances/CalendrierSeances.tsx — vue mensuelle des séances
"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { CalendarX, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState, Skeleton } from "@/components/common/States";
import { SeancesApi } from "@/lib/api";
import { formatDate, jeuInfo, todayIso } from "@/lib/format";
import type { Seance } from "@/lib/types";
import { cn } from "@/lib/utils";
import { SeanceCard } from "./SeanceCard";

const JOURS = ["L", "M", "M", "J", "V", "S", "D"];
const iso = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** Les 6 semaines (lundi → dimanche) qui couvrent le mois affiché. */
function grille(mois: Date): Date[] {
    const premier = new Date(mois.getFullYear(), mois.getMonth(), 1);
    const decalage = (premier.getDay() + 6) % 7; // lundi = 0
    return Array.from({ length: 42 }, (_, i) => new Date(mois.getFullYear(), mois.getMonth(), 1 - decalage + i));
}

export function CalendrierSeances({ jeu }: { jeu?: string }) {
    const aujourdHui = todayIso();
    const [mois, setMois] = useState(() => {
        const d = new Date();
        return new Date(d.getFullYear(), d.getMonth(), 1);
    });
    const [jour, setJour] = useState<string | null>(aujourdHui);
    const cases = useMemo(() => grille(mois), [mois]);
    const debut = iso(cases[0]);
    const fin = iso(cases[cases.length - 1]);

    const { data, isLoading } = useSWR(["/seances", "calendrier", debut, fin, jeu], () =>
        SeancesApi.list({ dateFrom: debut, dateTo: fin, jeu, limit: 200 }),
    );
    const parJour = useMemo(() => {
        const m = new Map<string, Seance[]>();
        (data?.items ?? []).forEach((s) => m.set(s.date_seance, [...(m.get(s.date_seance) ?? []), s]));
        m.forEach((liste) => liste.sort((a, b) => (a.heure_debut ?? "").localeCompare(b.heure_debut ?? "")));
        return m;
    }, [data]);

    // En changeant de mois, on sélectionne la première date qui a une séance (ou aujourd'hui)
    useEffect(() => {
        if (!data) return;
        const prefixe = iso(mois).slice(0, 7);
        if (jour?.startsWith(prefixe) && (parJour.has(jour) || jour === aujourdHui)) return;
        const premiere = [...parJour.keys()].filter((k) => k.startsWith(prefixe)).sort()[0];
        setJour(aujourdHui.startsWith(prefixe) ? aujourdHui : (premiere ?? null));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data, mois]);

    const changerMois = (delta: number) => setMois((m) => new Date(m.getFullYear(), m.getMonth() + delta, 1));
    const titre = mois.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
    const duJour = jour ? (parJour.get(jour) ?? []) : [];

    return (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="bg-card rounded-xl border p-3 sm:p-4">
                <div className="mb-3 flex items-center justify-between">
                    <Button variant="ghost" size="icon-sm" onClick={() => changerMois(-1)} aria-label="Mois précédent">
                        <ChevronLeft />
                    </Button>
                    <button
                        className="font-display text-gilded text-lg font-bold capitalize"
                        onClick={() => {
                            const d = new Date();
                            setMois(new Date(d.getFullYear(), d.getMonth(), 1));
                            setJour(aujourdHui);
                        }}
                        title="Revenir à aujourd'hui"
                    >
                        {titre}
                    </button>
                    <Button variant="ghost" size="icon-sm" onClick={() => changerMois(1)} aria-label="Mois suivant">
                        <ChevronRight />
                    </Button>
                </div>
                <div className="text-muted-foreground grid grid-cols-7 pb-1 text-center text-xs font-semibold" aria-hidden>
                    {JOURS.map((j, i) => <span key={i}>{j}</span>)}
                </div>
                <div className={cn("grid grid-cols-7 gap-1", isLoading && !data && "opacity-50")} role="grid" aria-label={`Séances de ${titre}`}>
                    {cases.map((d) => {
                        const cle = iso(d);
                        const seances = parJour.get(cle) ?? [];
                        const horsMois = d.getMonth() !== mois.getMonth();
                        const selection = cle === jour;
                        return (
                            <button
                                key={cle}
                                role="gridcell"
                                aria-selected={selection}
                                aria-label={`${formatDate(cle, "long")}${seances.length ? `, ${seances.length} séance(s)` : ""}`}
                                onClick={() => setJour(cle)}
                                className={cn(
                                    "relative flex aspect-square flex-col items-center justify-center gap-1 rounded-lg text-sm transition lg:aspect-auto lg:h-14",
                                    horsMois ? "text-muted-foreground/40" : "text-foreground",
                                    seances.length && !selection && "bg-accent/50 font-semibold",
                                    selection ? "bg-flame font-bold text-[#1a0d05] shadow-[0_4px_14px_-4px_var(--ember)]" : "hover:bg-accent",
                                    cle === aujourdHui && !selection && "ring-gold ring-1",
                                )}
                            >
                                <span className="tabular-nums">{d.getDate()}</span>
                                {seances.length > 0 && (
                                    <span className="flex gap-0.5" aria-hidden>
                                        {seances.slice(0, 3).map((s) => (
                                            <span
                                                key={s.id}
                                                className="size-1.5 rounded-full"
                                                style={{ backgroundColor: selection ? "#1a0d05" : (jeuInfo(s.jeu)?.color ?? "var(--gold)") }}
                                            />
                                        ))}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            <div aria-live="polite">
                {jour && <h3 className="mb-3 font-sans text-base font-semibold tracking-normal first-letter:uppercase">{formatDate(jour, "long")}</h3>}
                {isLoading && !data ? (
                    <Skeleton className="h-20" />
                ) : duJour.length ? (
                    <ul className="space-y-2">
                        {duJour.map((s) => <li key={s.id}><SeanceCard seance={s} href={`/seances/${s.id}`} /></li>)}
                    </ul>
                ) : (
                    <EmptyState
                        icon={<CalendarX />}
                        title={jour ? "Aucune séance ce jour-là" : "Aucune séance ce mois-ci"}
                        description="Les jours marqués d'un point ont au moins une séance."
                        className="bg-card rounded-xl border"
                    />
                )}
            </div>
        </div>
    );
}
