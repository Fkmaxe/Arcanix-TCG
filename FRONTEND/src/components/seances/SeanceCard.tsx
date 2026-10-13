import Link from "next/link";
import { ChevronRight, Clock, MapPin, Users } from "lucide-react";
import type { Seance } from "@/lib/types";
import { dateParts, formatHeure, formatPoints, relativeDay, todayIso } from "@/lib/format";
import { cn } from "@/lib/utils";
import { JeuBadge } from "./JeuBadge";

export function DateTile({ iso, className }: { iso: string; className?: string }) {
    const { jour, mois, semaine } = dateParts(iso);
    return (
        <div className={cn("frame-gilded flex w-14 shrink-0 flex-col items-center justify-center rounded-lg py-1.5 leading-none", className)}>
            <span className="text-muted-foreground text-[10px] uppercase">{semaine}</span>
            <span className="font-display text-gilded text-2xl font-bold">{jour}</span>
            <span className="text-muted-foreground text-[10px] uppercase">{mois}</span>
        </div>
    );
}

export function SeanceCard({ seance, href, showCount = false }: { seance: Seance; href?: string; showCount?: boolean }) {
    const rel = relativeDay(seance.date_seance);
    const passe = seance.date_seance < todayIso();
    const heure = formatHeure(seance.heure_debut);
    const content = (
        <div
            className={cn(
                "bg-card group flex items-center gap-3 rounded-xl border p-3 transition sm:p-4",
                href && "hover:border-gold/40 hover:bg-accent/30 active:scale-[0.99]",
                passe && "opacity-80",
            )}
        >
            <DateTile iso={seance.date_seance} />
            <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <h3 className="truncate font-sans text-[15px] font-semibold tracking-normal">{seance.nom}</h3>
                    {rel && <span className="text-ember text-xs font-semibold">{rel}</span>}
                </div>
                <div className="text-muted-foreground mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                    <JeuBadge jeu={seance.jeu} />
                    {heure && <span className="inline-flex items-center gap-1"><Clock className="size-3.5" />{heure}</span>}
                    {seance.lieu && <span className="inline-flex min-w-0 items-center gap-1"><MapPin className="size-3.5 shrink-0" /><span className="truncate">{seance.lieu}</span></span>}
                    {showCount && <span className="inline-flex items-center gap-1"><Users className="size-3.5" />{seance.nb_presents}</span>}
                </div>
            </div>
            <div className="flex shrink-0 items-center gap-1">
                <span className="text-gold font-display text-sm font-bold whitespace-nowrap tabular-nums">
                    +{formatPoints(seance.nb_point)}<span className="text-muted-foreground ml-0.5 font-sans text-[10px] font-normal">pts</span>
                </span>
                {href && <ChevronRight className="text-muted-foreground size-4 transition group-hover:translate-x-0.5" />}
            </div>
        </div>
    );
    return href ? <Link href={href} className="block rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring">{content}</Link> : content;
}
