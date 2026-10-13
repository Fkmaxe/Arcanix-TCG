// src/app/dashboard/page.tsx
"use client";
import { RoleGate } from "@/lib/auth";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

export default function Dashboard() {
    return (
        <div className="p-6 grid gap-4 md:grid-cols-3">
            <Card><CardContent className="p-4"><Link href="/me">Mon espace</Link></CardContent></Card>

            <RoleGate allow={["moderator","admin"]}>
                <Card><CardContent className="p-4"><Link href="/mod/seances">Gérer les séances</Link></CardContent></Card>
            </RoleGate>

            <RoleGate allow={["moderator","admin"]}>
                <Card><CardContent className="p-4"><Link href="/exports">Exports</Link></CardContent></Card>
            </RoleGate>

            <RoleGate allow={["admin"]}>
                <Card><CardContent className="p-4"><Link href="/admin/users">Utilisateurs</Link></CardContent></Card>
                <Card><CardContent className="p-4"><Link href="/admin/semestres">Semestres</Link></CardContent></Card>
            </RoleGate>
        </div>
    );
}