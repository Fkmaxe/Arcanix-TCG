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
    places_max: number | null;
    nb_inscrits: number;
    nb_attente: number;
    mon_inscription: "inscrit" | "attente" | null;
    a_resultats: boolean;
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

export interface MembreResume {
    utilisateur_id: number;
    prenom: string;
    nom: string;
    classe: string;
    discord_lie: boolean;
}

export interface InscritDetail extends MembreResume {
    statut: "inscrit" | "attente";
    cree_le: string;
}

export interface PointageDetail extends MembreResume {
    cree_le: string;
}

export interface Resultat {
    utilisateur_id: number;
    prenom: string;
    nom: string;
    place: number;
    victoires: number | null;
    defaites: number | null;
    nuls: number | null;
    deck: string | null;
    bonus: number;
    moi: boolean;
}

export type ResultatInput = Pick<Resultat, "utilisateur_id" | "place" | "victoires" | "defaites" | "nuls" | "deck">;

export interface SeanceDetail extends Seance {
    participants: ParticipantDetail[];
    ma_participation: boolean | null;
    inscrits: InscritDetail[];
    pointages: PointageDetail[];
    mon_pointage: boolean;
    pointage_ouvert: boolean;
    resultats: Resultat[];
}

export interface PointageInfo {
    ouvert: boolean;
    expire_le: string | null;
    code: string | null;
    url: string | null;
    secondes_restantes: number;
    periode_s: number;
    pointages: PointageDetail[];
}

export type Categorie = "organisation" | "tournoi" | "penalite" | "autre";

export interface Ajustement {
    id: number;
    utilisateur_id: number;
    prenom: string;
    nom: string;
    semestre: Semestre;
    seance_id: number | null;
    points: number;
    categorie: Categorie;
    motif: string;
    cree_par: string | null;
    cree_le: string;
}

export interface MonAjustement {
    id: number;
    points: number;
    categorie: Categorie;
    motif: string;
    semestre_id: number;
    seance_id: number | null;
    cree_le: string;
}

export interface EntreeJournal {
    id: number;
    cree_le: string;
    auteur_id: number | null;
    auteur_nom: string;
    action: string;
    resume: string;
    membre_id: number | null;
    seance_id: number | null;
    details: Record<string, unknown> | null;
}

export interface ConfigPublique {
    smtp: boolean;
    qr_periode_s: number;
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
    places_max: number | null;
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
    evolution: { date: string; seance: string; points: number; cumul: number; type: "presence" | "ajustement" }[];
}

export interface LigneClassement {
    rang: number;
    userId: number;
    prenom: string;
    nom: string;
    classe: string;
    points: number;
    presences: number;
    bonus: number;
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
    bonus: number;
}
