import { cn } from "@/lib/utils";

// Positions pseudo-aléatoires mais déterministes (pas d'écart serveur/client)
const EMBERS = Array.from({ length: 18 }, (_, i) => {
    const r = (n: number) => ((Math.sin(i * 97.13 + n * 13.7) + 1) / 2);
    return {
        left: `${Math.round(r(1) * 100)}%`,
        size: 2 + Math.round(r(2) * 3),
        delay: `${(r(3) * 6).toFixed(2)}s`,
        duration: `${(5 + r(4) * 5).toFixed(2)}s`,
        drift: `${Math.round((r(5) - 0.5) * 80)}px`,
    };
});

/** Braises qui s'élèvent (décor du hero). Désactivées si l'utilisateur réduit les animations. */
export function Embers({ className }: { className?: string }) {
    return (
        <div aria-hidden className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
            {EMBERS.map((e, i) => (
                <span
                    key={i}
                    className="animate-ember-rise absolute bottom-0 rounded-full bg-ember opacity-0 motion-reduce:hidden"
                    style={{
                        left: e.left,
                        width: e.size,
                        height: e.size,
                        animationDelay: e.delay,
                        boxShadow: "0 0 8px 2px rgb(255 122 26 / 0.7)",
                        ["--ember-duration" as string]: e.duration,
                        ["--ember-drift" as string]: e.drift,
                    }}
                />
            ))}
        </div>
    );
}
