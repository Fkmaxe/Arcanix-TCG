// src/components/seances/SeanceForm.tsx
"use client";
import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SeancesApi, SemestresApi } from "@/lib/api";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

export default function SeanceForm({ onSuccess }: { onSuccess: () => void }) {
    const [nom, setNom] = useState("");
    const [date, setDate] = useState<string>(new Date().toISOString().slice(0,10));
    const [nb, setNb] = useState<number>(1.0);
    const [semestres, setSemestres] = useState<any[]>([]);
    const [semestre, setSemestre] = useState<number | undefined>();

    useEffect(()=>{ SemestresApi.list().then(setSemestres); },[]);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!semestre) return;
        await SeancesApi.create({ nom, date_seance: date, nb_point: nb, semestre_id: semestre }); // POST /seances  [oai_citation:31‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
        onSuccess();
    };

    return (
        <form onSubmit={submit} className="space-y-3">
            <Input placeholder="Nom" value={nom} onChange={e=>setNom(e.target.value)} required minLength={1}/>
            <Input type="date" value={date} onChange={e=>setDate(e.target.value)} required/>
            <Input type="number" value={nb} onChange={e=>setNb(+e.target.value)} placeholder="Points" required min={0} step={0.5}/>
            <Select onValueChange={(v)=>setSemestre(+v)} required>
                <SelectTrigger><SelectValue placeholder="Semestre"/></SelectTrigger>
                <SelectContent>
                    {semestres.map(s => <SelectItem key={s.id} value={String(s.id)}>{s.annee} - S{s.numero}</SelectItem>)}
                </SelectContent>
            </Select>
            <Button type="submit" className="w-full" disabled={!semestre || !nom}>Enregistrer</Button>
        </form>
    );
}