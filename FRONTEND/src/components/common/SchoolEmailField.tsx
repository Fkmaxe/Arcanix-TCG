// src/components/common/SchoolEmailField.tsx — adresse de l'école : on ne saisit que l'identifiant
"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useConfig } from "@/lib/useConfig";
import { cn } from "@/lib/utils";

/**
 * Champ « identifiant » + suffixe @domaine figé dans la même bordure.
 * `value` / `onChange` manipulent l'adresse complète (ex. j.dupont@myskolae.fr).
 */
export function SchoolEmailField({
    id,
    value,
    onChange,
    required,
    autoFocus,
}: {
    id: string;
    value: string;
    onChange: (email: string) => void;
    required?: boolean;
    autoFocus?: boolean;
}) {
    const { domaine } = useConfig();
    // Texte tel que tapé : on ne coupe pas pendant la saisie (taper « @… » ne doit rien casser)
    const [brut, setBrut] = useState(() => value.split("@")[0]);
    const [identifiant, apres] = brut.split("@", 2) as [string, string | undefined];
    const autreDomaine = apres !== undefined && apres.length > 0 && !domaine.startsWith(apres.toLowerCase());

    // Valeur remise à zéro par le parent (ex. changement de statut)
    useEffect(() => {
        if (!value) setBrut("");
    }, [value]);

    const changer = (saisie: string) => {
        setBrut(saisie);
        const propre = saisie.trim().toLowerCase().replace(/\s+/g, "");
        const [local, dom] = propre.split("@", 2);
        // Autre domaine tapé : on transmet l'adresse réelle (l'API la refuse avec un message clair)
        if (dom && !domaine.startsWith(dom)) return onChange(propre);
        onChange(local ? `${local}@${domaine}` : "");
    };

    return (
        <div className="space-y-1.5">
            <div
                className={cn(
                    "bg-surface/60 border-input flex h-11 w-full items-stretch overflow-hidden rounded-md border sm:h-10",
                    "focus-within:border-ring focus-within:ring-ring/50 focus-within:ring-[3px]",
                    autreDomaine && "border-destructive",
                )}
            >
                <Input
                    id={id}
                    value={brut}
                    onChange={(e) => changer(e.target.value)}
                    // Adresse complète tapée ou collée : on n'affiche plus que l'identifiant
                    onBlur={() => !autreDomaine && setBrut(identifiant.trim().toLowerCase())}
                    placeholder="j.dupont"
                    required={required}
                    autoFocus={autoFocus}
                    autoComplete="username"
                    autoCapitalize="none"
                    spellCheck={false}
                    inputMode="email"
                    aria-invalid={autreDomaine}
                    aria-describedby={`${id}-aide`}
                    className="h-full min-w-0 flex-1 rounded-none border-0 bg-transparent shadow-none focus-visible:ring-0"
                />
                <span className="bg-muted text-muted-foreground flex shrink-0 items-center border-l px-3 text-sm select-none" aria-hidden>
                    @{domaine}
                </span>
            </div>
            <p id={`${id}-aide`} className={cn("text-xs", autreDomaine ? "text-destructive" : "text-muted-foreground")}>
                {autreDomaine
                    ? `Seules les adresses @${domaine} sont acceptées ici : si tu n'es pas élève, choisis « Externe ».`
                    : `Initiale du prénom, un point, puis le nom de famille — l'adresse se termine par @${domaine}.`}
            </p>
        </div>
    );
}

/** Choix « Élève de l'école » / « Externe ». */
export function StatutChoix({ externe, onChange }: { externe: boolean; onChange: (externe: boolean) => void }) {
    return (
        <div className="bg-muted grid grid-cols-2 rounded-lg p-1" role="radiogroup" aria-label="Statut">
            {([[false, "Élève de l'école"], [true, "Externe"]] as const).map(([valeur, label]) => (
                <button
                    key={label}
                    type="button"
                    role="radio"
                    aria-checked={externe === valeur}
                    onClick={() => onChange(valeur)}
                    className={cn(
                        "h-10 rounded-md text-sm font-medium transition",
                        externe === valeur ? "bg-card text-gold shadow-sm" : "text-muted-foreground hover:text-foreground",
                    )}
                >
                    {label}
                </button>
            ))}
        </div>
    );
}

/**
 * Choix du statut + champ email adapté : élève → identifiant suivi de @domaine visible, externe → adresse libre.
 * Changer de statut vide l'adresse (une adresse d'élève n'a pas de sens côté externe, et inversement).
 */
export function EmailSelonStatut({
    id,
    value,
    onChange,
    autoFocus,
}: {
    id: string;
    value: string;
    onChange: (email: string) => void;
    autoFocus?: boolean;
}) {
    const [externe, setExterne] = useState(false);
    return (
        <div className="space-y-3">
            <StatutChoix
                externe={externe}
                onChange={(v) => {
                    setExterne(v);
                    onChange("");
                }}
            />
            <div className="space-y-1.5">
                <Label htmlFor={id}>{externe ? "Email" : "Adresse de l'école"}</Label>
                {externe ? (
                    <Input
                        id={id}
                        type="email"
                        inputMode="email"
                        autoCapitalize="none"
                        spellCheck={false}
                        value={value}
                        onChange={(e) => onChange(e.target.value.trim())}
                        required
                        autoComplete="username"
                        autoFocus={autoFocus}
                        placeholder="ton.adresse@exemple.fr"
                    />
                ) : (
                    <SchoolEmailField id={id} value={value} onChange={onChange} required autoFocus={autoFocus} />
                )}
            </div>
        </div>
    );
}
