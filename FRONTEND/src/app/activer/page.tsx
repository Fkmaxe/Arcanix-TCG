import { Suspense } from "react";
import type { Metadata } from "next";
import ActiverForm from "./ActiverForm";

export const metadata: Metadata = { title: "Définir mon mot de passe", robots: { index: false } };

export default function ActiverPage() {
    return (
        <Suspense>
            <ActiverForm />
        </Suspense>
    );
}
