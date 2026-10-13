"use client";
import useSWR from "swr";
import { AuthApi } from "./api";

/** Fonctionnalités activées côté serveur (SMTP…). */
export function useConfig() {
    const { data } = useSWR("/config", () => AuthApi.config(), { revalidateOnFocus: false, dedupingInterval: 600_000 });
    return { smtp: data?.smtp ?? false, qrPeriode: data?.qr_periode_s ?? 30, charge: !!data };
}
