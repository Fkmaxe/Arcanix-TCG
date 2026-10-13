"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
    AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
    AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Bouton qui demande confirmation avant une action destructive. */
export function ConfirmButton({
    children,
    title,
    description,
    confirmLabel = "Confirmer",
    onConfirm,
    destructive = true,
}: {
    children: React.ReactNode; // le déclencheur (un <Button>)
    title: string;
    description?: React.ReactNode;
    confirmLabel?: string;
    onConfirm: () => Promise<unknown> | void;
    destructive?: boolean;
}) {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    return (
        <AlertDialog open={open} onOpenChange={(o) => !loading && setOpen(o)}>
            <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle className="font-display">{title}</AlertDialogTitle>
                    {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={loading}>Annuler</AlertDialogCancel>
                    <AlertDialogAction
                        disabled={loading}
                        className={cn(destructive && buttonVariants({ variant: "destructive" }))}
                        onClick={async (e) => {
                            e.preventDefault();
                            setLoading(true);
                            try {
                                await onConfirm();
                                setOpen(false);
                            } finally {
                                setLoading(false);
                            }
                        }}
                    >
                        {loading && <Loader2 className="animate-spin" />} {confirmLabel}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
