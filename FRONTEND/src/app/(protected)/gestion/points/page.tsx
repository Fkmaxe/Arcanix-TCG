"use client";

import { Suspense } from "react";
import { useState } from "react";
import useSWR from "swr";
import { useSearchParams } from "next/navigation";
import { Plus, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { DataTable, Pagination } from "@/components/common/DataTable";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorBox } from "@/components/common/States";
import { AjustementForm } from "@/components/points/AjustementForm";
import { SemestreSelect } from "@/components/semestres/SemestreSelect";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AjustementsApi } from "@/lib/api";
import { CATEGORIES, formatDateHeure, formatSigne, semestreLabel } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { Ajustement } from "@/lib/types";
import { cn } from "@/lib/utils";

const LIMIT = 25;

function Points({ a }: { a: Ajustement }) {
    return (
        <span className={cn("font-display text-base font-bold tabular-nums", a.points > 0 ? "text-success" : "text-destructive")}>
            {formatSigne(a.points)}
        </span>
    );
}

function PointsContenu() {
    const userId = Number(useSearchParams().get("membre")) || undefined;
    const [semestreId, setSemestreId] = useState<number | undefined>();
    const [categorie, setCategorie] = useState("toutes");
    const [page, setPage] = useState(1);
    const [creer, setCreer] = useState(false);
    const params = { semestreId, userId, categorie: categorie === "toutes" ? undefined : categorie, page, limit: LIMIT };
    const { data, error, isLoading, mutate } = useSWR(["/ajustements", params], () => AjustementsApi.list(params));

    const supprimer = async (a: Ajustement) => {
        try {
            await AjustementsApi.remove(a.id);
            toast.success("Ajustement annulé");
            mutate();
        } catch (err) {
            toast.error(errorMessage(err));
        }
    };
    const actions = (a: Ajustement) =>
        a.categorie === "tournoi" && a.seance_id ? (
            <span className="text-muted-foreground text-xs">via résultats</span>
        ) : (
            <ConfirmButton title="Annuler cet ajustement ?" description={`${formatSigne(a.points)} pts pour ${a.prenom} ${a.nom} : « ${a.motif} »`} confirmLabel="Annuler l'ajustement" onConfirm={() => supprimer(a)}>
                <Button size="icon-sm" variant="ghost" className="text-destructive" aria-label="Annuler l'ajustement"><Trash2 /></Button>
            </ConfirmButton>
        );

    return (
        <div className="space-y-5">
            <PageHeader
                eyebrow="Gestion"
                title="Bonus & malus"
                description="Points hors séance : aide à l'organisation, podiums, pénalités… toujours avec un motif."
                actions={<Button onClick={() => setCreer(true)} className="w-full sm:w-auto"><Plus /> Nouvel ajustement</Button>}
            />
            <div className="flex flex-col gap-2 sm:flex-row">
                <SemestreSelect value={semestreId} onChange={(v) => { setSemestreId(v); setPage(1); }} allowAll />
                <Select value={categorie} onValueChange={(v) => { setCategorie(v); setPage(1); }}>
                    <SelectTrigger className="sm:w-56" aria-label="Catégorie"><SelectValue /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="toutes">Toutes les catégories</SelectItem>
                        {Object.entries(CATEGORIES).map(([v, c]) => <SelectItem key={v} value={v}>{c.emoji} {c.label}</SelectItem>)}
                    </SelectContent>
                </Select>
            </div>
            {userId && data?.items[0] && (
                <p className="text-muted-foreground text-sm">Filtré sur <strong className="text-foreground">{data.items[0].prenom} {data.items[0].nom}</strong></p>
            )}
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}
            <DataTable
                isLoading={isLoading}
                rows={data?.items ?? []}
                rowKey={(a) => a.id}
                empty="Aucun bonus ni malus"
                emptyIcon={<Sparkles />}
                mobileCard={(a) => (
                    <div className="bg-card flex items-start gap-3 rounded-xl border p-3">
                        <Points a={a} />
                        <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">{a.prenom} {a.nom}</p>
                            <p className="text-sm">{CATEGORIES[a.categorie]?.emoji} {a.motif}</p>
                            <p className="text-muted-foreground text-xs">{formatDateHeure(a.cree_le)} · {a.cree_par ?? "—"} · {semestreLabel(a.semestre)}</p>
                        </div>
                        {actions(a)}
                    </div>
                )}
                columns={[
                    { key: "date", header: "Date", render: (a) => <span className="text-muted-foreground tabular-nums">{formatDateHeure(a.cree_le)}</span> },
                    { key: "membre", header: "Membre", render: (a) => <span className="font-medium">{a.prenom} {a.nom}</span> },
                    { key: "points", header: "Points", render: (a) => <Points a={a} /> },
                    { key: "motif", header: "Motif", className: "whitespace-normal min-w-56", render: (a) => <span><Badge variant="outline" className="mr-1.5">{CATEGORIES[a.categorie]?.label}</Badge>{a.motif}</span> },
                    { key: "par", header: "Par", render: (a) => a.cree_par ?? "—" },
                    { key: "actions", header: "", className: "text-right", render: actions },
                ]}
            />
            <Pagination page={page} total={data?.total ?? 0} limit={LIMIT} onPage={setPage} />

            <Dialog open={creer} onOpenChange={setCreer}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Bonus ou malus</DialogTitle>
                        <DialogDescription>Compté dans le classement du semestre choisi.</DialogDescription>
                    </DialogHeader>
                    {creer && <AjustementForm onSuccess={() => { setCreer(false); mutate(); }} />}
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default function GestionPointsPage() {
    return (
        <Suspense>
            <PointsContenu />
        </Suspense>
    );
}
