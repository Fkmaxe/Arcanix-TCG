"use client";

import { Suspense } from "react";
import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Clock, Loader2, ScanLine, TriangleAlert } from "lucide-react";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { Button } from "@/components/ui/button";
import { SeancesApi } from "@/lib/api";
import { errorMessage } from "@/lib/swr";
import type { Seance } from "@/lib/types";

type Etat = { type: "chargement" } | { type: "ok"; resultat: "pointe" | "deja_pointe" | "deja_valide"; seance: Seance } | { type: "erreur"; message: string };

const MESSAGES = {
    pointe: { titre: "Présence enregistrée !", texte: "La modération va valider ton passage : tes points arriveront juste après.", Icon: CheckCircle2 },
    deja_pointe: { titre: "Déjà pointé·e", texte: "Ta présence est déjà enregistrée, elle attend la validation de la modération.", Icon: Clock },
    deja_valide: { titre: "Présence déjà validée", texte: "Tes points pour cette séance sont déjà comptés.", Icon: CheckCircle2 },
};

function PointerContenu({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const code = useSearchParams().get("c") ?? "";
    const [etat, setEtat] = useState<Etat>({ type: "chargement" });
    const envoye = useRef(false);

    useEffect(() => {
        if (envoye.current) return; // une seule tentative (StrictMode rejoue les effets)
        envoye.current = true;
        if (!code) return setEtat({ type: "erreur", message: "QR code incomplet : scanne à nouveau le code affiché." });
        SeancesApi.pointer(Number(id), code)
            .then((r) => setEtat({ type: "ok", resultat: r.resultat, seance: r.seance }))
            .catch((e) => setEtat({ type: "erreur", message: errorMessage(e) }));
    }, [id, code]);

    return (
        <div className="mx-auto flex min-h-[calc(100dvh-10rem)] max-w-md flex-col justify-center">
            <OrnateCard className="text-center">
                {etat.type === "chargement" && (
                    <div className="py-6"><Loader2 className="text-ember mx-auto size-10 animate-spin" /><p className="mt-3">Pointage en cours…</p></div>
                )}
                {etat.type === "ok" && (() => {
                    const { titre, texte, Icon } = MESSAGES[etat.resultat];
                    return (
                        <div className="space-y-3 py-2">
                            <Icon className="text-success mx-auto size-16 drop-shadow-[0_0_18px_var(--success)]" />
                            <h1 className="text-gilded text-2xl font-bold">{titre}</h1>
                            <p className="font-semibold">{etat.seance.nom}</p>
                            <p className="text-muted-foreground text-sm">{texte}</p>
                            <Button asChild variant="outline" className="mt-2"><Link href={`/seances/${etat.seance.id}`}>Voir la séance</Link></Button>
                        </div>
                    );
                })()}
                {etat.type === "erreur" && (
                    <div className="space-y-3 py-2">
                        <TriangleAlert className="text-ember mx-auto size-14" />
                        <h1 className="text-gilded text-xl font-bold">Pointage impossible</h1>
                        <p className="text-muted-foreground text-sm">{etat.message}</p>
                        <p className="text-muted-foreground flex items-center justify-center gap-1.5 text-xs"><ScanLine className="size-4" /> Le code change toutes les 30 secondes : rescanne celui affiché.</p>
                        <Button asChild variant="outline" className="mt-2"><Link href="/dashboard">Retour à l&apos;accueil</Link></Button>
                    </div>
                )}
            </OrnateCard>
        </div>
    );
}

export default function PointerPage(props: Parameters<typeof PointerContenu>[0]) {
    return (
        <Suspense>
            <PointerContenu {...props} />
        </Suspense>
    );
}
