"use client";

import useSWR from "swr";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SemestresApi } from "@/lib/api";
import { semestreLabel } from "@/lib/format";
import type { Semestre } from "@/lib/types";
import { cn } from "@/lib/utils";

export function useSemestres() {
    const { data = [], ...rest } = useSWR<Semestre[]>("/semestres", () => SemestresApi.list());
    return { semestres: data, actif: data.find((s) => s.actif) ?? data[0], ...rest };
}

export function SemestreSelect({
    value,
    onChange,
    allowAll = false,
    className,
    id,
}: {
    value: number | undefined;
    onChange: (id: number | undefined) => void;
    allowAll?: boolean;
    className?: string;
    id?: string;
}) {
    const { semestres } = useSemestres();
    return (
        <Select value={value ? String(value) : allowAll ? "all" : undefined} onValueChange={(v) => onChange(v === "all" ? undefined : Number(v))}>
            <SelectTrigger id={id} className={cn("sm:w-56", className)} aria-label="Semestre">
                <SelectValue placeholder="Choisir un semestre" />
            </SelectTrigger>
            <SelectContent>
                {allowAll && <SelectItem value="all">Tous les semestres</SelectItem>}
                {semestres.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                        {semestreLabel(s)} {s.actif ? "· en cours" : ""}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
