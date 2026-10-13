"use client";

import { useState } from "react";
import useSWR from "swr";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { UsersApi } from "@/lib/api";
import { initials } from "@/lib/format";
import { useDebounced } from "@/lib/hooks";
import type { User } from "@/lib/types";

export type MembreChoisi = Pick<User, "id" | "prenom" | "nom" | "classe">;

/** Recherche d'un membre (côté serveur) avec affichage du choix. */
export function MembrePicker({ value, onChange, id }: { value: MembreChoisi | null; onChange: (m: MembreChoisi | null) => void; id?: string }) {
    const [query, setQuery] = useState("");
    const q = useDebounced(query.trim(), 250);
    const { data, isLoading } = useSWR(value || !q ? null : ["/users", "picker", q], () => UsersApi.list({ q, limit: 8 }));

    if (value) {
        return (
            <div className="bg-surface/60 flex h-11 items-center gap-2 rounded-md border px-2 sm:h-10">
                <span className="bg-muted text-gold grid size-7 place-items-center rounded-full text-xs font-bold">{initials(value.prenom, value.nom)}</span>
                <span className="min-w-0 flex-1 truncate text-sm">{value.prenom} {value.nom} <span className="text-muted-foreground">· {value.classe}</span></span>
                <button type="button" onClick={() => onChange(null)} className="text-muted-foreground hover:text-foreground grid size-8 place-items-center" aria-label="Changer de membre">
                    <X className="size-4" />
                </button>
            </div>
        );
    }
    return (
        <div className="relative">
            <Search className="text-muted-foreground absolute top-3.5 left-3 size-4 sm:top-3" />
            <Input id={id} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Chercher un membre…" className="pl-9" autoComplete="off" />
            {q && (
                <ul className="bg-popover absolute inset-x-0 top-full z-20 mt-1 max-h-64 overflow-auto rounded-lg border shadow-xl" role="listbox">
                    {isLoading && <li className="text-muted-foreground p-3 text-sm">Recherche…</li>}
                    {!isLoading && !data?.items.length && <li className="text-muted-foreground p-3 text-sm">Aucun membre trouvé</li>}
                    {data?.items.map((u) => (
                        <li key={u.id}>
                            <button
                                type="button"
                                role="option"
                                aria-selected={false}
                                className="hover:bg-accent flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm"
                                onClick={() => { onChange(u); setQuery(""); }}
                            >
                                <span className="font-medium">{u.prenom} {u.nom}</span>
                                <span className="text-muted-foreground truncate text-xs">{u.classe} · {u.adresse_mail}</span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
