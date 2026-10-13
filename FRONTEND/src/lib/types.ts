// src/lib/types.ts
import { z } from "zod";

export const User = z.object({
    id: z.number(),
    nom: z.string(),
    prenom: z.string(),
    adresse_mail: z.string().email(),
    role_utilisateur: z.enum(["user","moderator","admin"]),
    classe: z.string(),
    password: z.string().min(8),
});
export type User = z.infer<typeof User>;

export const Semestre = z.object({
    id: z.number(),
    annee: z.number(),
    numero: z.number(),
});
export type Semestre = z.infer<typeof Semestre>;

export const Seance = z.object({
    id: z.number(),
    nom: z.string(),
    date_seance: z.string(), // ISO date
    nb_point: z.number(),
    semestre_id: z.number(),
});
export type Seance = z.infer<typeof Seance>;

export const Participation = z.object({
    utilisateur_id: z.number(),
    seance_id: z.number(),
    present: z.boolean(),
    commentaire: z.string().nullable().optional(),
});
export type Participation = z.infer<typeof Participation>;

export const Token = z.object({
    access_token: z.string(),
    token_type: z.literal("bearer"),
});
export type Token = z.infer<typeof Token>;

export const MyPoints = z.object({
    userId: z.number(),
    semestres: z.array(z.object({
        semestre_id: z.number(),
        annee: z.number(),
        numero: z.number(),
        points: z.number(),
    })),
    total: z.number(),
});
export type MyPoints = z.infer<typeof MyPoints>;

export const UserCreate = User.omit({ id: true }).extend({
    password: z.string().min(8),
});
export type UserCreate = z.infer<typeof UserCreate>;
