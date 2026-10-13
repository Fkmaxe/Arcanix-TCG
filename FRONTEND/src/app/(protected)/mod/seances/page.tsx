// src/app/mod/seances/page.tsx
"use client";
import useSWR from "swr";
import { SeancesApi, SemestresApi } from "@/lib/api";
import { RoleGate } from "@/lib/auth";
import { DataTable } from "@/components/common/DataTable";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import SeanceForm from "@/components/seances/SeanceForm";
import ParticipantsManager from "@/components/seances/ParticipantsManager";
import { useState } from "react";

export default function ModSeancesPage() {
    const { data: seances = [], mutate, isLoading, error } = useSWR("/seances", () => SeancesApi.list()); // GET /seances  [oai_citation:30‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    const [openForm, setOpenForm] = useState(false);

    return (
        <RoleGate allow={["moderator","admin"]}>
            <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold">Séances</h1>
                    <Dialog open={openForm} onOpenChange={setOpenForm}>
                        <DialogTrigger asChild><Button>Nouvelle séance</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Créer une séance</DialogTitle>
                                <DialogDescription>Ajoutez une nouvelle séance avec ses points</DialogDescription>
                            </DialogHeader>
                            <SeanceForm onSuccess={()=>{ setOpenForm(false); mutate(); }}/>
                        </DialogContent>
                    </Dialog>
                </div>

                {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">Erreur lors du chargement des séances. Veuillez réessayer.</p>
                    </div>
                )}

                <DataTable
                    isLoading={isLoading}
                    columns={[
                        { key:"id", header:"ID" },
                        { key:"nom", header:"Nom" },
                        { key:"date_seance", header:"Date", render: (s:any) => new Date(s.date_seance).toLocaleDateString('fr-FR') },
                        { key:"nb_point", header:"Points" },
                        { key:"semestre_id", header:"Semestre" },
                        { key:"actions", header:"Actions", render: (s:any)=>(<ParticipantsManager seanceId={s.id}/>) },
                    ]}
                    rows={seances}
                />
            </div>
        </RoleGate>
    );
}