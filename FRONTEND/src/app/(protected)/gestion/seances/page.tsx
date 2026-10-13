"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { useRouter } from "next/navigation";
import { ClipboardCheck, Pencil, Plus, Search, Swords, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { DataTable, Pagination } from "@/components/common/DataTable";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorBox } from "@/components/common/States";
import { JeuBadge } from "@/components/seances/JeuBadge";
import SeanceForm from "@/components/seances/SeanceForm";
import { SeanceCard } from "@/components/seances/SeanceCard";
import { SemestreSelect } from "@/components/semestres/SemestreSelect";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { SeancesApi } from "@/lib/api";
import { formatDate, formatHeure, formatPoints, semestreLabel } from "@/lib/format";
import { useDebounced } from "@/lib/hooks";
import { errorMessage } from "@/lib/swr";
import type { Seance } from "@/lib/types";

const LIMIT = 25;

export default function GestionSeancesPage() {
    const router = useRouter();
    const [semestreId, setSemestreId] = useState<number | undefined>();
    const [query, setQuery] = useState("");
    const [page, setPage] = useState(1);
    const [editing, setEditing] = useState<Seance | "new" | null>(null);
    const q = useDebounced(query.trim());
    const params = { semestreId, q, page, limit: LIMIT };
    const { data, error, isLoading, mutate } = useSWR(["/seances", "gestion", params], () => SeancesApi.list(params));

    const supprimer = async (s: Seance) => {
        try {
            await SeancesApi.remove(s.id);
            toast.success("Séance supprimée");
            mutate();
        } catch (err) {
            toast.error(errorMessage(err));
        }
    };

    const actions = (s: Seance) => (
        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
            <Button asChild size="sm" variant="outline"><Link href={`/seances/${s.id}`}><ClipboardCheck /> Appel</Link></Button>
            <Button size="icon-sm" variant="ghost" onClick={() => setEditing(s)} aria-label="Modifier"><Pencil /></Button>
            <ConfirmButton title={`Supprimer « ${s.nom} » ?`} description={`${s.nb_participants} participation(s) seront supprimées.`} confirmLabel="Supprimer" onConfirm={() => supprimer(s)}>
                <Button size="icon-sm" variant="ghost" className="text-destructive" aria-label="Supprimer"><Trash2 /></Button>
            </ConfirmButton>
        </div>
    );

    return (
        <div className="space-y-5">
            <PageHeader
                eyebrow="Gestion"
                title="Séances"
                actions={<Button onClick={() => setEditing("new")} className="w-full sm:w-auto"><Plus /> Nouvelle séance</Button>}
            />
            <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                    <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                    <Input type="search" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} placeholder="Rechercher…" className="pl-9" />
                </div>
                <SemestreSelect value={semestreId} onChange={(v) => { setSemestreId(v); setPage(1); }} allowAll />
            </div>
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}

            <DataTable
                isLoading={isLoading}
                rows={data?.items ?? []}
                rowKey={(s) => s.id}
                empty="Aucune séance"
                emptyIcon={<Swords />}
                onRowClick={(s) => router.push(`/seances/${s.id}`)}
                mobileCard={(s) => (
                    <div className="space-y-2">
                        <SeanceCard seance={s} href={`/seances/${s.id}`} showCount />
                        <div className="flex justify-end">{actions(s)}</div>
                    </div>
                )}
                columns={[
                    { key: "date", header: "Date", render: (s) => <span className="tabular-nums">{formatDate(s.date_seance)} {formatHeure(s.heure_debut) && <span className="text-muted-foreground">· {formatHeure(s.heure_debut)}</span>}</span> },
                    { key: "nom", header: "Séance", render: (s) => <div className="flex items-center gap-2"><span className="font-medium">{s.nom}</span><JeuBadge jeu={s.jeu} /></div> },
                    { key: "points", header: "Points", render: (s) => <span className="text-gold font-semibold">{formatPoints(s.nb_point)}</span> },
                    { key: "presents", header: "Présents", render: (s) => `${s.nb_presents}/${s.nb_participants}` },
                    { key: "semestre", header: "Semestre", render: (s) => semestreLabel(s.semestre) },
                    { key: "actions", header: "", className: "text-right", render: actions },
                ]}
            />
            <Pagination page={page} total={data?.total ?? 0} limit={LIMIT} onPage={setPage} />

            <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editing === "new" ? "Nouvelle séance" : "Modifier la séance"}</DialogTitle>
                        {editing === "new" && <DialogDescription>Elle sera annoncée automatiquement sur le Discord.</DialogDescription>}
                    </DialogHeader>
                    {editing && (
                        <SeanceForm
                            seance={editing === "new" ? undefined : editing}
                            onSuccess={() => { setEditing(null); mutate(); }}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
