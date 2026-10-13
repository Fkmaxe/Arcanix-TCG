// src/app/layout.tsx
import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Providers from "@/components/providers/Providers";
import AppShell from "@/components/layout/AppShell";
import { Toaster } from "@/components/ui/sonner";

// Polices embarquées (src/app/fonts) : le build ne dépend pas de Google Fonts
const inter = localFont({ src: "./fonts/inter-variable-latin.woff2", weight: "100 900", variable: "--font-inter", display: "swap" });
const cinzel = localFont({ src: "./fonts/cinzel-variable-latin.woff2", weight: "400 900", variable: "--font-cinzel", display: "swap" });

export const metadata: Metadata = {
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
    title: { default: "Arcanix — Association TCG", template: "%s · Arcanix" },
    description: "Séances, présences et classement de l'association de jeux de cartes à collectionner Arcanix.",
    applicationName: "Arcanix",
    appleWebApp: { capable: true, title: "Arcanix", statusBarStyle: "black-translucent" },
    formatDetection: { telephone: false },
};

export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
    viewportFit: "cover",
    themeColor: [
        { media: "(prefers-color-scheme: dark)", color: "#0b0a0c" },
        { media: "(prefers-color-scheme: light)", color: "#f6efe0" },
    ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr" suppressHydrationWarning className={`${inter.variable} ${cinzel.variable}`}>
            <body className="font-sans">
                <Providers>
                    <AppShell>{children}</AppShell>
                    <Toaster position="top-center" richColors closeButton offset={{ top: 76 }} mobileOffset={{ top: 64, left: 12, right: 12 }} />
                </Providers>
            </body>
        </html>
    );
}
