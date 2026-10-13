// src/components/providers/SWRProvider.tsx
"use client";

import { SWRConfig } from "swr";
import { ThemeProvider } from "next-themes";
import { fetcher } from "@/lib/swr";
import { AuthProvider } from "@/lib/auth";

export default function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} themes={["dark", "light"]}>
            <SWRConfig value={{ fetcher, revalidateOnFocus: false, keepPreviousData: true }}>
                <AuthProvider>{children}</AuthProvider>
            </SWRConfig>
        </ThemeProvider>
    );
}
