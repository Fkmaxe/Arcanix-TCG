import { Suspense } from "react";
import type { Metadata } from "next";
import Desabonnement from "./Desabonnement";

export const metadata: Metadata = { title: "Désinscription des annonces", robots: { index: false } };

export default function DesabonnementPage() {
    return (
        <Suspense>
            <Desabonnement />
        </Suspense>
    );
}
