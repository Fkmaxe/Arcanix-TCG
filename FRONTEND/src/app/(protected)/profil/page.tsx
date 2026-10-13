"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { Check, Copy, KeyRound, Link2, Loader2, MessageCircle, ScrollText, Unlink, UserRound } from "lucide-react";
import { toast } from "sonner";
import { OrnateCard } from "@/components/brand/OrnateCard";
import { ConfirmButton } from "@/components/common/ConfirmButton";
import { PageHeader, SectionTitle } from "@/components/common/PageHeader";
import { PasswordForm } from "@/components/common/PasswordForm";
import { EmptyState } from "@/components/common/States";
import { JeuBadge } from "@/components/seances/JeuBadge";
import { SemestreSelect } from "@/components/semestres/SemestreSelect";
import { PointsChart } from "@/components/stats/PointsChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MeApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CATEGORIES, formatDate, formatPoints, formatSigne, ROLE_LABELS, semestreLabel } from "@/lib/format";
import { errorMessage } from "@/lib/swr";

function InfosForm() {
    const { me, refresh } = useAuth();
    const [form, setForm] = useState({ prenom: me?.prenom ?? "", nom: me?.nom ?? "", classe: me?.classe ?? "" });
    const [loading, setLoading] = useState(false);
    const dirty = form.prenom !== me?.prenom || form.nom !== me?.nom || form.classe !== me?.classe;
    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await MeApi.update(form);
            await refresh();
            toast.success("Profil mis à jour");
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <Label htmlFor="p-prenom">Prénom</Label>
                    <Input id="p-prenom" value={form.prenom} onChange={set("prenom")} required maxLength={100} />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="p-nom">Nom</Label>
                    <Input id="p-nom" value={form.nom} onChange={set("nom")} required maxLength={100} />
                </div>
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="p-classe">Classe</Label>
                <Input id="p-classe" value={form.classe} onChange={set("classe")} required maxLength={50} />
            </div>
            <div className="space-y-1.5">
                <Label htmlFor="p-mail">Email</Label>
                <Input id="p-mail" value={me?.adresse_mail ?? ""} disabled />
                <p className="text-muted-foreground text-xs">Pour changer d&apos;email, contacte la modération.</p>
            </div>
            <Button type="submit" disabled={!dirty || loading} className="w-full sm:w-auto">
                {loading && <Loader2 className="animate-spin" />} Enregistrer
            </Button>
        </form>
    );
}

