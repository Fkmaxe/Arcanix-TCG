"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { CalendarDays, CalendarX, List, Plus, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/DataTable";
import { EmptyState, ErrorBox, Skeleton } from "@/components/common/States";
import { CalendrierSeances } from "@/components/seances/CalendrierSeances";
import SeanceForm from "@/components/seances/SeanceForm";
import { SeanceCard } from "@/components/seances/SeanceCard";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { SeancesApi } from "@/lib/api";
import { isStaff, useAuth } from "@/lib/auth";
import { JEUX } from "@/lib/format";
import { useDebounced } from "@/lib/hooks";
import { errorMessage } from "@/lib/swr";
import { cn } from "@/lib/utils";

const LIMIT = 20;

export default function SeancesPage() {
    const { me } = useAuth();
    const router = useRouter();
    const [periode, setPeriode] = useState<"avenir" | "passees">("avenir");
    const [jeu, setJeu] = useState<string | undefined>();
    const [query, setQuery] = useState("");
    const [page, setPage] = useState(1);
    const [open, setOpen] = useState(false);
    const [vue, setVue] = useState<"liste" | "calendrier">("liste");
    const q = useDebounced(query.trim());

    // Mémorise la vue préférée (confort, sans garantie : stockage parfois indisponible)
    useEffect(() => {
        try {
            if (localStorage.getItem("arcanix:vue-seances") === "calendrier") setVue("calendrier");
        } catch {}
    }, []);
    const choisirVue = (v: "liste" | "calendrier") => {
        setVue(v);
        try {
            localStorage.setItem("arcanix:vue-seances", v);
        } catch {}
    };

    const params = { a_venir: periode === "avenir", jeu, q, page, limit: LIMIT };
    const { data, error, isLoading, mutate } = useSWR(vue === "liste" ? ["/seances", params] : null, () => SeancesApi.list(params));
    const reset = (fn: () => void) => { fn(); setPage(1); };

    return (
        <div className="space-y-5">
            <PageHeader
                title="Séances"
                description="Tournois, drafts et soirées de l'association."
                actions={
                    isStaff(me) && (
                        <Dialog open={open} onOpenChange={setOpen}>
                            <DialogTrigger asChild>
                                <Button className="w-full sm:w-auto"><Plus /> Nouvelle séance</Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Nouvelle séance</DialogTitle>
                                    <DialogDescription>Elle sera annoncée automatiquement sur le Discord.</DialogDescription>
                                </DialogHeader>
                                <SeanceForm onSuccess={(s) => { setOpen(false); mutate(); router.push(`/seances/${s.id}`); }} />
                            </DialogContent>
                        </Dialog>
                    )
                }
            />

            <div className="space-y-3">
                <div className="flex flex-col gap-2 sm:flex-row">
                    <div className="bg-muted inline-flex h-11 shrink-0 rounded-lg p-1" role="tablist" aria-label="Affichage">
                        {([["liste", "Liste", List], ["calendrier", "Calendrier", CalendarDays]] as const).map(([v, label, Icon]) => (
                            <button
                                key={v}
                                role="tab"
                                aria-selected={vue === v}
                                onClick={() => choisirVue(v)}
                                className={cn("flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 text-sm font-medium transition sm:flex-none", vue === v ? "bg-card text-gold shadow-sm" : "text-muted-foreground")}
                            >
                                <Icon className="size-4" /> {label}
                            </button>
                        ))}
                    </div>
                    {vue === "liste" && (
                    <div className="bg-muted inline-flex h-11 shrink-0 rounded-lg p-1" role="tablist" aria-label="Période">
                        {([["avenir", "À venir"], ["passees", "Passées"]] as const).map(([v, label]) => (
                            <button
                                key={v}
                                role="tab"
                                aria-selected={periode === v}
                                onClick={() => reset(() => setPeriode(v))}
                                className={cn("flex-1 rounded-md px-4 text-sm font-medium transition sm:flex-none", periode === v ? "bg-card text-gold shadow-sm" : "text-muted-foreground")}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                    )}
                    {vue === "liste" && (
                    <div className="relative flex-1">
                        <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                        <Input type="search" value={query} onChange={(e) => reset(() => setQuery(e.target.value))} placeholder="Rechercher une séance, un lieu…" className="pl-9" />
                    </div>
                    )}
                </div>
                {/* Filtres par jeu : défilement horizontal sur mobile */}
                <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:px-0">
                    {[{ value: undefined, label: "Tous les jeux", color: "var(--gold)" }, ...JEUX].map((j) => {
                        const active = jeu === j.value;
                        return (
                            <button
                                key={j.label}
                                onClick={() => reset(() => setJeu(j.value))}
                                aria-pressed={active}
                                className={cn(
                                    "h-9 shrink-0 rounded-full border px-3.5 text-sm transition",
                                    active ? "border-transparent font-semibold text-[#1a0d05]" : "text-muted-foreground hover:text-foreground",
                                )}
                                style={active ? { backgroundColor: j.color } : undefined}
                            >
                                {j.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {vue === "calendrier" ? (
                <CalendrierSeances jeu={jeu} />
            ) : (
            <>
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}
            {isLoading && !data ? (
                <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[76px]" />)}</div>
            ) : data?.items.length ? (
                <>
                    <ul className="grid gap-2 lg:grid-cols-2">
                        {data.items.map((s) => (
                            <li key={s.id}><SeanceCard seance={s} href={`/seances/${s.id}`} showCount={isStaff(me) || periode === "passees"} /></li>
                        ))}
                    </ul>
                    <Pagination page={page} total={data.total} limit={LIMIT} onPage={setPage} />
                </>
            ) : (
                <EmptyState
                    icon={<CalendarX />}
                    title={periode === "avenir" ? "Aucune séance à venir" : "Aucune séance passée"}
                    description={q || jeu ? "Essaie d'élargir ta recherche." : "Les prochaines dates seront annoncées sur le Discord."}
                />
            )}
            </>
            )}
        </div>
    );
}
