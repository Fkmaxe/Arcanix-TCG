"use client";

import { useState } from "react";
import useSWR from "swr";
import { Copy, KeyRound, MessageCircle, MoreVertical, Pencil, Plus, Search, Trash2, Users } from "lucide-react";
import { toast } from "sonner";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { DataTable, Pagination } from "@/components/common/DataTable";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorBox } from "@/components/common/States";
import UserForm from "@/components/users/UserForm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UsersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { initials, ROLE_LABELS } from "@/lib/format";
import { useDebounced } from "@/lib/hooks";
import { errorMessage } from "@/lib/swr";
import type { User } from "@/lib/types";

const LIMIT = 25;

function RoleBadge({ role }: { role: User["role_utilisateur"] }) {
    const variant = role === "admin" ? "ember" : role === "moderator" ? "gold" : "outline";
    return <Badge variant={variant}>{ROLE_LABELS[role]}</Badge>;
}

export default function GestionMembresPage() {
    const { me } = useAuth();
    const admin = me?.role_utilisateur === "admin";
    const [query, setQuery] = useState("");
    const [role, setRole] = useState<string>("tous");
    const [page, setPage] = useState(1);
    const [editing, setEditing] = useState<User | "new" | null>(null);
    const [lien, setLien] = useState<{ user: User; url: string; heures: number } | null>(null);
    const q = useDebounced(query.trim());
    const params = { q, role: role === "tous" ? undefined : role, page, limit: LIMIT };
    const { data, error, isLoading, mutate } = useSWR(["/users", params], () => UsersApi.list(params));

    // Un modérateur ne gère que les membres (et lui-même)
    const peutGerer = (u: User) => admin || u.role_utilisateur === "user" || u.id === me?.id;

    const genererLien = async (u: User) => {
        try {
            const r = await UsersApi.lienMotDePasse(u.id);
            setLien({ user: u, url: r.url, heures: r.expire_dans_heures });
        } catch (err) {
            toast.error(errorMessage(err));
        }
    };

    const actions = (u: User) =>
        peutGerer(u) && (
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button size="icon-sm" variant="ghost" aria-label={`Actions pour ${u.prenom} ${u.nom}`} onClick={(e) => e.stopPropagation()}>
                        <MoreVertical />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => setEditing(u)}><Pencil /> Modifier</DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => genererLien(u)}><KeyRound /> Lien de mot de passe</DropdownMenuItem>
                    {admin && u.id !== me?.id && (
                        <>
                            <DropdownMenuSeparator />
                            <ConfirmButton
                                title={`Supprimer ${u.prenom} ${u.nom} ?`}
                                description="Son compte et toutes ses participations seront définitivement supprimés."
                                confirmLabel="Supprimer"
                                onConfirm={async () => {
                                    try {
                                        await UsersApi.remove(u.id);
                                        toast.success("Membre supprimé");
                                        mutate();
                                    } catch (err) {
                                        toast.error(errorMessage(err));
                                    }
                                }}
                            >
                                <DropdownMenuItem variant="destructive" onSelect={(e) => e.preventDefault()}><Trash2 /> Supprimer</DropdownMenuItem>
                            </ConfirmButton>
                        </>
                    )}
                </DropdownMenuContent>
            </DropdownMenu>
        );

    return (
        <div className="space-y-5">
            <PageHeader
                eyebrow="Gestion"
                title="Membres"
                description={data ? `${data.total} membre${data.total > 1 ? "s" : ""}` : undefined}
                actions={<Button onClick={() => setEditing("new")} className="w-full sm:w-auto"><Plus /> Nouveau membre</Button>}
            />
            <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                    <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                    <Input type="search" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} placeholder="Nom, email, classe…" className="pl-9" />
                </div>
                <Select value={role} onValueChange={(v) => { setRole(v); setPage(1); }}>
                    <SelectTrigger className="sm:w-48" aria-label="Rôle"><SelectValue /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="tous">Tous les rôles</SelectItem>
                        <SelectItem value="user">Membres</SelectItem>
                        <SelectItem value="moderator">Modérateurs</SelectItem>
                        <SelectItem value="admin">Admins</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}

            <DataTable
                isLoading={isLoading}
                rows={data?.items ?? []}
                rowKey={(u) => u.id}
                empty="Aucun membre trouvé"
                emptyIcon={<Users />}
                mobileCard={(u) => (
                    <div className="bg-card flex items-center gap-3 rounded-xl border p-3">
                        <div className="bg-muted text-gold grid size-10 shrink-0 place-items-center rounded-full text-sm font-bold">{initials(u.prenom, u.nom)}</div>
                        <div className="min-w-0 flex-1">
                            <p className="flex items-center gap-2 truncate text-sm font-medium">
                                {u.prenom} {u.nom} {u.discord_id && <MessageCircle className="text-muted-foreground size-3.5" aria-label="Discord lié" />}
                            </p>
                            <p className="text-muted-foreground truncate text-xs">{u.adresse_mail}</p>
                            <div className="mt-1 flex items-center gap-2 text-xs"><RoleBadge role={u.role_utilisateur} /><span className="text-muted-foreground">{u.classe}</span></div>
                        </div>
                        {actions(u)}
                    </div>
                )}
                columns={[
                    { key: "nom", header: "Membre", render: (u) => <span className="font-medium">{u.prenom} {u.nom}</span> },
                    { key: "mail", header: "Email", render: (u) => <span className="text-muted-foreground">{u.adresse_mail}</span> },
                    { key: "classe", header: "Classe", render: (u) => u.classe },
                    { key: "role", header: "Rôle", render: (u) => <RoleBadge role={u.role_utilisateur} /> },
                    { key: "discord", header: "Discord", render: (u) => (u.discord_id ? <Badge variant="success">Lié</Badge> : <span className="text-muted-foreground">—</span>) },
                    { key: "actions", header: "", className: "text-right", render: actions },
                ]}
            />
            <Pagination page={page} total={data?.total ?? 0} limit={LIMIT} onPage={setPage} />

            <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editing === "new" ? "Nouveau membre" : "Modifier le membre"}</DialogTitle>
                        <DialogDescription>
                            {editing === "new" ? "Astuce : les membres peuvent aussi s'inscrire seuls avec /register sur Discord." : "Les modifications sont immédiates."}
                        </DialogDescription>
                    </DialogHeader>
                    {editing && (
                        <UserForm user={editing === "new" ? undefined : editing} onSuccess={() => { setEditing(null); mutate(); }} />
                    )}
                </DialogContent>
            </Dialog>

            <Dialog open={!!lien} onOpenChange={(o) => !o && setLien(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Lien de mot de passe</DialogTitle>
                        <DialogDescription>
                            À transmettre à {lien?.user.prenom} en message privé. Valable {lien?.heures} h, utilisable une seule fois.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="bg-muted rounded-lg p-3 font-mono text-xs break-all select-all">{lien?.url}</div>
                    <Button
                        onClick={async () => {
                            try {
                                await navigator.clipboard.writeText(lien?.url ?? "");
                                toast.success("Lien copié");
                            } catch {
                                toast.error("Copie impossible : sélectionne le lien à la main.");
                            }
                        }}
                    >
                        <Copy /> Copier le lien
                    </Button>
                </DialogContent>
            </Dialog>
        </div>
    );
}
