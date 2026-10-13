"use client";

import { useState } from "react";
import useSWR from "swr";
import { CalendarRange, Crown, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { RequireRole } from "@/components/common/AuthGuard";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorBox, Skeleton } from "@/components/common/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SemestresApi } from "@/lib/api";
import { semestreLabel } from "@/lib/format";
import { errorMessage } from "@/lib/swr";
import type { Semestre } from "@/lib/types";

function SemestreForm({ semestre, onSuccess }: { semestre?: Semestre; onSuccess: () => void }) {
    const [annee, setAnnee] = useState(String(semestre?.annee ?? new Date().getFullYear()));
    const [numero, setNumero] = useState(String(semestre?.numero ?? 1));
    const [loading, setLoading] = useState(false);
    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const body = { annee: Number(annee), numero: Number(numero) };
            if (semestre) await SemestresApi.update(semestre.id, body);
            else await SemestresApi.create(body);
            toast.success(semestre ? "Semestre modifié" : "Semestre créé");
            onSuccess();
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };
    return (
        <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="sem-annee">Année</Label>
                    <Input id="sem-annee" type="number" inputMode="numeric" min={2000} max={2100} value={annee} onChange={(e) => setAnnee(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="sem-num">Semestre</Label>
                    <Select value={numero} onValueChange={setNumero}>
                        <SelectTrigger id="sem-num"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="1">S1</SelectItem>
                            <SelectItem value="2">S2</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
                {loading && <Loader2 className="animate-spin" />} Enregistrer
            </Button>
        </form>
    );
}

export default function GestionSemestresPage() {
    const { data, error, isLoading, mutate } = useSWR("/semestres", () => SemestresApi.list());
    const [editing, setEditing] = useState<Semestre | "new" | null>(null);

    const act = async (fn: () => Promise<unknown>, ok: string) => {
        try {
            await fn();
            toast.success(ok);
            mutate();
        } catch (err) {
            toast.error(errorMessage(err));
        }
    };

    return (
        <RequireRole allow={["admin"]}>
            <div className="space-y-5">
                <PageHeader
                    eyebrow="Gestion"
                    title="Semestres"
                    description="Le semestre en cours sert au classement et aux points affichés sur Discord."
                    actions={<Button onClick={() => setEditing("new")} className="w-full sm:w-auto"><Plus /> Nouveau semestre</Button>}
                />
                {error && <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />}
                {isLoading && !data ? (
                    <Skeleton className="h-40" />
                ) : !data?.length ? (
                    <EmptyState icon={<CalendarRange />} title="Aucun semestre" description="Crée le premier semestre pour pouvoir programmer des séances." />
                ) : (
                    <ul className="grid gap-3 sm:grid-cols-2">
                        {data.map((s) => (
                            <li key={s.id} className={`bg-card flex flex-col gap-3 rounded-xl border p-4 ${s.actif ? "frame-gilded" : ""}`}>
                                <div className="flex items-center justify-between gap-2">
                                    <p className="font-display text-xl font-bold">{semestreLabel(s)}</p>
                                    {s.actif && <Badge variant="gold"><Crown /> En cours</Badge>}
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {!s.actif && (
                                        <ConfirmButton
                                            title={`Passer au semestre ${semestreLabel(s)} ?`}
                                            description="Le semestre actuel sera clôturé et son podium annoncé sur Discord."
                                            confirmLabel="Activer"
                                            destructive={false}
                                            onConfirm={() => act(() => SemestresApi.activer(s.id), `${semestreLabel(s)} est le semestre en cours`)}
                                        >
                                            <Button size="sm" variant="gold"><Crown /> Définir en cours</Button>
                                        </ConfirmButton>
                                    )}
                                    <Button size="sm" variant="outline" onClick={() => setEditing(s)}><Pencil /> Modifier</Button>
                                    {!s.actif && (
                                        <ConfirmButton
                                            title={`Supprimer ${semestreLabel(s)} ?`}
                                            description="Impossible si des séances y sont rattachées."
                                            confirmLabel="Supprimer"
                                            onConfirm={() => act(() => SemestresApi.remove(s.id), "Semestre supprimé")}
                                        >
                                            <Button size="sm" variant="ghost" className="text-destructive"><Trash2 /> Supprimer</Button>
                                        </ConfirmButton>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                )}

                <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{editing === "new" ? "Nouveau semestre" : "Modifier le semestre"}</DialogTitle>
                            <DialogDescription>Un seul S1 et un seul S2 par année.</DialogDescription>
                        </DialogHeader>
                        {editing && <SemestreForm semestre={editing === "new" ? undefined : editing} onSuccess={() => { setEditing(null); mutate(); }} />}
                    </DialogContent>
                </Dialog>
            </div>
        </RequireRole>
    );
}
