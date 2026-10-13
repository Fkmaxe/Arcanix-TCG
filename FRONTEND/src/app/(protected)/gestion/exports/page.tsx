"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { FileJson, FileSpreadsheet, ListChecks, Loader2, Users } from "lucide-react";
import { toast } from "sonner";
import { DataTable } from "@/components/common/DataTable";
import { PageHeader, SectionTitle } from "@/components/common/PageHeader";
import { ErrorBox, StatTile } from "@/components/common/States";
import { SemestreSelect, useSemestres } from "@/components/semestres/SemestreSelect";
import { Button } from "@/components/ui/button";
import { StatsApi } from "@/lib/api";
import { formatPoints } from "@/lib/format";
import { errorMessage } from "@/lib/swr";

export default function ExportsPage() {
    const { actif } = useSemestres();
    const [choix, setChoix] = useState<number | undefined>();
    const semestreId = choix ?? actif?.id;
    const { data = [], error, isLoading, mutate } = useSWR(semestreId ? ["/stats/points", semestreId] : null, () => StatsApi.points(semestreId));
    const [busy, setBusy] = useState<string | null>(null);

    const stats = useMemo(() => {
        const actifs = data.filter((p) => p.presences > 0);
        const pts = actifs.map((p) => p.points);
        return {
            membres: data.length,
            actifs: actifs.length,
            moyenne: pts.length ? pts.reduce((a, b) => a + b, 0) / pts.length : 0,
            max: pts.length ? Math.max(...pts) : 0,
        };
    }, [data]);

    const run = async (key: string, fn: () => Promise<void>) => {
        setBusy(key);
        try {
            await fn();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setBusy(null);
        }
    };

    const boutons = [
        { key: "csv", label: "Points (CSV)", icon: FileSpreadsheet, fn: () => StatsApi.exportPointsCsv(semestreId) },
        { key: "json", label: "Points (JSON)", icon: FileJson, fn: () => StatsApi.exportPointsJson(semestreId) },
        { key: "part", label: "Présences détaillées (CSV)", icon: ListChecks, fn: () => StatsApi.exportParticipationsCsv(semestreId) },
    ];

    return (
        <div className="space-y-6">
            <PageHeader
                eyebrow="Gestion"
                title="Exports"
                description="Points et présences par semestre, prêts pour Excel."
                actions={<SemestreSelect value={semestreId} onChange={setChoix} className="w-full" />}
            />
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatTile icon={<Users />} label="Membres" value={stats.membres} />
                <StatTile label="Actifs" value={stats.actifs} />
                <StatTile label="Moyenne (actifs)" value={formatPoints(Math.round(stats.moyenne * 10) / 10)} />
                <StatTile label="Maximum" value={formatPoints(stats.max)} />
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
                {boutons.map(({ key, label, icon: Icon, fn }) => (
                    <Button key={key} variant="outline" disabled={!semestreId || !!busy} onClick={() => run(key, fn)}>
                        {busy === key ? <Loader2 className="animate-spin" /> : <Icon />} {label}
                    </Button>
                ))}
            </div>
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}
            <section>
                <SectionTitle>Aperçu</SectionTitle>
                <DataTable
                    isLoading={isLoading}
                    rows={data}
                    rowKey={(r) => r.userId}
                    empty="Aucun membre"
                    mobileCard={(r) => (
                        <div className="bg-card flex items-center gap-3 rounded-xl border p-3">
                            <span className="font-display text-muted-foreground w-7 text-center font-bold">{r.rang}</span>
                            <div className="min-w-0 flex-1">
                                <p className="truncate text-sm font-medium">{r.prenom} {r.nom}</p>
                                <p className="text-muted-foreground text-xs">{r.classe} · {r.presences} présence(s)</p>
                            </div>
                            <span className="text-gold font-display font-bold">{formatPoints(r.points)}</span>
                        </div>
                    )}
                    columns={[
                        { key: "rang", header: "Rang", render: (r) => <span className="font-display font-bold">#{r.rang}</span> },
                        { key: "nom", header: "Nom", render: (r) => `${r.nom} ${r.prenom}` },
                        { key: "classe", header: "Classe", render: (r) => r.classe },
                        { key: "presences", header: "Présences", render: (r) => r.presences },
                        { key: "bonus", header: "Bonus/malus", render: (r) => (r.bonus ? <span className={r.bonus > 0 ? "text-success" : "text-destructive"}>{r.bonus > 0 ? "+" : ""}{formatPoints(r.bonus)}</span> : "—") },
                        { key: "points", header: "Points", render: (r) => <span className="text-gold font-semibold">{formatPoints(r.points)}</span> },
                    ]}
                />
            </section>
        </div>
    );
}
