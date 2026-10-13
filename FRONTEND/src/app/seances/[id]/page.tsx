"use client";

import Link from "next/link";
import { use, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { ArrowLeft, CalendarDays, CheckCircle2, Clock, Flame, MapPin, Pencil, Trash2, Users, XCircle } from "lucide-react";
import { toast } from "sonner";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { SectionTitle } from "@/components/common/PageHeader";
import { ErrorBox, FullPageLoader } from "@/components/common/States";
import { AppelPresence } from "@/components/seances/AppelPresence";
import { JeuBadge } from "@/components/seances/JeuBadge";
import SeanceForm from "@/components/seances/SeanceForm";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { SeancesApi } from "@/lib/api";
import { isStaff, useAuth } from "@/lib/auth";
import { formatDate, formatHeure, formatPoints, relativeDay, semestreLabel, todayIso } from "@/lib/format";
import { errorMessage } from "@/lib/swr";

export default function SeanceDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const sid = Number(id);
    const { me, token, ready } = useAuth();
    const router = useRouter();
    const staff = isStaff(me);
    const [edit, setEdit] = useState(false);
    // La clé inclut le jeton : la vue change selon qu'on est connecté (participants, ma présence)
    const { data: seance, error, mutate } = useSWR(ready ? ["/seances", sid, token] : null, () => SeancesApi.get(sid));

    if (error) {
        return (
            <div className="space-y-4">
                <Button asChild variant="ghost" size="sm"><Link href="/seances"><ArrowLeft /> Séances</Link></Button>
                <ErrorBox message={errorMessage(error)} onRetry={() => mutate()} />
            </div>
        );
    }
    if (!seance) return <FullPageLoader />;

    const rel = relativeDay(seance.date_seance);
    const passee = seance.date_seance < todayIso();
    const heure = formatHeure(seance.heure_debut);

    return (
        <div className="space-y-6">
            <Button asChild variant="ghost" size="sm" className="-ml-2">
                <Link href="/seances"><ArrowLeft /> Séances</Link>
            </Button>

            <OrnateCard>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                            <JeuBadge jeu={seance.jeu} />
                            {rel && <span className="text-ember text-xs font-semibold uppercase">{rel}</span>}
                            {passee && <span className="text-muted-foreground text-xs">Terminée</span>}
                        </div>
                        <h1 className="text-gilded text-2xl font-bold break-words sm:text-3xl">{seance.nom}</h1>
                        <ul className="text-muted-foreground mt-3 space-y-1.5 text-sm">
                            <li className="flex items-center gap-2"><CalendarDays className="text-gold size-4" /> <span className="first-letter:uppercase">{formatDate(seance.date_seance, "long")}</span></li>
                            {heure && <li className="flex items-center gap-2"><Clock className="text-gold size-4" /> {heure}</li>}
                            {seance.lieu && <li className="flex items-center gap-2"><MapPin className="text-gold size-4" /> {seance.lieu}</li>}
                            <li className="flex items-center gap-2"><Users className="text-gold size-4" /> {seance.nb_presents} présent{seance.nb_presents > 1 ? "s" : ""} · semestre {semestreLabel(seance.semestre)}</li>
                        </ul>
                    </div>
                    <div className="frame-gilded flex shrink-0 items-center gap-3 self-start rounded-xl px-4 py-3">
                        <Flame className="text-ember size-7" />
                        <div>
                            <p className="font-display text-gilded text-3xl leading-none font-bold">+{formatPoints(seance.nb_point)}</p>
                            <p className="text-muted-foreground text-xs">points par présence</p>
                        </div>
                    </div>
                </div>
                {seance.description && <p className="mt-5 text-sm leading-relaxed whitespace-pre-line">{seance.description}</p>}

                {me && seance.ma_participation !== null && (
                    <div className={`mt-5 flex items-center gap-2 rounded-lg border p-3 text-sm ${seance.ma_participation ? "border-success/30 bg-success/10 text-success" : "border-destructive/30 bg-destructive/10 text-destructive"}`}>
                        {seance.ma_participation ? <><CheckCircle2 className="size-4" /> Ta présence est validée : +{formatPoints(seance.nb_point)} pts</> : <><XCircle className="size-4" /> Tu étais inscrit·e mais noté·e absent·e</>}
                    </div>
                )}

                {staff && (
                    <div className="mt-5 flex flex-wrap gap-2 border-t pt-4">
                        <Button variant="outline" size="sm" onClick={() => setEdit(true)}><Pencil /> Modifier</Button>
                        <ConfirmButton
                            title={`Supprimer « ${seance.nom} » ?`}
                            description={`Les ${seance.nb_participants} participation(s) et les points associés seront supprimés.`}
                            confirmLabel="Supprimer"
                            onConfirm={async () => {
                                try {
                                    await SeancesApi.remove(seance.id);
                                    toast.success("Séance supprimée");
                                    router.replace("/seances");
                                } catch (err) {
                                    toast.error(errorMessage(err));
                                }
                            }}
                        >
                            <Button variant="ghost" size="sm" className="text-destructive"><Trash2 /> Supprimer</Button>
                        </ConfirmButton>
                    </div>
                )}
            </OrnateCard>

            {staff && (
                <section>
                    <SectionTitle>Appel des présences</SectionTitle>
                    <AppelPresence seance={seance} onSaved={(s) => mutate(s, { revalidate: false })} />
                </section>
            )}

            {!me && (
                <p className="text-muted-foreground text-center text-sm">
                    <Link href={`/login?next=/seances/${seance.id}`} className="text-gold underline">Connecte-toi</Link> pour voir ta participation.
                </p>
            )}

            <Dialog open={edit} onOpenChange={setEdit}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Modifier la séance</DialogTitle></DialogHeader>
                    <SeanceForm seance={seance} onSuccess={() => { setEdit(false); mutate(); }} />
                </DialogContent>
            </Dialog>
        </div>
    );
}
