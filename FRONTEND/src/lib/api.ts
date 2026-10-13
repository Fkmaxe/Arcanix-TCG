// src/lib/api.ts — appels typés vers l'API Arcanix
import { download, fetcher, fetchPage } from "./swr";
import type {
    Classement, MaParticipation, Me, MesStats, MyPoints, ParticipantDetail, Seance, SeanceDetail, SeanceInput,
    Semestre, StatPoints, User,
} from "./types";

const json = (method: string, body?: unknown): RequestInit => ({
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
});
const qs = (params: Record<string, string | number | boolean | null | undefined>) => {
    const p = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
    });
    const s = p.toString();
    return s ? `?${s}` : "";
};

export const AuthApi = {
    login: (email: string, password: string) =>
        fetcher<{ access_token: string }>("/auth/login", json("POST", { email, password })),
    me: () => fetcher<Me>("/auth/me"),
    definirMotDePasse: (jeton: string, mot_de_passe: string) =>
        fetcher<{ access_token: string }>("/auth/definir-mot-de-passe", json("POST", { jeton, mot_de_passe })),
    register: (body: { nom: string; prenom: string; adresse_mail: string; classe: string; password: string }) =>
        fetcher<User>("/users", json("POST", body)),
};

export const MeApi = {
    update: (body: Partial<Pick<Me, "nom" | "prenom" | "classe">>) => fetcher<Me>("/me", json("PATCH", body)),
    changePassword: (new_password: string, current_password?: string) =>
        fetcher<null>("/me/password", json("PATCH", { new_password, current_password })),
    participations: (semestreId?: number) => fetcher<MaParticipation[]>(`/me/participations${qs({ semestreId })}`),
    points: () => fetcher<MyPoints>("/me/points"),
    stats: (semestreId?: number) => fetcher<MesStats>(`/me/stats${qs({ semestreId })}`),
    codeDiscord: () => fetcher<{ code: string; expire_dans_minutes: number }>("/me/code-discord", json("POST")),
    delierDiscord: () => fetcher<null>("/me/discord", json("DELETE")),
};

export type UsersQuery = { q?: string; role?: string; classe?: string; page?: number; limit?: number };
export const UsersApi = {
    list: (params: UsersQuery = {}) => fetchPage<User>(`/users${qs(params)}`),
    classes: () => fetcher<string[]>("/users/classes"),
    create: (body: Omit<User, "id" | "discord_id" | "doit_changer_mdp"> & { password: string }) =>
        fetcher<User>("/users", json("POST", body)),
    update: (id: number, body: Partial<Omit<User, "id" | "discord_id" | "doit_changer_mdp">>) =>
        fetcher<User>(`/users/${id}`, json("PATCH", body)),
    remove: (id: number) => fetcher<null>(`/users/${id}`, json("DELETE")),
    setPassword: (id: number, new_password: string) =>
        fetcher<null>(`/users/${id}/password`, json("PATCH", { new_password })),
    lienMotDePasse: (id: number) =>
        fetcher<{ url: string; expire_dans_heures: number }>(`/users/${id}/lien-mot-de-passe`, json("POST")),
};

export const SemestresApi = {
    list: () => fetcher<Semestre[]>("/semestres"),
    actif: () => fetcher<Semestre | null>("/semestres/actif"),
    create: (b: { annee: number; numero: number }) => fetcher<Semestre>("/semestres", json("POST", b)),
    update: (id: number, b: { annee?: number; numero?: number }) => fetcher<Semestre>(`/semestres/${id}`, json("PATCH", b)),
    activer: (id: number) => fetcher<Semestre>(`/semestres/${id}/activer`, json("POST")),
    remove: (id: number) => fetcher<null>(`/semestres/${id}`, json("DELETE")),
};

export type SeancesQuery = {
    semestreId?: number; a_venir?: boolean; jeu?: string; q?: string; page?: number; limit?: number;
};
export const SeancesApi = {
    list: (params: SeancesQuery = {}) => fetchPage<Seance>(`/seances${qs(params)}`),
    get: (id: number) => fetcher<SeanceDetail>(`/seances/${id}`),
    create: (b: SeanceInput) => fetcher<Seance>("/seances", json("POST", b)),
    update: (id: number, b: Partial<SeanceInput>) => fetcher<Seance>(`/seances/${id}`, json("PATCH", b)),
    remove: (id: number) => fetcher<null>(`/seances/${id}`, json("DELETE")),
    appel: (id: number, participants: { utilisateur_id: number; present: boolean }[], remplacer = true) =>
        fetcher<SeanceDetail>(`/seances/${id}/participants`, json("PUT", { participants, remplacer })),
    retirer: (id: number, uid: number) => fetcher<null>(`/seances/${id}/participants/${uid}`, json("DELETE")),
    patchParticipant: (id: number, uid: number, b: Partial<Pick<ParticipantDetail, "present" | "commentaire">>) =>
        fetcher(`/seances/${id}/participants/${uid}`, json("PATCH", b)),
};

export const StatsApi = {
    classement: (semestreId?: number, classe?: string) =>
        fetcher<Classement>(`/stats/classement${qs({ semestreId, classe })}`),
    points: (semestreId?: number) => fetcher<StatPoints[]>(`/stats/points${qs({ semestreId })}`),
    exportPointsCsv: (semestreId?: number) => download(`/exports/points.csv${qs({ semestreId })}`, "points.csv"),
    exportPointsJson: (semestreId?: number) => download(`/exports/points.json${qs({ semestreId })}`, "points.json"),
    exportParticipationsCsv: (semestreId?: number) =>
        download(`/exports/participations.csv${qs({ semestreId })}`, "participations.csv"),
};
