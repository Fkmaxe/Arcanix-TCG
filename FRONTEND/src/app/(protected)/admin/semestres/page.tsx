// src/app/admin/semestres/page.tsx
"use client";
import useSWR from "swr";
import { SemestresApi } from "@/lib/api";
import { DataTable } from "@/components/common/DataTable";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import SemestreForm from "@/components/semestres/SemestreForm";
import { RoleGate } from "@/lib/auth";

export default function AdminSemestresPage() {
    const { data: semestres = [], mutate, isLoading, error } = useSWR("/semestres", () => SemestresApi.list()); // GET /semestres  [oai_citation:28‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    return (
        <RoleGate allow={["admin"]}>
            <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold">Semestres</h1>
                    <Dialog>
                        <DialogTrigger asChild><Button>Nouveau</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Créer un semestre</DialogTitle>
                                <DialogDescription>Ajoutez un nouveau semestre académique</DialogDescription>
                            </DialogHeader>
                            <SemestreForm onSuccess={mutate}/>
                        </DialogContent>
                    </Dialog>
                </div>

                {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">Erreur lors du chargement des semestres. Veuillez réessayer.</p>
                    </div>
                )}

                <DataTable
                    isLoading={isLoading}
                    columns={[{key:"id",header:"ID"},{key:"annee",header:"Année"},{key:"numero",header:"N°"}]}
                    rows={semestres}
                />
            </div>
        </RoleGate>
    );
}