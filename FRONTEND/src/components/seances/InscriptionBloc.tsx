// src/components/seances/InscriptionBloc.tsx — « Je viens » sur la page d'une séance
"use client";

import Link from "next/link";
import { useState } from "react";
import { CheckCircle2, Hourglass, Loader2, LogIn, Users, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { SeancesApi } from "@/lib/api";
import { isStaff, useAuth } from "@/lib/auth";
import { todayIso, classeOuExterne } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { SeanceDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

export function InscriptionBloc({ seance, onChange }: { seance: SeanceDetail; onChange: () => void }) {
    const { me } = useAuth();
    const [loading, setLoading] = useState(false);
    if (seance.date_seance < todayIso()) return null;

    const { places_max: places, nb_inscrits: inscrits, nb_attente: attente, mon_inscription: statut } = seance;
    const complet = places !== null && inscrits >= places;
    const ratio = places ? Math.min(1, inscrits / places) : 0;

    const agir = async (fn: () => Promise<{ statut: string | null }>) => {
        setLoading(true);
        try {
            const r = await fn();
            if (r.statut === "inscrit") toast.success("C'est noté, à bientôt !");
            else if (r.statut === "attente") toast.info("Séance complète : tu es en liste d'attente, tu seras prévenu·e si une place se libère.");
            else toast.success("Désinscription prise en compte");
            onChange();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-card space-y-3 rounded-xl border p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                    <p className="flex items-center gap-2 font-semibold">
                        <Users className="text-gold size-4" />
                        {inscrits} inscrit{inscrits > 1 ? "s" : ""}
                        {places ? <span className="text-muted-foreground font-normal">/ {places} places</span> : null}
                        {complet && <span className="text-ember text-xs font-bold uppercase">complet</span>}
                    </p>
                    {attente > 0 && <p className="text-muted-foreground text-xs">{attente} en liste d&apos;attente</p>}
                </div>
                {!me ? (
                    <Button asChild variant="outline" size="sm">
                        <Link href={`/login?next=/seances/${seance.id}`}><LogIn /> Se connecter pour s&apos;inscrire</Link>
                    </Button>
                ) : statut ? (
                    <Button variant="outline" disabled={loading} onClick={() => agir(() => SeancesApi.desinscrire(seance.id))}>
                        {loading && <Loader2 className="animate-spin" />}
                        {statut === "attente" ? "Quitter la liste d'attente" : "Je ne viens plus"}
                    </Button>
                ) : (
                    <Button disabled={loading} onClick={() => agir(() => SeancesApi.inscrire(seance.id))}>
                        {loading && <Loader2 className="animate-spin" />}
                        {complet ? "Rejoindre la liste d'attente" : "✋ Je viens"}
                    </Button>
                )}
            </div>
            {places ? (
                <div className="bg-muted h-2 overflow-hidden rounded-full" role="progressbar" aria-valuenow={inscrits} aria-valuemax={places} aria-label="Places occupées">
                    <div className={cn("h-full rounded-full transition-all", complet ? "bg-ember" : "bg-flame")} style={{ width: `${ratio * 100}%` }} />
                </div>
            ) : null}
            {statut === "inscrit" && (
                <p className="text-success flex items-center gap-1.5 text-sm"><CheckCircle2 className="size-4" /> Tu es inscrit·e à cette séance.</p>
            )}
            {statut === "attente" && (
                <p className="text-gold flex items-center gap-1.5 text-sm"><Hourglass className="size-4" /> Tu es en liste d&apos;attente.</p>
            )}

            {isStaff(me) && seance.inscrits.length > 0 && (
                <details className="group">
                    <summary className="text-gold cursor-pointer text-sm font-medium select-none">Voir les inscrits ({seance.inscrits.length})</summary>
                    <ul className="mt-2 divide-y rounded-lg border">
                        {seance.inscrits.map((i) => (
                            <li key={i.utilisateur_id} className="flex items-center gap-2 px-3 py-2 text-sm">
                                <span className="min-w-0 flex-1 truncate">{i.prenom} {i.nom} <span className="text-muted-foreground text-xs">· {classeOuExterne(i)}</span></span>
                                {i.statut === "attente" && <span className="text-gold text-xs">attente</span>}
                                <Button
                                    size="icon-sm"
                                    variant="ghost"
                                    aria-label={`Retirer ${i.prenom} ${i.nom} des inscrits`}
                                    onClick={async () => {
                                        try {
                                            await SeancesApi.retirerInscription(seance.id, i.utilisateur_id);
                                            toast.success(`${i.prenom} retiré·e des inscrits`);
                                            onChange();
                                        } catch (err) {
                                            toast.error(errorMessage(err));
                                        }
                                    }}
                                >
                                    <X />
                                </Button>
                            </li>
                        ))}
                    </ul>
                </details>
            )}
        </div>
    );
}
