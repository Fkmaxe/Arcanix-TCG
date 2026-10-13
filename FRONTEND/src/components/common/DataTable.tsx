// src/components/common/DataTable.tsx — tableau sur desktop, cartes sur mobile
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { EmptyState, Skeleton } from "./States";

export type Column<T> = {
    key: string;
    header: string;
    render?: (row: T) => React.ReactNode;
    className?: string;
};

export function DataTable<T>({
    columns,
    rows,
    rowKey,
    mobileCard,
    empty = "Aucune donnée",
    emptyIcon,
    isLoading = false,
    onRowClick,
    rowClassName,
}: {
    columns: Column<T>[];
    rows: T[];
    rowKey: (row: T) => string | number;
    /** Rendu d'une ligne en carte sur mobile ; sinon le tableau défile horizontalement */
    mobileCard?: (row: T) => React.ReactNode;
    empty?: string;
    emptyIcon?: React.ReactNode;
    isLoading?: boolean;
    onRowClick?: (row: T) => void;
    rowClassName?: (row: T) => string | undefined;
}) {
    if (isLoading && rows.length === 0) {
        return (
            <div className="space-y-2" aria-busy>
                {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-14 w-full" />
                ))}
            </div>
        );
    }
    if (rows.length === 0) return <EmptyState title={empty} icon={emptyIcon} />;

    const cell = (c: Column<T>, r: T) => (c.render ? c.render(r) : String((r as Record<string, unknown>)[c.key] ?? "—"));

    return (
        <>
            {mobileCard && (
                <ul className="space-y-2 md:hidden">
                    {rows.map((r) => (
                        <li key={rowKey(r)}>{mobileCard(r)}</li>
                    ))}
                </ul>
            )}
            <div className={cn("bg-card overflow-x-auto rounded-xl border", mobileCard && "hidden md:block", isLoading && "opacity-60")}>
                <Table>
                    <TableHeader>
                        <TableRow className="hover:bg-transparent">
                            {columns.map((c) => (
                                <TableHead key={c.key} className={c.className}>{c.header}</TableHead>
                            ))}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {rows.map((r) => (
                            <TableRow
                                key={rowKey(r)}
                                onClick={onRowClick ? () => onRowClick(r) : undefined}
                                className={cn(onRowClick && "cursor-pointer", rowClassName?.(r))}
                            >
                                {columns.map((c) => (
                                    <TableCell key={c.key} className={c.className}>{cell(c, r)}</TableCell>
                                ))}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </>
    );
}

export function Pagination({ page, total, limit, onPage }: { page: number; total: number; limit: number; onPage: (p: number) => void }) {
    const pages = Math.max(1, Math.ceil(total / limit));
    if (pages <= 1) return null;
    return (
        <div className="mt-4 flex items-center justify-between gap-2 text-sm">
            <span className="text-muted-foreground">
                {total} résultat{total > 1 ? "s" : ""} · page {page}/{pages}
            </span>
            <div className="flex gap-2">
                <Button variant="outline" size="icon-sm" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Page précédente">
                    <ChevronLeft />
                </Button>
                <Button variant="outline" size="icon-sm" disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label="Page suivante">
                    <ChevronRight />
                </Button>
            </div>
        </div>
    );
}
