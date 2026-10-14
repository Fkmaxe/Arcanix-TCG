// src/lib/format.ts — mise en forme (dates, points, jeux)
import type { Semestre } from "./types";

const parseDate = (iso: string) => {
    const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
    return new Date(y, m - 1, d); // date locale, sans décalage de fuseau
};

export const todayIso = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export function formatDate(iso: string, style: "court" | "long" | "jour" = "court") {
    const d = parseDate(iso);
    if (style === "long")
        return d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    if (style === "jour") return d.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function dateParts(iso: string) {
    const d = parseDate(iso);
    return {
        jour: d.getDate(),
        mois: d.toLocaleDateString("fr-FR", { month: "short" }).replace(".", ""),
        semaine: d.toLocaleDateString("fr-FR", { weekday: "short" }).replace(".", ""),
    };
}

export function relativeDay(iso: string) {
    const diff = Math.round((parseDate(iso).getTime() - parseDate(todayIso()).getTime()) / 86_400_000);
    if (diff === 0) return "Aujourd'hui";
    if (diff === 1) return "Demain";
    if (diff === -1) return "Hier";
    if (diff > 1 && diff < 7) return `Dans ${diff} jours`;
    return null;
}

export const formatHeure = (h: string | null) => (h ? h.slice(0, 5).replace(":", "h") : null);

export const formatPoints = (n: number) =>
    n.toLocaleString("fr-FR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });

export const semestreLabel = (s?: Pick<Semestre, "annee" | "numero"> | null) =>
    s ? `${s.annee} · S${s.numero}` : "—";

export const initials = (prenom?: string, nom?: string) =>
    `${prenom?.[0] ?? ""}${nom?.[0] ?? ""}`.toUpperCase() || "?";

export const ROLE_LABELS: Record<string, string> = {
    user: "Membre",
    moderator: "Modérateur",
    admin: "Admin",
};

export const JEUX: { value: string; label: string; color: string }[] = [
    { value: "pokemon", label: "Pokémon", color: "#f2c94c" },
    { value: "magic", label: "Magic", color: "#e8361f" },
    { value: "yugioh", label: "Yu-Gi-Oh!", color: "#a06cd5" },
    { value: "lorcana", label: "Lorcana", color: "#4fa3e0" },
    { value: "onepiece", label: "One Piece", color: "#ff7a1a" },
    { value: "fab", label: "Flesh and Blood", color: "#c0392b" },
    { value: "autre", label: "Autre", color: "#b9a98d" },
];
export const jeuInfo = (v?: string | null) => JEUX.find((j) => j.value === v) ?? null;

export const CATEGORIES: Record<string, { label: string; emoji: string }> = {
    organisation: { label: "Aide à l'organisation", emoji: "🛠️" },
    tournoi: { label: "Tournoi", emoji: "⚔️" },
    penalite: { label: "Pénalité", emoji: "⚠️" },
    autre: { label: "Autre", emoji: "✨" },
};

export const formatSigne = (n: number) => (n > 0 ? `+${formatPoints(n)}` : formatPoints(n));

export const formatDateHeure = (iso: string) =>
    new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

export const libellePlace = (p: number) => (p === 1 ? "1re" : `${p}e`);

/** Classe d'un membre, ou « Externe » : seuls les membres extérieurs à l'école n'ont pas de classe. */
export const classeOuExterne = (m: { classe?: string | null }) => m.classe || "Externe";

/** Complète un identifiant de l'école (« j.dupont ») avec le domaine ; laisse une adresse complète intacte. */
export const completerEmail = (saisie: string, domaine: string) => {
    const v = saisie.trim();
    return v && !v.includes("@") ? `${v}@${domaine}` : v;
};

/** État de publication d'un canal pour la modération : « Publiée le … », « Programmée le … » ou « Non publiée ». */
export function etatPublication(le: string | null, envoye: boolean): { texte: string; programme: boolean } {
    if (envoye && le) return { texte: `publiée le ${formatDateHeure(le)}`, programme: false };
    if (!le) return { texte: "non publiée", programme: false };
    if (new Date(le).getTime() > Date.now()) return { texte: `programmée le ${formatDateHeure(le)}`, programme: true };
    return { texte: "publication en cours", programme: false };
}
