"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { useRouter, useSearchParams } from "next/navigation";
import { CalendarCog, Crown, History, KeyRound, ListChecks, QrCode, Sparkles, Swords, Trophy, UserCog, X } from "lucide-react";
import { Pagination } from "@/components/common/DataTable";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorBox, Skeleton } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { JournalApi, UsersApi } from "@/lib/api";
import { formatDateHeure } from "@/lib/format";
import { errorMessage } from "@/lib/swr";

const LIMIT = 30;
const FILTRES: [string, string][] = [
    ["tout", "Toutes les actions"],
    ["presence", "Présences"],
    ["points", "Bonus & malus"],
    ["tournoi", "Résultats de tournoi"],
    ["pointage", "Pointage QR"],
    ["seance", "Séances"],
    ["membre", "Membres & rôles"],
    ["semestre", "Semestres"],
    ["inscription", "Inscriptions"],
];

function icone(action: string) {
    if (action.startsWith("presence")) return ListChecks;
    if (action.startsWith("points")) return Sparkles;
    if (action.startsWith("tournoi")) return Trophy;
    if (action.startsWith("pointage")) return QrCode;
    if (action.startsWith("seance")) return Swords;
    if (action.startsWith("semestre")) return Crown;
    if (action === "membre.lien_mdp" || action === "membre.mdp") return KeyRound;
    if (action.startsWith("membre")) return UserCog;
    return CalendarCog;
}

function JournalContenu() {
    const router = useRouter();
    const membreId = Number(useSearchParams().get("membre")) || undefined;
    const [filtre, setFiltre] = useState("tout");
    const [page, setPage] = useState(1);
    const params = { membreId, action: filtre === "tout" ? undefined : filtre, page, limit: LIMIT };
    const { data, error, isLoading, mutate } = useSWR(["/journal", params], () => JournalApi.list(params));
    const { data: membre } = useSWR(membreId ? ["/users", membreId] : null, () => UsersApi.get(membreId!));

    // Regroupement par jour
    const groupes = new Map<string, NonNullable<typeof data>["items"]>();
    data?.items.forEach((e) => {
        const jour = new Date(e.cree_le).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
        groupes.set(jour, [...(groupes.get(jour) ?? []), e]);
    });

    return (
        <div className="space-y-5">
            <PageHeader eyebrow="Gestion" title="Journal" description="Qui a fait quoi, et quand : présences, points, rôles… En cas de contestation, tout est ici." />
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Select value={filtre} onValueChange={(v) => { setFiltre(v); setPage(1); }}>
                    <SelectTrigger className="sm:w-64" aria-label="Type d'action"><SelectValue /></SelectTrigger>
                    <SelectContent>{FILTRES.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent>
                </Select>
                {membreId && (
                    <span className="bg-accent inline-flex h-9 items-center gap-1 self-start rounded-full pr-1 pl-3 text-sm">
                        {membre ? `${membre.prenom} ${membre.nom}` : `Membre #${membreId}`}
                        <Button size="icon-sm" variant="ghost" className="size-7" aria-label="Retirer le filtre membre" onClick={() => router.replace("/gestion/journal")}><X /></Button>
                    </span>
                )}
            </div>
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}
            {isLoading && !data ? (
                <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
            ) : !data?.items.length ? (
                <EmptyState icon={<History />} title="Aucune entrée" description="Les actions de la modération apparaîtront ici." />
            ) : (
                <div className="space-y-6">
                    {[...groupes].map(([jour, entrees]) => (
                        <section key={jour}>
                            <h2 className="text-muted-foreground mb-2 font-sans text-xs font-semibold tracking-wider uppercase first-letter:uppercase">{jour}</h2>
                            <ol className="bg-card divide-y rounded-xl border">
                                {entrees.map((e) => {
                                    const Icon = icone(e.action);
                                    return (
                                        <li key={e.id} className="flex gap-3 px-3 py-3 sm:px-4">
                                            <span className="bg-accent text-gold mt-0.5 grid size-8 shrink-0 place-items-center rounded-full"><Icon className="size-4" /></span>
                                            <div className="min-w-0 flex-1">
                                                <p className="text-sm">{e.resume}</p>
                                                <p className="text-muted-foreground mt-0.5 flex flex-wrap gap-x-2 text-xs">
                                                    <span>{formatDateHeure(e.cree_le).split(" ")[1] ?? formatDateHeure(e.cree_le)}</span>
                                                    <span>· par {e.auteur_nom}</span>
                                                    {e.seance_id && <Link href={`/seances/${e.seance_id}`} className="text-gold hover:underline">· séance</Link>}
                                                    {e.membre_id && !membreId && (
                                                        <Link href={`/gestion/journal?membre=${e.membre_id}`} className="text-gold hover:underline">· historique du membre</Link>
                                                    )}
                                                </p>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ol>
                        </section>
                    ))}
                    <Pagination page={page} total={data.total} limit={LIMIT} onPage={setPage} />
                </div>
            )}
        </div>
    );
}

export default function JournalPage() {
    return (
        <Suspense>
            <JournalContenu />
        </Suspense>
    );
}
