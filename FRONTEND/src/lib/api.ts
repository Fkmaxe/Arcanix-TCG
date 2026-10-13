// src/lib/api.ts
import { fetcher } from "./swr";
import { User, Semestre, Seance, Participation, MyPoints } from "./types";

// USERS
export const UsersApi = {
    list: (params?: URLSearchParams) => fetcher(`/users${params ? `?${params}` : ""}`),                       // GET /users  [oai_citation:3‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    get: (id: number) => fetcher(`/users/${id}`),                                                             // GET /users/{id}  [oai_citation:4‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    create: (body: { nom: string; prenom: string; adresse_mail: string; classe: string; role_utilisateur: string; password: string }) => fetcher(`/users`, { method:"POST", body: JSON.stringify(body) }),        // POST /users  [oai_citation:5‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    update: (id: number, body: Partial<User>) => fetcher(`/users/${id}`, { method:"PATCH", body: JSON.stringify(body) }), // PATCH  [oai_citation:6‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    remove: (id: number) => fetcher(`/users/${id}`, { method:"DELETE" }),
    changePassword: async (id: number, new_password: string) =>
        fetcher(`/users/${id}/password`, {
            method: "PATCH",
            body: JSON.stringify({ new_password }),
        }),
};

// SEMESTRES
export const SemestresApi = {
    list: () => fetcher(`/semestres`),                                                                        // GET /semestres  [oai_citation:8‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    get: (id: number) => fetcher(`/semestres/${id}`),                                                         // GET /semestres/{sid}  [oai_citation:9‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    create: (b: Partial<Semestre>) => fetcher(`/semestres`, { method:"POST", body: JSON.stringify(b) }),      // POST  [oai_citation:10‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    update: (id: number, b: Partial<Semestre>) => fetcher(`/semestres/${id}`, { method:"PATCH", body: JSON.stringify(b) }), // PATCH  [oai_citation:11‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    remove: (id: number) => fetcher(`/semestres/${id}`, { method:"DELETE" }),                                 // DELETE  [oai_citation:12‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
};

// SEANCES
export const SeancesApi = {
    list: (params?: URLSearchParams) => fetcher(`/seances${params ? `?${params}` : ""}`),                     // GET /seances  [oai_citation:13‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    get: (id:number) => fetcher(`/seances/${id}`),                                                            // GET /seances/{sid}  [oai_citation:14‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    create: (b: Partial<Seance>) => fetcher(`/seances`, { method:"POST", body: JSON.stringify(b) }),          // POST  [oai_citation:15‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    update: (id:number, b: Partial<Seance>) => fetcher(`/seances/${id}`, { method:"PATCH", body: JSON.stringify(b) }), // PATCH  [oai_citation:16‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    remove: (id:number) => fetcher(`/seances/${id}`, { method:"DELETE" }),                                    // DELETE  [oai_citation:17‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    participants: {
        list: (sid:number) => fetcher(`/seances/${sid}/participants`),                                          // GET participants  [oai_citation:18‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
        add: (sid:number, p: Participation) => fetcher(`/seances/${sid}/participants`, { method:"POST", body: JSON.stringify(p) }), // POST  [oai_citation:19‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
        patch: (sid:number, uid:number, b: Partial<Participation>) => fetcher(`/seances/${sid}/participants/${uid}`, { method:"PATCH", body: JSON.stringify(b) }), // PATCH  [oai_citation:20‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
        remove: (sid:number, uid:number) => fetcher(`/seances/${sid}/participants/${uid}`, { method:"DELETE" }), // DELETE  [oai_citation:21‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    }
};

// ME
export const MeApi = {
    participations: (semestreId?: number) => fetcher(`/me/participations${semestreId?`?semestreId=${semestreId}`:""}`), // GET /me/participations  [oai_citation:22‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    points: () => fetcher(`/me/points`) as Promise<MyPoints>,                                                // GET /me/points  [oai_citation:23‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
};

// STATS / EXPORTS
export const StatsApi = {
    points: (params?: URLSearchParams) => fetcher(`/stats/points${params?`?${params}`:""}`),                  // GET /stats/points  [oai_citation:24‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
    exportParticipationsCsv: (semestreId?: number) =>
        fetcher(`/exports/participations.csv${semestreId?`?semestreId=${semestreId}`:""}`),                     // GET /exports/participations.csv  [oai_citation:25‡Points & Séances API - Swagger UI.pdf](sediment://file_000000002d4461f4ad4348e62483adfa)
};
export const AuthApi = {
    register: (payload: {
        nom: string; prenom: string; adresse_mail: string; classe: string; password: string;
    }) => fetcher(`/auth/register`, { method: "POST", body: JSON.stringify(payload) }),
};