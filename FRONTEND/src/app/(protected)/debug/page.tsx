"use client";

import { useMe } from "@/lib/auth";

export default function DebugPage() {
    const { me, isLoading, error } = useMe();

    if (isLoading) return <div className="p-6">Chargement...</div>;
    if (error) return <div className="p-6 text-red-600">Erreur: {JSON.stringify(error)}</div>;

    return (
        <div className="p-6 space-y-4">
            <h1 className="text-2xl font-bold">Debug - Informations utilisateur</h1>

            <div className="bg-gray-100 p-4 rounded-lg">
                <h2 className="font-semibold mb-2">Données brutes du "me":</h2>
                <pre className="text-xs overflow-auto">
                    {JSON.stringify(me, null, 2)}
                </pre>
            </div>

            <div className="space-y-2">
                <p><strong>ID:</strong> {me?.id}</p>
                <p><strong>Nom:</strong> {me?.nom}</p>
                <p><strong>Prénom:</strong> {me?.prenom}</p>
                <p><strong>Email:</strong> {me?.adresse_mail}</p>
                <p><strong>Rôle (role_utilisateur):</strong> <span className="bg-blue-100 px-2 py-1 rounded">{me?.role_utilisateur || "NON DÉFINI"}</span></p>
                <p><strong>Classe:</strong> {me?.classe}</p>
            </div>

            <div className="space-y-2">
                <h2 className="font-semibold">Tests de permissions:</h2>
                <p>Est admin ? {me?.role_utilisateur === "admin" ? "✅ OUI" : "❌ NON"}</p>
                <p>Est moderator ? {me?.role_utilisateur === "moderator" ? "✅ OUI" : "❌ NON"}</p>
                <p>Est user ? {me?.role_utilisateur === "user" ? "✅ OUI" : "❌ NON"}</p>
            </div>
        </div>
    );
}
