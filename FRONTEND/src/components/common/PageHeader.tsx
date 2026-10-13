import { cn } from "@/lib/utils";

export function PageHeader({
    title,
    description,
    actions,
    eyebrow,
    className,
}: {
    title: React.ReactNode;
    description?: React.ReactNode;
    actions?: React.ReactNode;
    eyebrow?: React.ReactNode;
    className?: string;
}) {
    return (
        <header className={cn("mb-5 flex flex-col gap-3 sm:mb-8 sm:flex-row sm:items-end sm:justify-between", className)}>
            <div className="min-w-0">
                {eyebrow && <p className="text-ember mb-1 text-xs font-semibold tracking-[0.2em] uppercase">{eyebrow}</p>}
                <h1 className="text-gilded text-2xl font-bold sm:text-3xl">{title}</h1>
                {description && <p className="text-muted-foreground mt-1.5 text-sm sm:text-base">{description}</p>}
            </div>
            {actions && <div className="flex flex-wrap gap-2 sm:shrink-0">{actions}</div>}
        </header>
    );
}

export function SectionTitle({ children, action, className }: { children: React.ReactNode; action?: React.ReactNode; className?: string }) {
    return (
        <div className={cn("mb-3 flex items-center gap-3", className)}>
            <svg viewBox="0 0 12 12" className="text-ember size-2.5 shrink-0" aria-hidden>
                <path d="M6 0 12 6 6 12 0 6Z" fill="currentColor" />
            </svg>
            <h2 className="text-base font-semibold tracking-wide sm:text-lg">{children}</h2>
            <span className="rule-ornate flex-1" />
            {action}
        </div>
    );
}
