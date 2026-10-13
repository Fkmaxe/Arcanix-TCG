import { cn } from "@/lib/utils";

/** Arabesque d'angle inspirée des enluminures du logo. */
export function CornerFlourish({ className }: { className?: string }) {
    return (
        <svg viewBox="0 0 48 48" aria-hidden className={cn("pointer-events-none size-7 sm:size-9", className)}>
            <defs>
                <linearGradient id="arcanix-or" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0" stopColor="var(--frame-from)" />
                    <stop offset="0.6" stopColor="var(--frame-via)" />
                    <stop offset="1" stopColor="var(--frame-to)" />
                </linearGradient>
            </defs>
            <g fill="none" stroke="url(#arcanix-or)" strokeWidth="1.6" strokeLinecap="round">
                <path d="M3 45V17C3 9.3 9.3 3 17 3h28" />
                <path d="M9 36c0-14 13-27 27-27" opacity=".7" />
                <path d="M14 14c4 0 6 2.5 6 6-3 0-6-2-6-6Z" />
            </g>
            <circle cx="9" cy="9" r="2.6" fill="url(#arcanix-or)" />
        </svg>
    );
}

/** Filet décoratif avec losange central. */
export function Divider({ className }: { className?: string }) {
    return (
        <div className={cn("flex items-center gap-3", className)} aria-hidden>
            <span className="rule-ornate flex-1" />
            <svg viewBox="0 0 24 12" className="h-3 w-6 text-gold">
                <path d="M12 1 17 6l-5 5-5-5 5-5Z" fill="currentColor" opacity=".9" />
                <circle cx="2" cy="6" r="1.4" fill="currentColor" opacity=".6" />
                <circle cx="22" cy="6" r="1.4" fill="currentColor" opacity=".6" />
            </svg>
            <span className="rule-ornate flex-1" />
        </div>
    );
}
