"use client";

import { useState } from "react";
import useSWR from "swr";
import { Trophy } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorBox, Skeleton } from "@/components/common/States";
import { SemestreSelect } from "@/components/semestres/SemestreSelect";
import { Podium } from "@/components/stats/Podium";
import { StatsApi } from "@/lib/api";
import { formatPoints, semestreLabel } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import { cn } from "@/lib/utils";

export default function ClassementPage() {
    const [semestreId, setSemestreId] = useState<number | undefined>();
    const { data, error, isLoading, mutate } = useSWR(["/stats/classement", semestreId], () => StatsApi.classement(semestreId));
    const lignes = data?.lignes ?? [];
    const moi = lignes.find((l) => l.moi);

    return (
        <div className="space-y-6">
            <PageHeader
                title="Classement"
                eyebrow={data?.semestre ? `Semestre ${semestreLabel(data.semestre)}` : undefined}
                description="Les membres les plus assidus de l'association."
                actions={<SemestreSelect value={semestreId ?? data?.semestre?.id} onChange={setSemestreId} className="w-full" />}
            />
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}

            {isLoading && !data ? (
                <Skeleton className="h-64" />
            ) : lignes.length === 0 ? (
                <EmptyState icon={<Trophy />} title="Le classement est vide" description="Aucune présence enregistrée sur ce semestre." />
            ) : (
                <>
                    <div className="mx-auto max-w-xl pt-2">
                        <Podium lignes={lignes} />
                    </div>

                    {moi && moi.rang > 3 && (
                        <a href={`#ligne-${moi.userId}`} className="border-ember/40 bg-ember/10 block rounded-xl border p-3 text-center text-sm">
                            Tu es <strong className="text-ember">#{moi.rang}</strong> avec <strong>{formatPoints(moi.points)} pts</strong> — voir ma position
                        </a>
                    )}

                    <ol className="bg-card divide-y overflow-hidden rounded-xl border">
                        {lignes.map((l) => (
                            <li
                                key={l.userId}
                                id={`ligne-${l.userId}`}
                                className={cn("flex items-center gap-3 px-3 py-3 sm:px-4", l.moi && "bg-ember/10 shadow-[inset_3px_0_0_var(--ember)]")}
                            >
                                <span
                                    className={cn(
                                        "font-display w-8 shrink-0 text-center text-lg font-bold tabular-nums",
                                        l.rang === 1 ? "text-gold" : l.rang <= 3 ? "text-foreground" : "text-muted-foreground",
                                    )}
                                >
                                    {l.rang}
                                </span>
                                <div className="min-w-0 flex-1">
                                    <p className="truncate text-sm font-medium">
                                        {l.prenom} {l.nom} {l.moi && <span className="text-ember text-xs">(toi)</span>}
                                    </p>
                                    <p className="text-muted-foreground text-xs">
                                        {l.classe} · {l.presences} présence{l.presences > 1 ? "s" : ""}
                                        {l.bonus !== 0 && <span className={l.bonus > 0 ? "text-success" : "text-destructive"}> · {l.bonus > 0 ? "+" : ""}{formatPoints(l.bonus)} bonus</span>}
                                    </p>
                                </div>
                                <span className="font-display text-gold text-base font-bold tabular-nums">{formatPoints(l.points)}</span>
                            </li>
                        ))}
                    </ol>
                </>
            )}
        </div>
    );
}
