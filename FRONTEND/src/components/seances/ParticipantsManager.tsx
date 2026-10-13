// src/components/seances/ParticipantsManager.tsx
"use client";

import useSWR from "swr";
import { useEffect, useMemo, useState } from "react";
import { SeancesApi, UsersApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
} from "@/components/ui/avatar";
import { Loader2, Search, Trash2, UserPlus } from "lucide-react";
import { cn } from "@/lib/utils";

type Participant = {
    utilisateur_id: number;
    seance_id: number;
    present: boolean;
    commentaire?: string | null;
};
type User = {
    id: number;
    nom: string;
    prenom: string;
    adresse_mail: string;
    role_utilisateur: string;
    classe: string;
};

function initials(u?: User) {
    if (!u) return "??";
    const a = u.prenom?.[0] ?? "";
    const b = u.nom?.[0] ?? "";
    return (a + b).toUpperCase();
}

export default function ParticipantsManager({ seanceId }: { seanceId: number }) {
    const {
        data: participants = [],
        mutate,
        isLoading: loadingParticipants,
    } = useSWR<Participant[]>(
        `/seances/${seanceId}/participants`,
        () => SeancesApi.participants.list(seanceId)
    );

    const [open, setOpen] = useState(false);
    const [allUsers, setAllUsers] = useState<User[]>([]);
    const [loadingAction, setLoadingAction] = useState(false);
    const [query, setQuery] = useState("");

    const usersById = useMemo(
        () => new Map(allUsers.map((u) => [u.id, u])),
        [allUsers]
    );

    const filteredUsers = useMemo(() => {
        if (!query.trim()) return [];
        const q = query.toLowerCase();
        return allUsers
            .filter(
                (u) =>
                    u.adresse_mail.toLowerCase().includes(q) ||
                    `${u.prenom} ${u.nom}`.toLowerCase().includes(q)
            )
            .slice(0, 10);
    }, [allUsers, query]);

    const stats = useMemo(() => {
        const present = participants.filter(p => p.present).length;
        const absent = participants.length - present;
        return { present, absent, total: participants.length };
    }, [participants]);

    useEffect(() => {
        if (!open) return;
        UsersApi.list()
            .then(setAllUsers)
            .catch(() => setAllUsers([]));
    }, [open]);

    const togglePresence = async (uid: number, present: boolean) => {
        const next = participants.map((p) =>
            p.utilisateur_id === uid ? { ...p, present } : p
        );
        mutate(next, { revalidate: false });
        await SeancesApi.participants.patch(seanceId, uid, { present });
        mutate();
    };

    const addUser = async (uid: number) => {
        if (participants.some((p) => p.utilisateur_id === uid)) return;
        setLoadingAction(true);
        const optimistic: Participant = {
            utilisateur_id: uid,
            seance_id: seanceId,
            present: true,
        };
        mutate([optimistic, ...participants], { revalidate: false });
        await SeancesApi.participants.add(seanceId, optimistic);
        await mutate();
        setQuery("");
        setLoadingAction(false);
    };

    const remove = async (uid: number) => {
        setLoadingAction(true);
        const next = participants.filter((p) => p.utilisateur_id !== uid);
        mutate(next, { revalidate: false });
        await SeancesApi.participants.remove(seanceId, uid);
        await mutate();
        setLoadingAction(false);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="secondary" size="sm">
                    Participants
                </Button>
            </DialogTrigger>

            <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden p-0">
                <div className="flex flex-col h-full max-h-[85vh] p-4 md:p-6 gap-4">
                    <DialogHeader className="space-y-1 flex-shrink-0">
                        <DialogTitle>Gérer les participants</DialogTitle>
                        <DialogDescription>
                            Ajouter/retirer des utilisateurs et marquer la présence.
                        </DialogDescription>
                    </DialogHeader>

                    {/* Barre d'ajout */}
                    <div className="rounded-xl border p-2 sm:p-3 md:p-4 bg-muted/10 flex-shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder='Chercher par email ou "Prénom Nom"...'
                                className="pl-8"
                            />
                        </div>
                        <Button
                            variant="default"
                            size="sm"
                            disabled={!filteredUsers[0] || loadingAction}
                            onClick={() => filteredUsers[0] && addUser(filteredUsers[0].id)}
                        >
                            {loadingAction ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <UserPlus className="mr-2 h-4 w-4" />
                            )}
                            Ajouter
                        </Button>
                    </div>

                    {query && (
                        <>
                            <Separator className="my-3" />
                            <div className="max-h-48 overflow-auto">
                                <div className="grid gap-2 sm:grid-cols-2 pr-2">
                                    {filteredUsers.length === 0 && (
                                        <p className="text-sm text-muted-foreground col-span-2">
                                            Aucun utilisateur trouvé.
                                        </p>
                                    )}
                                    {filteredUsers.map((u) => {
                                        const alreadyAdded = participants.some(p => p.utilisateur_id === u.id);
                                        return (
                                        <div
                                            key={u.id}
                                            className={cn(
                                                "flex items-center justify-between rounded-lg border p-2 bg-background transition",
                                                alreadyAdded ? "opacity-50 cursor-not-allowed" : "hover:bg-accent/10 cursor-pointer"
                                            )}
                                        >
                                            <div className="flex items-center gap-3">
                                                <Avatar className="h-8 w-8">
                                                    <AvatarImage alt={`${u.prenom} ${u.nom}`} />
                                                    <AvatarFallback>{initials(u)}</AvatarFallback>
                                                </Avatar>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium leading-none truncate">
                                                        {u.prenom} {u.nom}
                                                        {alreadyAdded && <span className="ml-2 text-xs text-muted-foreground">(déjà ajouté)</span>}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground truncate">
                                                        {u.adresse_mail}
                                                    </p>
                                                </div>
                                            </div>
                                            <Button
                                                size="icon"
                                                variant="ghost"
                                                onClick={() => !alreadyAdded && addUser(u.id)}
                                                disabled={alreadyAdded}
                                            >
                                                <UserPlus className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    );
                                })}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                    {/* Liste des participants (scrollable) */}
                    <div className="rounded-xl border bg-muted/10 flex flex-col overflow-hidden flex-1 min-h-0">
                        <div className="flex items-center justify-between p-2 sm:p-3 md:p-4 flex-shrink-0">
                            <div className="flex items-center gap-4">
                                <p className="text-sm text-muted-foreground">
                                    {stats.total} participant{stats.total > 1 ? "s" : ""}
                                </p>
                                {stats.total > 0 && (
                                    <div className="flex items-center gap-2 text-xs">
                                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                            {stats.present} présent{stats.present > 1 ? "s" : ""}
                                        </Badge>
                                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                                            {stats.absent} absent{stats.absent > 1 ? "s" : ""}
                                        </Badge>
                                    </div>
                                )}
                            </div>
                        </div>
                        <Separator className="flex-shrink-0" />
                        <div className="overflow-auto flex-1" style={{ maxHeight: "400px" }}>
                            <div className="divide-y">
                            {loadingParticipants ? (
                                Array.from({ length: 4 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center justify-between p-2 sm:p-3 md:p-4 animate-pulse"
                                    >
                                        <div className="flex items-center gap-2 sm:gap-3">
                                            <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-muted flex-shrink-0" />
                                            <div className="space-y-2">
                                                <div className="h-3 w-32 sm:w-40 rounded bg-muted" />
                                                <div className="h-2 w-20 sm:w-24 rounded bg-muted" />
                                            </div>
                                        </div>
                                        <div className="h-8 w-12 sm:w-16 rounded bg-muted flex-shrink-0" />
                                    </div>
                                ))
                            ) : participants.length === 0 ? (
                                <div className="p-6 text-sm text-muted-foreground text-center">
                                    Aucun participant pour cette séance.
                                </div>
                            ) : (
                                participants.map((p) => {
                                    const u = usersById.get(p.utilisateur_id);
                                    const label = u
                                        ? `${u.prenom} ${u.nom}`
                                        : `Utilisateur #${p.utilisateur_id}`;

                                    return (
                                        <div
                                            key={p.utilisateur_id}
                                            className="flex items-center justify-between gap-2 p-2 sm:p-3 md:p-4 hover:bg-accent/10 transition"
                                        >
                                            <div className="flex min-w-0 items-center gap-2 sm:gap-3 flex-1 overflow-hidden">
                                                <Avatar className="h-7 w-7 sm:h-8 sm:w-8 flex-shrink-0">
                                                    <AvatarImage alt={label} />
                                                    <AvatarFallback>{initials(u)}</AvatarFallback>
                                                </Avatar>
                                                <div className="min-w-0 flex-1 overflow-hidden">
                                                    <div className="flex items-center gap-1 sm:gap-2 overflow-hidden">
                                                        <p className="truncate font-medium text-xs sm:text-sm" title={label}>{label}</p>
                                                        {!!u?.role_utilisateur && (
                                                            <Badge variant="outline" className="hidden md:inline-flex text-xs flex-shrink-0">
                                                                {u.role_utilisateur}
                                                            </Badge>
                                                        )}
                                                        {!!u?.classe && (
                                                            <Badge variant="secondary" className="hidden lg:inline-flex text-xs flex-shrink-0">
                                                                {u.classe}
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className="truncate text-xs text-muted-foreground" title={u?.adresse_mail}>
                                                        {u?.adresse_mail ?? "—"}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                                                <div className="flex items-center gap-1 sm:gap-2">
                                                    <Checkbox
                                                        checked={p.present}
                                                        onCheckedChange={(v) =>
                                                            togglePresence(p.utilisateur_id, !!v)
                                                        }
                                                        aria-label={`Présence de ${label}`}
                                                    />
                                                    <span className="text-xs sm:text-sm hidden sm:inline">Présent</span>
                                                </div>
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    disabled={loadingAction}
                                                    onClick={() => remove(p.utilisateur_id)}
                                                    className="h-8 w-8 sm:h-9 sm:w-9"
                                                >
                                                    {loadingAction ? (
                                                        <Loader2 className="h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
                                                    ) : (
                                                        <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                                                    )}
                                                </Button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                            </div>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}