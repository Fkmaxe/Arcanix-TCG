"use client";

import Link from "next/link";
import useSWR from "swr";
import { CalendarRange, ChevronRight, Download, History, Sparkles, Swords, Users } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatTile } from "@/components/common/States";
import { SeancesApi, StatsApi, UsersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatPoints } from "@/lib/format";

export default function GestionPage() {
    const { me } = useAuth();
    const admin = me?.role_utilisateur === "admin";
    const { data: membres } = useSWR(["/users", "count"], () => UsersApi.list({ limit: 1 }));
    const { data: avenir } = useSWR(["/seances", "count-avenir"], () => SeancesApi.list({ a_venir: true, limit: 1 }));
    const { data: points } = useSWR(["/stats/points", "actif"], () => StatsApi.points());
    const actifs = points?.filter((p) => p.presences > 0).length;
    const totalPts = points?.reduce((a, p) => a + p.points, 0);

    const tuiles = [
        { href: "/gestion/seances", icon: Swords, titre: "Séances", texte: "Créer, modifier, faire l'appel." },
        { href: "/gestion/membres", icon: Users, titre: "Membres", texte: "Comptes, rôles, mots de passe." },
        { href: "/gestion/points", icon: Sparkles, titre: "Bonus & malus", texte: "Points hors séance, avec motif." },
        { href: "/gestion/journal", icon: History, titre: "Journal", texte: "Qui a fait quoi, et quand." },
        ...(admin ? [{ href: "/gestion/semestres", icon: CalendarRange, titre: "Semestres", texte: "Semestre en cours, clôture et podium." }] : []),
        { href: "/gestion/exports", icon: Download, titre: "Exports", texte: "Points et présences en CSV / JSON." },
    ];

    return (
        <div className="space-y-6">
            <PageHeader eyebrow="Modération" title="Salle du conseil" description="Tout ce qu'il faut pour faire vivre l'association." />
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatTile label="Membres" value={membres?.total ?? "—"} />
                <StatTile label="Actifs (semestre)" value={actifs ?? "—"} />
                <StatTile label="Séances à venir" value={avenir?.total ?? "—"} />
                <StatTile label="Points distribués" value={totalPts !== undefined ? formatPoints(totalPts) : "—"} />
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
                {tuiles.map(({ href, icon: Icon, titre, texte }) => (
                    <li key={href}>
                        <Link href={href} className="bg-card hover:border-gold/40 hover:bg-accent/30 flex items-center gap-4 rounded-xl border p-4 transition">
                            <span className="frame-gilded grid size-12 shrink-0 place-items-center rounded-lg">
                                <Icon className="text-gold size-6" />
                            </span>
                            <div className="min-w-0 flex-1">
                                <p className="font-display font-semibold">{titre}</p>
                                <p className="text-muted-foreground text-sm">{texte}</p>
                            </div>
                            <ChevronRight className="text-muted-foreground" />
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
}
