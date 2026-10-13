import { cn } from "@/lib/utils";
import { CornerFlourish } from "./Ornament";

/** Carte à cadre doré et coins enluminés — à réserver aux éléments clés. */
export function OrnateCard({
    className,
    children,
    corners = true,
    ...props
}: React.ComponentProps<"div"> & { corners?: boolean }) {
    return (
        <div
            className={cn(
                "frame-gilded text-card-foreground relative rounded-xl p-4 shadow-[0_18px_40px_-24px_var(--ember)] sm:p-6",
                className,
            )}
            {...props}
        >
            {corners && (
                <>
                    <CornerFlourish className="absolute top-1.5 left-1.5" />
                    <CornerFlourish className="absolute top-1.5 right-1.5 -scale-x-100" />
                    <CornerFlourish className="absolute bottom-1.5 left-1.5 -scale-y-100" />
                    <CornerFlourish className="absolute right-1.5 bottom-1.5 -scale-100" />
                </>
            )}
            <div className="relative">{children}</div>
        </div>
    );
}
