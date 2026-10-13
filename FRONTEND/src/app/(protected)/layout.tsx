// src/app/(protected)/layout.tsx
"use client";

import AuthGuard from "@/components/common/AuthGuard";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
    return <AuthGuard>{children}</AuthGuard>;
}
