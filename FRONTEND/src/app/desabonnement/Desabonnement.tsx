"use client";

import Link from "next/link";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { BellOff, Loader2, TriangleAlert } from "lucide-react";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { Button } from "@/components/ui/button";
import { AuthApi } from "@/lib/api";
import { errorMessage } from "@/lib/swr";

/** Désinscription des emails d'annonce : confirmation par un clic (évite les désinscriptions par les antispams). */
export default function Desabonnement() {
    const params = useSearchParams();
    const u = params.get("u") ?? "";
    const s = params.get("s") ?? "";
    const [etat, setEtat] = useState<"attente" | "chargement" | "ok" | "erreur">("attente");
    const [message, setMessage] = useState("");

    const confirmer = async () => {
        setEtat("chargement");
        try {
            setMessage((await AuthApi.desabonner(u, s)).message);
            setEtat("ok");
        } catch (e) {
            setMessage(errorMessage(e));
            setEtat("erreur");
        }
    };

    return (
        <div className="mx-auto flex min-h-[calc(100dvh-8rem)] max-w-md flex-col justify-center py-6">
            <OrnateCard className="space-y-4 text-center">
                {etat === "ok" ? (
                    <>
                        <BellOff className="text-gold mx-auto size-12" />
                        <h1 className="text-gilded text-2xl font-bold">C&apos;est noté</h1>
                        <p className="text-muted-foreground text-sm">{message}</p>
                        <p className="text-muted-foreground text-xs">Tu peux te réabonner à tout moment depuis ton profil, section Notifications.</p>
                        <Button asChild variant="outline"><Link href="/profil#notifications">Mon profil</Link></Button>
                    </>
                ) : etat === "erreur" || !u || !s ? (
                    <>
                        <TriangleAlert className="text-ember mx-auto size-12" />
                        <h1 className="text-gilded text-xl font-bold">Lien invalide</h1>
                        <p className="text-muted-foreground text-sm">{message || "Ce lien de désinscription est incomplet."} Tu peux gérer tes notifications depuis ton profil.</p>
                        <Button asChild variant="outline"><Link href="/profil#notifications">Mon profil</Link></Button>
                    </>
                ) : (
                    <>
                        <BellOff className="text-gold mx-auto size-12" />
                        <h1 className="text-gilded text-2xl font-bold">Ne plus recevoir les annonces ?</h1>
                        <p className="text-muted-foreground text-sm">Tu ne recevras plus d&apos;email quand une nouvelle séance est publiée. Les annonces restent visibles sur le site et le Discord.</p>
                        <Button className="w-full" onClick={confirmer} disabled={etat === "chargement"}>
                            {etat === "chargement" && <Loader2 className="animate-spin" />} Me désinscrire
                        </Button>
                    </>
                )}
            </OrnateCard>
        </div>
    );
}
