// src/app/(protected)/admin/users/page.tsx
"use client";
import useSWR from "swr";
import { UsersApi } from "@/lib/api";
import { DataTable } from "@/components/common/DataTable";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import {
    Dialog, DialogContent, DialogHeader, DialogTrigger,
    DialogTitle, DialogDescription
} from "@/components/ui/dialog"; // 👈 ajoute Title/Description
import UserForm from "@/components/users/UserForm";
import UserEditForm from "@/components/users/UserEditForm";
import { RoleGate } from "@/lib/auth";
import {
    AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
    AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger
} from "@/components/ui/alert-dialog";

export default function AdminUsersPage() {
    const { data: users = [], mutate, isLoading, error } = useSWR("/users", () => UsersApi.list());
    const [openCreate, setOpenCreate] = useState(false);
    const [editUser, setEditUser] = useState<any | null>(null);

    return (
        <RoleGate allow={["admin"]}>
            <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold">Utilisateurs</h1>

                    {/* Créer */}
                    <Dialog open={openCreate} onOpenChange={setOpenCreate}>
                        <DialogTrigger asChild><Button>Nouveau</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Créer un utilisateur</DialogTitle>
                                <DialogDescription>
                                    Renseignez les informations de l’utilisateur puis validez.
                                </DialogDescription>
                            </DialogHeader>
                            <UserForm onSuccess={() => { setOpenCreate(false); mutate(); }} />
                        </DialogContent>
                    </Dialog>
                </div>

                {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">Erreur lors du chargement des utilisateurs. Veuillez réessayer.</p>
                    </div>
                )}

                <DataTable
                    isLoading={isLoading}
                    columns={[
                        { key: "id", header: "ID" },
                        { key: "nom", header: "Nom" },
                        { key: "prenom", header: "Prénom" },
                        { key: "adresse_mail", header: "Email" },
                        { key: "classe", header: "Classe" },
                        { key: "role_utilisateur", header: "Rôle" },
                        {
                            key: "actions",
                            header: "",
                            render: (row: any) => (
                                <div className="flex gap-2 justify-end">
                                    {/* Modifier */}
                                    <Button size="sm" variant="outline" onClick={() => setEditUser(row)}>
                                        Modifier
                                    </Button>

                                    {/* Supprimer */}
                                    <AlertDialog>
                                        <AlertDialogTrigger asChild>
                                            <Button size="sm" variant="destructive">Supprimer</Button>
                                        </AlertDialogTrigger>
                                        <AlertDialogContent>
                                            <AlertDialogHeader>
                                                <AlertDialogTitle>
                                                    Supprimer {row.prenom} {row.nom} ?
                                                </AlertDialogTitle>
                                            </AlertDialogHeader>
                                            <AlertDialogFooter>
                                                <AlertDialogCancel>Annuler</AlertDialogCancel>
                                                <AlertDialogAction
                                                    onClick={async () => {
                                                        await UsersApi.remove(row.id);
                                                        mutate();
                                                    }}
                                                >
                                                    Confirmer
                                                </AlertDialogAction>
                                            </AlertDialogFooter>
                                        </AlertDialogContent>
                                    </AlertDialog>
                                </div>
                            ),
                        },
                    ]}
                    rows={users}
                />

                {/* Dialog d'édition */}
                <Dialog open={!!editUser} onOpenChange={(v) => !v && setEditUser(null)}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Modifier l’utilisateur</DialogTitle>
                            <DialogDescription>
                                Mettez à jour les informations puis enregistrez.
                            </DialogDescription>
                        </DialogHeader>
                        {editUser && (
                            <UserEditForm
                                user={editUser}
                                onSuccess={() => { setEditUser(null); mutate(); }}
                            />
                        )}
                    </DialogContent>
                </Dialog>
            </div>
        </RoleGate>
    );
}