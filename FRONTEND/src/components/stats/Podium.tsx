import { Crown } from "lucide-react";
import type { LigneClassement } from "@/lib/types";
import { formatPoints, initials } from "@/lib/format";
import { cn } from "@/lib/utils";

const STYLES = {
    1: { h: "h-28 sm:h-36", ring: "from-[#ffe7a3] via-[#f5c24b] to-[#b8860b]", label: "text-gold" },
    2: { h: "h-20 sm:h-28", ring: "from-[#f1f1f1] via-[#c0c0c0] to-[#8a8a8a]", label: "text-[#6f6f6f] dark:text-[#c9c9c9]" },
    3: { h: "h-16 sm:h-20", ring: "from-[#f0b27a] via-[#cd7f32] to-[#8b4513]", label: "text-[#9a5420] dark:text-[#d9925a]" },
} as const;

function Marche({ ligne, place }: { ligne?: LigneClassement; place: 1 | 2 | 3 }) {
    const s = STYLES[place];
    return (
        <div className="flex min-w-0 flex-1 flex-col items-center gap-2">
            {ligne ? (
                <>
                    {place === 1 && <Crown className="text-gold animate-flicker size-6" aria-hidden />}
                    <div className={cn("rounded-full bg-gradient-to-br p-[2px]", s.ring)}>
                        <div className={cn("bg-card grid size-12 place-items-center rounded-full text-sm font-bold sm:size-14", s.label)}>
                            {initials(ligne.prenom, ligne.nom)}
                        </div>
                    </div>
                    <div className="w-full text-center">
                        <p className={cn("truncate text-sm font-semibold", ligne.moi && "text-ember")}>{ligne.prenom} {ligne.nom}</p>
                        <p className="font-display text-gilded text-lg font-bold tabular-nums">{formatPoints(ligne.points)}</p>
                    </div>
                </>
            ) : (
                <div className="text-muted-foreground grid size-12 place-items-center rounded-full border border-dashed text-xs sm:size-14">—</div>
            )}
            <div
                className={cn(
                    "frame-gilded flex w-full items-start justify-center rounded-t-lg pt-2",
                    s.h,
                    place === 1 && "shadow-[0_-10px_40px_-10px_var(--ember)]",
                )}
            >
                <span className={cn("font-display text-3xl font-bold", s.label)}>{place}</span>
            </div>
        </div>
    );
}

export function Podium({ lignes }: { lignes: LigneClassement[] }) {
    // Les ex æquo partagent un rang : on prend simplement les trois premiers
    const [a, b, c] = lignes;
    return (
        <div className="flex items-end gap-2 sm:gap-4" aria-label="Podium">
            <Marche ligne={b} place={2} />
            <Marche ligne={a} place={1} />
            <Marche ligne={c} place={3} />
        </div>
    );
}
