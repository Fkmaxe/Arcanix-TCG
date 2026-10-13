import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export function EmptyState({
    icon,
    title,
    description,
    action,
    className,
}: {
    icon?: React.ReactNode;
    title: string;
    description?: React.ReactNode;
    action?: React.ReactNode;
    className?: string;
}) {
    return (
        <div className={cn("flex flex-col items-center gap-2 px-4 py-10 text-center", className)}>
            {icon && <div className="text-gold/70 mb-1 [&_svg]:size-10">{icon}</div>}
            <p className="font-display text-base font-semibold">{title}</p>
            {description && <p className="text-muted-foreground max-w-sm text-sm">{description}</p>}
            {action && <div className="mt-3">{action}</div>}
        </div>
    );
}

export function Skeleton({ className }: { className?: string }) {
    return (
        <div
            className={cn(
                "animate-shimmer rounded-md bg-[linear-gradient(90deg,var(--muted)_25%,var(--accent)_50%,var(--muted)_75%)] bg-[length:200%_100%]",
                className,
            )}
        />
    );
}

export function FullPageLoader({ label = "Chargement…" }: { label?: string }) {
    return (
        <div className="text-muted-foreground flex min-h-[50dvh] items-center justify-center gap-2" role="status">
            <Loader2 className="text-ember size-5 animate-spin" /> {label}
        </div>
    );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
    return (
        <div className="border-destructive/40 bg-destructive/10 text-destructive flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm" role="alert">
            <span>{message}</span>
            {onRetry && (
                <button onClick={onRetry} className="font-medium underline underline-offset-4">
                    Réessayer
                </button>
            )}
        </div>
    );
}

export function StatTile({
    label,
    value,
    hint,
    icon,
    className,
}: {
    label: string;
    value: React.ReactNode;
    hint?: React.ReactNode;
    icon?: React.ReactNode;
    className?: string;
}) {
    return (
        <div className={cn("bg-card rounded-xl border p-3 sm:p-4", className)}>
            <div className="text-muted-foreground flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase [&_svg]:size-3.5">
                {icon}
                {label}
            </div>
            <div className="font-display mt-1 text-2xl font-bold tabular-nums sm:text-3xl">{value}</div>
            {hint && <div className="text-muted-foreground mt-0.5 text-xs">{hint}</div>}
        </div>
    );
}
