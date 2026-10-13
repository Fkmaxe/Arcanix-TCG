"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { isActive, navItems } from "./nav";
import { ThemeToggle, UserMenu } from "./UserMenu";

// Pages plein écran (sans barre de navigation basse)
const BARE = ["/login", "/register", "/activer", "/mot-de-passe-oublie"];

// Changer d'onglet ouvre toujours la page en haut
const versLeHaut = () => window.scrollTo({ top: 0 });

export default function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname() || "/";
    const { me, ready, isLoading } = useAuth();
    const items = navItems(me);
    const bare = BARE.some((p) => pathname.startsWith(p));
    const showBottomNav = !!me && !bare;

    return (
        <>
            <a href="#contenu" className="bg-primary text-primary-foreground sr-only z-[60] rounded px-3 py-2 focus:not-sr-only focus:fixed focus:top-2 focus:left-2">
                Aller au contenu
            </a>
            <header className="pt-safe bg-background/75 supports-[backdrop-filter]:bg-background/60 fixed inset-x-0 top-0 z-40 border-b backdrop-blur-md">
                <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:h-16 sm:px-6">
                    <Link href={me ? "/dashboard" : "/"} className="shrink-0 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-label="Arcanix — accueil">
                        <Logo size={34} />
                    </Link>

                    {/* Navigation desktop */}
                    <nav className="ml-6 hidden items-center gap-1 md:flex" aria-label="Navigation principale">
                        {items.map((item) => {
                            const active = isActive(item, pathname);
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    onClick={versLeHaut}
                                    aria-current={active ? "page" : undefined}
                                    className={cn(
                                        "relative rounded-md px-3 py-2 text-sm font-medium transition",
                                        active ? "text-gold" : "text-muted-foreground hover:text-foreground hover:bg-accent/60",
                                    )}
                                >
                                    {item.label}
                                    {active && <span className="bg-flame absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full sm:-bottom-[17px]" />}
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="ml-auto flex items-center gap-1.5">
                        {!ready || isLoading ? (
                            <div className="bg-muted size-10 animate-pulse rounded-full" />
                        ) : me ? (
                            <UserMenu />
                        ) : (
                            <>
                                <ThemeToggle />
                                {!bare && (
                                    <>
                                        <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                                            <Link href="/register">Créer un compte</Link>
                                        </Button>
                                        <Button asChild size="sm">
                                            <Link href={`/login${pathname !== "/" ? `?next=${encodeURIComponent(pathname)}` : ""}`}>Connexion</Link>
                                        </Button>
                                    </>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </header>

            <main
                id="contenu"
                className={cn(
                    "mx-auto w-full max-w-6xl px-4 pt-[calc(4.5rem+env(safe-area-inset-top))] sm:px-6 sm:pt-24",
                    showBottomNav ? "pb-[calc(6rem+env(safe-area-inset-bottom))] md:pb-12" : "pb-12",
                )}
            >
                {children}
            </main>

            {/* Barre d'onglets mobile (zone du pouce) */}
            {showBottomNav && (
                <nav
                    aria-label="Navigation principale"
                    className="pb-safe bg-background/90 supports-[backdrop-filter]:bg-background/75 fixed inset-x-0 bottom-0 z-40 border-t backdrop-blur-md md:hidden"
                >
                    <div className="rule-ornate absolute inset-x-0 top-0" />
                    <ul className="mx-auto flex max-w-md items-stretch justify-around">
                        {items.map((item) => {
                            const active = isActive(item, pathname);
                            const Icon = item.icon;
                            return (
                                <li key={item.href} className="flex-1">
                                    <Link
                                        href={item.href}
                                        onClick={versLeHaut}
                                        aria-current={active ? "page" : undefined}
                                        className={cn(
                                            "flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition",
                                            active ? "text-gold" : "text-muted-foreground active:text-foreground",
                                        )}
                                    >
                                        <span className={cn("grid h-7 w-12 place-items-center rounded-full transition", active && "bg-gold/15")}>
                                            <Icon className={cn("size-5", active && "drop-shadow-[0_0_6px_var(--ember)]")} />
                                        </span>
                                        {item.label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>
            )}
        </>
    );
}
