"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { MesStats } from "@/lib/types";
import { formatDate, formatPoints } from "@/lib/format";

/** Courbe du cumul de points sur le semestre (SVG, sans dépendance). */
export function PointsChart({ data }: { data: MesStats["evolution"] }) {
    const id = useId().replace(/:/g, "");
    const [hover, setHover] = useState<number | null>(null);
    // Largeur réelle du conteneur : le texte garde une taille lisible sur mobile
    const ref = useRef<HTMLElement>(null);
    const [W, setW] = useState(600);
    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const ro = new ResizeObserver(([e]) => setW(Math.max(260, Math.round(e.contentRect.width))));
        ro.observe(el);
        return () => ro.disconnect();
    }, []);
    if (data.length === 0) {
        return (
            <figure ref={ref}>
                <p className="text-muted-foreground py-8 text-center text-sm">Pas encore de points ce semestre.</p>
            </figure>
        );
    }
    const H = 200, P = { t: 16, r: 12, b: 24, l: 32 };
    const max = Math.max(...data.map((d) => d.cumul), 1);
    const pts = [{ cumul: 0 }, ...data].map((d, i, arr) => ({
        x: P.l + (i / Math.max(arr.length - 1, 1)) * (W - P.l - P.r),
        y: H - P.b - (d.cumul / max) * (H - P.t - P.b),
    }));
    const line = pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const area = `${line} L${pts[pts.length - 1].x},${H - P.b} L${pts[0].x},${H - P.b} Z`;
    const ticks = [0, max / 2, max];
    const h = hover !== null ? data[hover] : null;

    return (
        <figure ref={ref} className="relative">
            <svg viewBox={`0 0 ${W} ${H}`} height={H} className="w-full" role="img" aria-label={`Évolution : ${formatPoints(max)} points cumulés`}>
                <defs>
                    <linearGradient id={`fill-${id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0" stopColor="var(--ember)" stopOpacity="0.45" />
                        <stop offset="1" stopColor="var(--ember)" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id={`stroke-${id}`} x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0" stopColor="var(--flame)" />
                        <stop offset="1" stopColor="var(--gold)" />
                    </linearGradient>
                </defs>
                {ticks.map((t) => {
                    const y = H - P.b - (t / max) * (H - P.t - P.b);
                    return (
                        <g key={t}>
                            <line x1={P.l} x2={W - P.r} y1={y} y2={y} stroke="var(--border)" strokeDasharray="3 4" />
                            <text x={P.l - 6} y={y + 4} textAnchor="end" fontSize="11" fill="var(--muted-foreground)">{formatPoints(Math.round(t * 10) / 10)}</text>
                        </g>
                    );
                })}
                <path d={area} fill={`url(#fill-${id})`} />
                <path d={line} fill="none" stroke={`url(#stroke-${id})`} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
                {pts.slice(1).map((p, i) => (
                    <g key={i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} onClick={() => setHover(i)}>
                        <circle cx={p.x} cy={p.y} r="14" fill="transparent" />
                        <circle cx={p.x} cy={p.y} r={hover === i ? 5.5 : 3.5} fill="var(--gold)" stroke="var(--card)" strokeWidth="2" />
                    </g>
                ))}
            </svg>
            <figcaption className="text-muted-foreground mt-1 min-h-5 text-center text-xs" aria-live="polite">
                {h ? (
                    <>
                        <span className="text-foreground font-medium">{h.seance}</span> · {formatDate(h.date, "jour")} · +{formatPoints(h.points)} → <span className="text-gold font-semibold">{formatPoints(h.cumul)} pts</span>
                    </>
                ) : (
                    "Touchez un point pour le détail"
                )}
            </figcaption>
        </figure>
    );
}
