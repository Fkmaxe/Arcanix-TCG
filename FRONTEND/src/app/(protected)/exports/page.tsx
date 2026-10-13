"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import { SemestresApi, StatsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DataTable } from "@/components/common/DataTable";
import { Download, FileSpreadsheet } from "lucide-react";
import { RoleGate } from "@/lib/auth";

type SemestreType = {
    id: number;
    annee: number;
    numero: number;
};

type PointsData = {
    user_id: number;
    nom: string;
    prenom: string;
    classe: string;
    points: number;
    rang?: number;
};

export default function ExportsPage() {
    const { data: semestres = [] } = useSWR<SemestreType[]>("/semestres", () => SemestresApi.list());
    const [selectedSemestre, setSelectedSemestre] = useState<number | null>(null);
    const [isExporting, setIsExporting] = useState(false);

    const { data: pointsData = [], isLoading } = useSWR<PointsData[]>(
        selectedSemestre ? `/stats/points?semestreId=${selectedSemestre}` : null,
        () => {
            if (!selectedSemestre) return [];
            const params = new URLSearchParams({ semestreId: selectedSemestre.toString() });
            return StatsApi.points(params);
        }
    );

    const sortedData = useMemo(() => {
        return [...pointsData]
            .sort((a, b) => b.points - a.points)
            .map((item, index) => ({ ...item, rang: index + 1 }));
    }, [pointsData]);

    const stats = useMemo(() => {
        if (pointsData.length === 0) return { total: 0, average: 0, max: 0, min: 0 };
        const points = pointsData.map(p => p.points);
        return {
            total: pointsData.length,
            average: points.reduce((a, b) => a + b, 0) / points.length,
            max: Math.max(...points),
            min: Math.min(...points),
        };
    }, [pointsData]);

    const selectedSemestreData = semestres.find(s => s.id === selectedSemestre);

    const exportToCSV = () => {
        setIsExporting(true);

        try {
            const headers = ["Rang", "Nom", "Prénom", "Classe", "Points"];
            const rows = sortedData.map((row) => [
                row.rang,
                row.nom,
                row.prenom,
                row.classe,
                row.points.toFixed(1),
            ]);

            const csvContent = [
                headers.join(","),
                ...rows.map(row => row.join(","))
            ].join("\n");

            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);

            const filename = selectedSemestreData
                ? `points_${selectedSemestreData.annee}_S${selectedSemestreData.numero}.csv`
                : "points.csv";

            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } finally {
            setIsExporting(false);
        }
    };

    const exportToJSON = () => {
        setIsExporting(true);

        try {
            const exportData = {
                semestre: selectedSemestreData,
                exportDate: new Date().toISOString(),
                stats,
                data: sortedData.map((row) => ({
                    rang: row.rang,
                    nom: row.nom,
                    prenom: row.prenom,
                    classe: row.classe,
                    points: row.points,
                })),
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);

            const filename = selectedSemestreData
                ? `points_${selectedSemestreData.annee}_S${selectedSemestreData.numero}.json`
                : "points.json";

            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <RoleGate allow={["admin", "moderator"]}>
            <div className="p-6 space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Exports</h1>
                    <p className="text-muted-foreground mt-1">
                        Exportez les points des étudiants par semestre
                    </p>
                </div>

                {/* Sélection du semestre */}
                <Card>
                    <CardHeader>
                        <CardTitle>Sélectionner un semestre</CardTitle>
                        <CardDescription>
                            Choisissez le semestre pour lequel vous souhaitez voir les points
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Select
                            value={selectedSemestre?.toString()}
                            onValueChange={(v) => setSelectedSemestre(Number(v))}
                        >
                            <SelectTrigger className="w-full md:w-[300px]">
                                <SelectValue placeholder="Choisir un semestre..." />
                            </SelectTrigger>
                            <SelectContent>
                                {semestres.map((s) => (
                                    <SelectItem key={s.id} value={s.id.toString()}>
                                        {s.annee} - Semestre {s.numero}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </CardContent>
                </Card>

                {/* Statistiques */}
                {selectedSemestre && sortedData.length > 0 && (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Total étudiants</CardDescription>
                                <CardTitle className="text-3xl">{stats.total}</CardTitle>
                            </CardHeader>
                        </Card>
                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Moyenne</CardDescription>
                                <CardTitle className="text-3xl">{stats.average.toFixed(1)}</CardTitle>
                            </CardHeader>
                        </Card>
                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Maximum</CardDescription>
                                <CardTitle className="text-3xl">{stats.max}</CardTitle>
                            </CardHeader>
                        </Card>
                        <Card>
                            <CardHeader className="pb-3">
                                <CardDescription>Minimum</CardDescription>
                                <CardTitle className="text-3xl">{stats.min}</CardTitle>
                            </CardHeader>
                        </Card>
                    </div>
                )}

                {/* Tableau des résultats */}
                {selectedSemestre && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Points par étudiant</CardTitle>
                                    <CardDescription>
                                        {selectedSemestreData &&
                                            `Année ${selectedSemestreData.annee} - Semestre ${selectedSemestreData.numero}`
                                        }
                                    </CardDescription>
                                </div>
                                {sortedData.length > 0 && (
                                    <div className="flex gap-2">
                                        <Button
                                            onClick={exportToCSV}
                                            disabled={isExporting}
                                            variant="outline"
                                            size="sm"
                                        >
                                            <FileSpreadsheet className="mr-2 h-4 w-4" />
                                            Export CSV
                                        </Button>
                                        <Button
                                            onClick={exportToJSON}
                                            disabled={isExporting}
                                            variant="outline"
                                            size="sm"
                                        >
                                            <Download className="mr-2 h-4 w-4" />
                                            Export JSON
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <DataTable
                                isLoading={isLoading}
                                columns={[
                                    {
                                        key: "rang",
                                        header: "Rang",
                                        render: (row: PointsData) => (
                                            <span className="font-medium">#{row.rang}</span>
                                        )
                                    },
                                    { key: "nom", header: "Nom" },
                                    { key: "prenom", header: "Prénom" },
                                    { key: "classe", header: "Classe" },
                                    {
                                        key: "points",
                                        header: "Points",
                                        render: (row: PointsData) => (
                                            <span className="font-semibold">{row.points.toFixed(1)}</span>
                                        )
                                    },
                                ]}
                                rows={sortedData}
                                empty="Aucune donnée pour ce semestre"
                            />
                        </CardContent>
                    </Card>
                )}

                {!selectedSemestre && (
                    <Card>
                        <CardContent className="py-12">
                            <div className="text-center text-muted-foreground">
                                <FileSpreadsheet className="mx-auto h-12 w-12 mb-4 opacity-50" />
                                <p>Sélectionnez un semestre pour afficher les points</p>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </RoleGate>
    );
}
