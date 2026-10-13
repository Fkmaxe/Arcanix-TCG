"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import useSWR from "swr";
import { QRCodeSVG } from "qrcode.react";
import { ArrowLeft, ClipboardCheck, Expand, Loader2, Lock, QrCode, Users } from "lucide-react";
import { toast } from "sonner";
import AuthGuard, { RequireRole } from "@/components/common/AuthGuard";
import { FullPageLoader } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { SeancesApi } from "@/lib/api";
import { formatHeure } from "@/lib/format";
import { errorMessage } from "@/lib/swr";

function EcranQr({ sid }: { sid: number }) {
    const { data: seance } = useSWR(["/seances", sid, "qr"], () => SeancesApi.get(sid));
    // Rafraîchi toutes les 2 s : nouveau code à chaque période et pointés en direct
    const { data: info, mutate } = useSWR(["/seances", sid, "pointage"], () => SeancesApi.pointage(sid), { refreshInterval: 2000 });
    const [recu, setRecu] = useState(() => Date.now());
    const [maintenant, setMaintenant] = useState(() => Date.now());
    const [busy, setBusy] = useState(false);

    useEffect(() => setRecu(Date.now()), [info?.code, info?.secondes_restantes]);
    useEffect(() => {
        const t = setInterval(() => setMaintenant(Date.now()), 250);
        return () => clearInterval(t);
    }, []);

    if (!seance || !info) return <FullPageLoader />;
    const restant = Math.max(0, info.secondes_restantes - (maintenant - recu) / 1000);

    const action = async (fn: () => Promise<unknown>, ok: string) => {
        setBusy(true);
        try {
            await fn();
            await mutate();
            toast.success(ok);
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-5 text-center">
            <div className="flex w-full items-center justify-between gap-2">
                <Button asChild variant="ghost" size="sm" className="-ml-2"><Link href={`/seances/${sid}`}><ArrowLeft /> Séance</Link></Button>
                {info.ouvert && (
                    <Button variant="ghost" size="sm" onClick={() => document.documentElement.requestFullscreen?.().catch(() => {})}>
                        <Expand /> Plein écran
                    </Button>
                )}
            </div>
            <div>
                <p className="text-ember text-xs font-semibold tracking-[0.2em] uppercase">Pointage</p>
                <h1 className="text-gilded text-2xl font-bold sm:text-3xl">{seance.nom}</h1>
                {formatHeure(seance.heure_debut) && <p className="text-muted-foreground text-sm">{formatHeure(seance.heure_debut)} · {seance.lieu}</p>}
            </div>

            {!info.ouvert ? (
                <div className="bg-card w-full max-w-md space-y-4 rounded-xl border p-6">
                    <QrCode className="text-gold mx-auto size-12" />
                    <p className="text-muted-foreground text-sm">
                        Les membres scannent le QR code pour déclarer leur présence. Le code change toutes les {info.periode_s} secondes,
                        et tu valides ensuite l&apos;appel : aucun point n&apos;est donné sans toi.
                    </p>
                    <Button className="w-full" size="lg" disabled={busy} onClick={() => action(() => SeancesApi.ouvrirPointage(sid), "Pointage ouvert")}>
                        {busy && <Loader2 className="animate-spin" />} Ouvrir le pointage
                    </Button>
                </div>
            ) : (
                <>
                    <div className="rounded-2xl bg-white p-4 shadow-[0_0_60px_-10px_var(--ember)] sm:p-6">
                        {info.url && (
                            <QRCodeSVG value={info.url} size={512} level="M" marginSize={0} className="h-auto w-[min(78vw,58vh)] max-w-[420px]" title="QR code de pointage" />
                        )}
                    </div>
                    <div className="w-full max-w-sm">
                        <div className="bg-muted h-1.5 overflow-hidden rounded-full">
                            <div className="bg-flame h-full rounded-full transition-[width] duration-200 ease-linear" style={{ width: `${(restant / info.periode_s) * 100}%` }} />
                        </div>
                        <p className="text-muted-foreground mt-1.5 text-xs">Nouveau code dans {Math.ceil(restant)} s · code {info.code}</p>
                    </div>
                    <p className="text-lg font-medium">Scanne avec l&apos;appareil photo de ton téléphone</p>

                    <div className="bg-card w-full rounded-xl border p-4 text-left">
                        <p className="mb-2 flex items-center gap-2 font-semibold">
                            <Users className="text-gold size-4" />
                            <span className="font-display text-2xl tabular-nums">{info.pointages.length}</span> pointé{info.pointages.length > 1 ? "s" : ""}
                        </p>
                        <ul className="flex flex-wrap gap-1.5" aria-live="polite">
                            {[...info.pointages].reverse().map((p) => (
                                <li key={p.utilisateur_id} className="bg-success/15 text-success rounded-full px-2.5 py-1 text-sm">{p.prenom} {p.nom[0]}.</li>
                            ))}
                        </ul>
                    </div>
                    <div className="flex w-full flex-col gap-2 sm:flex-row sm:justify-center">
                        <Button asChild size="lg"><Link href={`/seances/${sid}#appel`}><ClipboardCheck /> Valider l&apos;appel</Link></Button>
                        <Button variant="outline" size="lg" disabled={busy} onClick={() => action(() => SeancesApi.fermerPointage(sid), "Pointage fermé")}>
                            <Lock /> Fermer le pointage
                        </Button>
                    </div>
                </>
            )}
        </div>
    );
}

export default function QrPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    return (
        <AuthGuard>
            <RequireRole allow={["moderator", "admin"]}>
                <EcranQr sid={Number(id)} />
            </RequireRole>
        </AuthGuard>
    );
}
