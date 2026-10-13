"use client";

import Link from "next/link";
import useSWR from "swr";
import { ArrowRight, CalendarX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SectionTitle } from "@/components/common/PageHeader";
import { EmptyState, Skeleton } from "@/components/common/States";
import { SeanceCard } from "@/components/seances/SeanceCard";
import { SeancesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function HomeCta() {
    const { me, ready, isLoading } = useAuth();
    if (!ready || isLoading) return <div className="h-12" />;
    if (me) {
        return (
            <Button asChild size="lg" className="w-full sm:w-auto">
                <Link href="/dashboard">Mon tableau de bord <ArrowRight /></Link>
            </Button>
        );
    }
    return (
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button asChild size="lg"><Link href="/register">Rejoindre l&apos;aventure</Link></Button>
            <Button asChild size="lg" variant="outline"><Link href="/login">J&apos;ai déjà un compte</Link></Button>
        </div>
    );
}

export function ProchainesSeances() {
    const { data, isLoading } = useSWR(["/seances", "a-venir", 4], () => SeancesApi.list({ a_venir: true, limit: 4 }));
    const seances = data?.items ?? [];
    return (
        <section className="mx-auto max-w-3xl">
            <SectionTitle action={<Link href="/seances" className="text-gold text-sm hover:underline">Tout voir</Link>}>
                Prochaines séances
            </SectionTitle>
            {isLoading && !data ? (
                <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-[76px]" />)}</div>
            ) : seances.length ? (
                <ul className="space-y-2">
                    {seances.map((s) => <li key={s.id}><SeanceCard seance={s} href={`/seances/${s.id}`} /></li>)}
                </ul>
            ) : (
                <EmptyState icon={<CalendarX />} title="Aucune séance programmée" description="Les prochaines dates seront annoncées ici et sur le Discord." />
            )}
        </section>
    );
}
