// src/lib/types.ts — types renvoyés par l'API
export type Role = "user" | "moderator" | "admin";

export interface Me {
    id: number;
    nom: string;
    prenom: string;
    email: string;
    adresse_mail: string;
    role_utilisateur: Role;
    classe: string;
    doit_changer_mdp: boolean;
    discord_lie: boolean;
}

export interface User {
    id: number;
    nom: string;
    prenom: string;
    adresse_mail: string;
    role_utilisateur: Role;
    classe: string;
    discord_id: string | null;
    doit_changer_mdp: boolean;
}

export interface Semestre {
    id: number;
    annee: number;
    numero: number;
    actif: boolean;
}

export interface Seance {
    id: number;
    nom: string;
    date_seance: string; // AAAA-MM-JJ
    heure_debut: string | null; // HH:MM:SS
    lieu: string | null;
    jeu: string | null;
    description: string | null;
    nb_point: number;
    semestre_id: number;
    semestre: Semestre | null;
    nb_participants: number;
    nb_presents: number;
}

export interface ParticipantDetail {
    utilisateur_id: number;
    seance_id: number;
    present: boolean;
    commentaire: string | null;
    nom: string;
    prenom: string;
    classe: string;
    adresse_mail: string | null;
    discord_lie: boolean;
}

export interface SeanceDetail extends Seance {
    participants: ParticipantDetail[];
    ma_participation: boolean | null;
}

export type SeanceInput = {
    nom: string;
    date_seance: string;
    heure_debut: string | null;
    lieu: string | null;
    jeu: string | null;
    description: string | null;
    nb_point: number;
    semestre_id: number;
};

export interface MaParticipation {
    seance_id: number;
    seance_nom: string;
    date_seance: string;
    jeu: string | null;
    nb_point: number;
    present: boolean;
    commentaire: string | null;
    semestre_id: number;
}

export interface MyPoints {
    userId: number;
    semestres: { semestre_id: number; annee: number; numero: number; points: number }[];
    total: number;
}

export interface MesStats {
    semestre: Semestre | null;
    points: number;
    rang: number | null;
    nb_membres_classes: number;
    seances_semestre: number;
    presences: number;
    taux_presence: number;
    evolution: { date: string; seance: string; points: number; cumul: number }[];
}

export interface LigneClassement {
    rang: number;
    userId: number;
    prenom: string;
    nom: string;
    classe: string;
    points: number;
    presences: number;
    moi: boolean;
}

export interface Classement {
    semestre: Semestre | null;
    lignes: LigneClassement[];
}

export interface StatPoints {
    rang: number;
    userId: number;
    nom: string;
    prenom: string;
    classe: string;
    points: number;
    presences: number;
}
