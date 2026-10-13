// src/components/semestres/SemestreForm.tsx
"use client";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SemestresApi } from "@/lib/api";

export default function SemestreForm({ onSuccess }: { onSuccess: () => void }) {
    const [annee, setAnnee] = useState<number>(new Date().getFullYear());
    const [numero, setNumero] = useState<number>(1);
    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        await SemestresApi.create({ annee, numero }); // POST /semestres  [oai_citation:29‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
        onSuccess();
    };
    return (
        <form onSubmit={submit} className="space-y-3">
            <Input type="number" value={annee} onChange={(e)=>setAnnee(+e.target.value)} placeholder="Année" required min={2000} max={2100}/>
            <Input type="number" value={numero} onChange={(e)=>setNumero(+e.target.value)} placeholder="Numéro (1 ou 2)" required min={1} max={2}/>
            <Button type="submit" className="w-full" disabled={numero < 1 || numero > 2}>Enregistrer</Button>
        </form>
    );
}