import { jeuInfo } from "@/lib/format";
import { cn } from "@/lib/utils";

export function JeuBadge({ jeu, className }: { jeu: string | null | undefined; className?: string }) {
    const info = jeuInfo(jeu);
    if (!info) return null;
    return (
        <span
            className={cn("inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium", className)}
            style={{ borderColor: `${info.color}66`, backgroundColor: `${info.color}1a`, color: info.color }}
        >
            <span className="size-1.5 rounded-full" style={{ backgroundColor: info.color }} />
            {info.label}
        </span>
    );
}