function DiscordLink() {
    const { me, refresh } = useAuth();
    const [code, setCode] = useState<{ code: string; expire_dans_minutes: number } | null>(null);
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const commande = code ? `/lier code:${code.code}` : "";

    const generer = async () => {
        setLoading(true);
        try {
            setCode(await MeApi.codeDiscord());
        } catch (err) {
            toast.error(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };
    const copier = async () => {
        try {
            await navigator.clipboard.writeText(commande);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            toast.error("Copie impossible, recopie la commande à la main.");
        }
    };

    if (me?.discord_lie) {
        return (
            <div className="space-y-4">
                <div className="border-success/30 bg-success/10 text-success flex items-center gap-2 rounded-lg border p-3 text-sm">
                    <Check className="size-4" /> Ton compte Discord est lié : tu peux utiliser <code>/points</code>, <code>/classement</code>…
                </div>
                <ConfirmButton
                    title="Délier ton compte Discord ?"
                    description="Les commandes du bot ne te reconnaîtront plus. Tu pourras le relier à tout moment."
                    confirmLabel="Délier"
                    onConfirm={async () => {
                        try {
                            await MeApi.delierDiscord();
                            await refresh();
                            toast.success("Compte Discord délié");
                        } catch (err) {
                            toast.error(errorMessage(err));
                        }
                    }}
                >
                    <Button variant="outline"><Unlink /> Délier Discord</Button>
                </ConfirmButton>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <ol className="text-muted-foreground list-inside list-decimal space-y-1 text-sm">
                <li>Génère un code ci-dessous (valable quelques minutes).</li>
                <li>Sur le serveur Discord de l&apos;asso, tape la commande affichée.</li>
            </ol>
            {code ? (
                <div className="space-y-2">
                    <div className="frame-gilded flex items-center justify-between gap-3 rounded-lg p-3">
                        <code className="text-gold font-mono text-lg font-bold tracking-wider break-all">{commande}</code>
                        <Button size="icon-sm" variant="ghost" onClick={copier} aria-label="Copier la commande">
                            {copied ? <Check className="text-success" /> : <Copy />}
                        </Button>
                    </div>
                    <p className="text-muted-foreground text-xs">
                        Expire dans {code.expire_dans_minutes} minutes.{" "}
                        <button className="text-gold underline" onClick={() => refresh()}>J&apos;ai lié mon compte</button>
                    </p>
                </div>
            ) : (
                <Button onClick={generer} disabled={loading}>
                    {loading ? <Loader2 className="animate-spin" /> : <Link2 />} Générer mon code
                </Button>
            )}
        </div>
    );
}

export default function ProfilPage() {
    const { me } = useAuth();
    const [semestreId, setSemestreId] = useState<number | undefined>();
    const { data: stats } = useSWR(["/me/stats", semestreId], () => MeApi.stats(semestreId));
    const { data: points } = useSWR("/me/points", () => MeApi.points());
    const { data: historique = [] } = useSWR(["/me/participations", semestreId], () => MeApi.participations(semestreId));
    const { data: ajustements = [] } = useSWR(["/me/ajustements", semestreId], () => MeApi.ajustements(semestreId));

    return (
        <div className="space-y-8">
            <PageHeader
                eyebrow={me ? `${ROLE_LABELS[me.role_utilisateur]} · ${me.classe}` : undefined}
                title={me ? `${me.prenom} ${me.nom}` : "Profil"}
                description="Tes informations, ta progression et ton grimoire de séances."
            />

            <div className="grid gap-4 sm:grid-cols-3">
                <OrnateCard className="flex flex-col sm:col-span-1 [&>div]:flex [&>div]:flex-1 [&>div]:flex-col" corners={false}>
                    <p className="text-muted-foreground text-xs font-semibold tracking-[0.2em] uppercase">Total cumulé</p>
                    <p className="font-display text-gilded mt-1 text-5xl font-bold tabular-nums">{formatPoints(points?.total ?? 0)}</p>
                    <ul className="mt-4 mb-4 space-y-1 text-sm">
                        {points?.semestres.map((s) => (
                            <li key={s.semestre_id} className="flex justify-between">
                                <span className="text-muted-foreground">{semestreLabel(s)}</span>
                                <span className="tabular-nums">{formatPoints(s.points)}</span>
                            </li>
                        ))}
                    </ul>
                    {stats?.semestre && (
                        <div className="mt-auto grid grid-cols-2 gap-3 border-t pt-4">
                            <div>
                                <p className="text-muted-foreground text-xs uppercase">Présences</p>
                                <p className="font-display text-2xl font-bold">{stats.presences}<span className="text-muted-foreground text-sm font-normal">/{stats.seances_semestre}</span></p>
                            </div>
                            <div>
                                <p className="text-muted-foreground text-xs uppercase">Assiduité</p>
                                <p className="font-display text-2xl font-bold">{Math.round(stats.taux_presence * 100)}%</p>
                            </div>
                        </div>
                    )}
                </OrnateCard>
                <Card className="sm:col-span-2">
                    <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                        <div>
                            <CardTitle>Progression</CardTitle>
                            <CardDescription>
                                {stats?.semestre ? `${semestreLabel(stats.semestre)} · ${formatPoints(stats.points)} pts${stats.rang ? ` · #${stats.rang}` : ""}` : "—"}
                            </CardDescription>
                        </div>
                        <SemestreSelect value={semestreId ?? stats?.semestre?.id} onChange={setSemestreId} className="w-full sm:w-48" />
                    </CardHeader>
                    <CardContent>
                        <PointsChart data={stats?.evolution ?? []} />
                    </CardContent>
                </Card>
            </div>

            <section id="historique" className="scroll-mt-24">
                <SectionTitle>Historique</SectionTitle>
                {ajustements.length > 0 && (
                    <ul className="bg-card mb-3 divide-y rounded-xl border">
                        {ajustements.map((a) => (
                            <li key={a.id} className="flex items-center gap-3 px-4 py-3">
                                <span className="text-lg" aria-hidden>{CATEGORIES[a.categorie]?.emoji}</span>
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium">{a.motif}</p>
                                    <p className="text-muted-foreground text-xs">{CATEGORIES[a.categorie]?.label} · {formatDate(a.cree_le.slice(0, 10), "jour")}</p>
                                </div>
                                <span className={`font-display text-sm font-bold whitespace-nowrap ${a.points > 0 ? "text-success" : "text-destructive"}`}>{formatSigne(a.points)}</span>
                            </li>
                        ))}
                    </ul>
                )}
                {historique.length ? (
                    <ul className="bg-card divide-y rounded-xl border">
                        {historique.map((p) => (
                            <li key={p.seance_id}>
                                <Link href={`/seances/${p.seance_id}`} className="hover:bg-accent/30 flex items-center gap-3 px-4 py-3 transition">
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-sm font-medium">{p.seance_nom}</p>
                                        <div className="text-muted-foreground mt-0.5 flex flex-wrap items-center gap-2 text-xs">
                                            {formatDate(p.date_seance, "jour")} <JeuBadge jeu={p.jeu} />
                                            {p.commentaire && <span className="italic">« {p.commentaire} »</span>}
                                        </div>
                                    </div>
                                    {p.present ? (
                                        <span className="text-gold font-display text-sm font-bold whitespace-nowrap">+{formatPoints(p.nb_point)}</span>
                                    ) : (
                                        <span className="text-destructive text-xs">Absent</span>
                                    )}
                                </Link>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <EmptyState icon={<ScrollText />} title="Ton grimoire est encore vierge" description="Tes participations apparaîtront ici." />
                )}
            </section>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><UserRound className="text-gold size-5" /> Mes informations</CardTitle>
                    </CardHeader>
                    <CardContent>{me && <InfosForm key={me.id} />}</CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><KeyRound className="text-gold size-5" /> Mot de passe</CardTitle>
                    </CardHeader>
                    <CardContent><PasswordForm /></CardContent>
                </Card>
                <Card id="discord" className="scroll-mt-24">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><MessageCircle className="text-gold size-5" /> Discord</CardTitle>
                        <CardDescription>Lie ton compte pour utiliser le bot et recevoir les annonces.</CardDescription>
                    </CardHeader>
                    <CardContent><DiscordLink /></CardContent>
                </Card>
            </div>
        </div>
    );
}
