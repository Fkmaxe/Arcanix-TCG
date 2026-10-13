import { CalendarDays, Crown, Home, Shield, Swords, Trophy, User } from "lucide-react";
import type { Me } from "@/lib/types";

export type NavItem = { href: string; label: string; icon: typeof Home; match?: (p: string) => boolean };

export function navItems(me: Me | null): NavItem[] {
    if (!me) {
        return [
            { href: "/", label: "Accueil", icon: Home, match: (p) => p === "/" },
            { href: "/seances", label: "Séances", icon: CalendarDays },
        ];
    }
    const items: NavItem[] = [
        { href: "/dashboard", label: "Accueil", icon: Home, match: (p) => p === "/dashboard" || p === "/" },
        { href: "/seances", label: "Séances", icon: Swords },
        { href: "/classement", label: "Classement", icon: Trophy },
        { href: "/profil", label: "Profil", icon: User },
    ];
    if (me.role_utilisateur === "admin" || me.role_utilisateur === "moderator") {
        items.push({ href: "/gestion", label: "Gestion", icon: me.role_utilisateur === "admin" ? Crown : Shield });
    }
    return items;
}

export const isActive = (item: NavItem, pathname: string) =>
    item.match ? item.match(pathname) : pathname === item.href || pathname.startsWith(`${item.href}/`);
