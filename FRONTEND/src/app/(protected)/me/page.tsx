// src/app/me/page.tsx
"use client";
import useSWR from "swr";
import { MeApi, SemestresApi } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/common/DataTable";

export default function MePage() {
    const { data: points } = useSWR("/me/points", () => MeApi.points()); // GET /me/points  [oai_citation:36‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    const [semestres, setSemestres] = useState<any[]>([]);
    const [sid, setSid] = useState<number|undefined>();
    const { data: parts = [] } = useSWR(`/me/participations?sid=${sid??""}`, () => MeApi.participations(sid)); // GET /me/participations  [oai_citation:37‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)

    useEffect(()=>{ SemestresApi.list().then(setSemestres); },[]);
    return (
        <div className="p-6 grid gap-6 md:grid-cols-2">
            <Card>
                <CardHeader>Mes points</CardHeader>
                <CardContent className="space-y-2">
                    <div className="text-3xl font-semibold">{points?.total ?? 0}</div>
                    <div className="space-y-1">
                        {points?.semestres?.map((s:any)=>(
                            <div key={s.semestre_id} className="flex justify-between text-sm">
                                <span>{s.annee} - S{s.numero}</span><span>{s.points}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>Mes participations</CardHeader>
                <CardContent className="space-y-3">
                    <Select onValueChange={v=>setSid(+v)}>
                        <SelectTrigger><SelectValue placeholder="Filtrer par semestre" /></SelectTrigger>
                        <SelectContent>
                            {semestres.map(s=> <SelectItem key={s.id} value={String(s.id)}>{s.annee} - S{s.numero}</SelectItem>)}
                        </SelectContent>
                    </Select>
                    <DataTable
                        columns={[
                            { key:"seance_id", header:"Séance" },
                            { key:"present", header:"Présent" },
                            { key:"commentaire", header:"Commentaire" },
                        ]}
                        rows={parts}
                    />
                </CardContent>
            </Card>
        </div>
    );
}