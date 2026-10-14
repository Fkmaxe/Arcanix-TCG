// src/app/(protected)/dashboard/page.tsx
"use client";

import Link from "next/link";
import useSWR from "swr";
import { CalendarCheck, CalendarX, ChevronRight, Flame, MessageCircle, Percent, Shield, Trophy } from "lucide-react";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { PageHeader, SectionTitle } from "@/components/common/PageHeader";
import { EmptyState, Skeleton, StatTile } from "@/components/common/States";
import { SeanceCard } from "@/components/seances/SeanceCard";
import { Button } from "@/components/ui/button";
import { MeApi, SeancesApi } from "@/lib/api";
import { isStaff, useAuth } from "@/lib/auth";
import { formatDate, formatPoints, semestreLabel } from "@/lib/format";

export default function Dashboard() {
    const { me } = useAuth();
    const { data: stats, isLoading } = useSWR("/me/stats", () => MeApi.stats());
    const { data: prochaines } = useSWR(["/seances", "a-venir", 3], () => SeancesApi.list({ a_venir: true, limit: 3 }));
    const { data: recentes } = useSWR("/me/participations", () => MeApi.participations());

    const salut = new Date().getHours() < 18 ? "Bonjour" : "Bonsoir";

    return (
        <div className="space-y-8">
            <PageHeader
                eyebrow={stats?.semestre ? `Semestre ${semestreLabel(stats.semestre)}` : undefined}
                title={`${salut}, ${me?.prenom}`}
                description="Voici où en est ta quête ce semestre."
            />

            {/* Points du semestre */}
            <OrnateCard className="overflow-hidden">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <p className="text-muted-foreground text-xs font-semibold tracking-[0.2em] uppercase">Points du semestre</p>
                        {isLoading ? (
                            <Skeleton className="mt-2 h-14 w-32" />
                        ) : (
                            <p className="font-display text-gilded mt-1 text-6xl font-bold tabular-nums">{formatPoints(stats?.points ?? 0)}</p>
                        )}
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-center">
                            <p className="text-muted-foreground text-xs uppercase">Rang</p>
                            <p className="font-display text-3xl font-bold">
                                {stats?.hors_classement ? <span className="text-muted-foreground text-sm font-normal">Hors classement</span>
                                    : stats?.rang ? <>#{stats.rang}<span className="text-muted-foreground text-base font-normal">/{stats.nb_membres_classes}</span></> : "—"}
                            </p>
                        </div>
                        <Button asChild variant="outline">
                            <Link href="/classement"><Trophy /> Classement</Link>
                        </Button>
                    </div>
                </div>
            </OrnateCard>

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatTile icon={<CalendarCheck />} label="Présences" value={stats?.presences ?? "—"} hint={`sur ${stats?.seances_semestre ?? 0} séance(s)`} />
                <StatTile icon={<Percent />} label="Assiduité" value={stats ? `${Math.round(stats.taux_presence * 100)}%` : "—"} />
                <StatTile icon={<Flame />} label="Dernier gain" value={stats?.evolution.length ? `+${formatPoints(stats.evolution[stats.evolution.length - 1].points)}` : "—"} />
                <StatTile
                    icon={<MessageCircle />}
                    label="Discord"
                    value={me?.discord_lie ? "Lié" : "Non lié"}
                    hint={me?.discord_lie ? "Notifications actives" : <Link href="/profil#discord" className="text-gold underline">Lier mon compte</Link>}
                />
            </div>

            {isStaff(me) && (
                <Link href="/gestion" className="bg-accent/40 hover:bg-accent/70 flex items-center gap-3 rounded-xl border border-gold/30 p-4 transition">
                    <Shield className="text-gold size-6 shrink-0" />
                    <div className="min-w-0 flex-1">
                        <p className="font-semibold">Espace de gestion</p>
                        <p className="text-muted-foreground text-sm">Séances, appel, membres et exports.</p>
                    </div>
                    <ChevronRight className="text-muted-foreground" />
                </Link>
            )}

            <div className="grid gap-8 lg:grid-cols-2">
                <section>
                    <SectionTitle action={<Link href="/seances" className="text-gold text-sm hover:underline">Tout voir</Link>}>
                        Prochaines séances
                    </SectionTitle>
                    {prochaines?.items.length ? (
                        <ul className="space-y-2">
                            {prochaines.items.map((s) => <li key={s.id}><SeanceCard seance={s} href={`/seances/${s.id}`} /></li>)}
                        </ul>
                    ) : (
                        <EmptyState icon={<CalendarX />} title="Rien de prévu pour l'instant" />
                    )}
                </section>
                <section>
                    <SectionTitle action={<Link href="/profil#historique" className="text-gold text-sm hover:underline">Historique</Link>}>
                        Mes dernières séances
                    </SectionTitle>
                    {recentes?.length ? (
                        <ul className="bg-card divide-y rounded-xl border">
                            {recentes.slice(0, 5).map((p) => (
                                <li key={p.seance_id}>
                                    <Link href={`/seances/${p.seance_id}`} className="hover:bg-accent/30 flex items-center gap-3 px-4 py-3 transition">
                                        <div className="min-w-0 flex-1">
                                            <p className="truncate text-sm font-medium">{p.seance_nom}</p>
                                            <p className="text-muted-foreground text-xs">{formatDate(p.date_seance, "jour")}</p>
                                        </div>
                                        {p.present ? (
                                            <span className="text-gold font-display text-sm font-bold">+{formatPoints(p.nb_point)}</span>
                                        ) : (
                                            <span className="text-destructive text-xs">Absent</span>
                                        )}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <EmptyState title="Aucune participation pour l'instant" description="Viens à une séance pour gagner tes premiers points !" />
                    )}
                </section>
            </div>
        </div>
    );
}
