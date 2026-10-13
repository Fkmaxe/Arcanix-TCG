// src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css"; // <= corrige bien le chemin (./, pas ../)
import { Inter } from "next/font/google";
import SWRProvider from "@/components/providers/SWRProvider";
import TopBar from "@/components/layout/TopBar";
import { Toaster } from "@/components/ui/sonner"
import { ThemeProvider } from "next-themes"

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Points & Séances",
    description: "Suivez vos points et gérez les séances.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr" suppressHydrationWarning>
        <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <SWRProvider>
                <TopBar />
                <div className="min-h-dvh pt-14 bg-background text-foreground">
                    {children}
                </div>
                <Toaster />
            </SWRProvider>
        </ThemeProvider>
        </body>
        </html>
    );
}