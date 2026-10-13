// src/components/common/DataTable.tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function DataTable<T>({
                                 columns, rows, empty = "Aucune donnée", isLoading = false,
                             }: {
    columns: { key: keyof T | string; header: string; render?: (row: T) => React.ReactNode }[];
    rows: T[];
    empty?: string;
    isLoading?: boolean;
}) {
    return (
        <Table>
            <TableHeader>
                <TableRow>{columns.map(c => <TableHead key={String(c.key)}>{c.header}</TableHead>)}</TableRow>
            </TableHeader>
            <TableBody>
                {isLoading ? (
                    <TableRow><TableCell colSpan={columns.length} className="text-center text-sm text-muted-foreground">Chargement...</TableCell></TableRow>
                ) : rows.length === 0 ? (
                    <TableRow><TableCell colSpan={columns.length} className="text-center text-sm text-muted-foreground">{empty}</TableCell></TableRow>
                ) : rows.map((r, i) => (
                    <TableRow key={i}>
                        {columns.map(c => <TableCell key={String(c.key)}>{c.render ? c.render(r) : (r as any)[c.key]}</TableCell>)}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}