"use client";

import { RequireRole } from "@/components/common/AuthGuard";

export default function GestionLayout({ children }: { children: React.ReactNode }) {
    return <RequireRole allow={["moderator", "admin"]}>{children}</RequireRole>;
}
