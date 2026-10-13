import Image from "next/image";
import { cn } from "@/lib/utils";

export function Logo({ size = 36, withText = true, className }: { size?: number; withText?: boolean; className?: string }) {
    return (
        <span className={cn("inline-flex items-center gap-2.5", className)}>
            <Image
                src="/brand/carte-192.png"
                alt=""
                width={size}
                height={size}
                className="drop-shadow-[0_0_8px_rgb(255_122_26/0.45)]"
                priority
            />
            {withText && (
                <span className="font-display text-gilded text-lg font-bold tracking-[0.14em]">ARCANIX</span>
            )}
        </span>
    );
}
