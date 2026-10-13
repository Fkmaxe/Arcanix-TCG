"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { LogOut, Moon, ScrollText, Sun, User } from "lucide-react";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";
import { initials, ROLE_LABELS } from "@/lib/format";

export function ThemeToggle({ className }: { className?: string }) {
    const { resolvedTheme, setTheme } = useTheme();
    const dark = resolvedTheme !== "light";
    return (
        <button
            type="button"
            onClick={() => setTheme(dark ? "light" : "dark")}
            className={className ?? "hover:bg-accent text-muted-foreground hover:text-foreground grid size-10 place-items-center rounded-md transition"}
            aria-label={dark ? "Passer au thème Parchemin" : "Passer au thème Obsidienne"}
            title={dark ? "Thème Parchemin" : "Thème Obsidienne"}
        >
            {dark ? <Sun className="size-5" /> : <Moon className="size-5" />}
        </button>
    );
}

export function UserMenu() {
    const { me, logout } = useAuth();
    const router = useRouter();
    const { resolvedTheme, setTheme } = useTheme();
    if (!me) return null;
    const dark = resolvedTheme !== "light";

    return (
        <DropdownMenu>
            <DropdownMenuTrigger
                className="frame-gilded text-gold grid size-10 place-items-center rounded-full text-sm font-bold outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Menu du compte"
            >
                {initials(me.prenom, me.nom)}
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
                <DropdownMenuLabel className="font-normal">
                    <div className="font-display font-semibold">{me.prenom} {me.nom}</div>
                    <div className="text-muted-foreground truncate text-xs">{me.adresse_mail}</div>
                    <div className="text-gold mt-1 text-xs">{ROLE_LABELS[me.role_utilisateur]} · {me.classe}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                    <Link href="/profil"><User /> Mon profil</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                    <Link href="/profil#historique"><ScrollText /> Mon historique</Link>
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setTheme(dark ? "light" : "dark")}>
                    {dark ? <Sun /> : <Moon />} Thème {dark ? "Parchemin" : "Obsidienne"}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    variant="destructive"
                    onSelect={() => {
                        logout();
                        router.replace("/login");
                    }}
                >
                    <LogOut /> Déconnexion
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
