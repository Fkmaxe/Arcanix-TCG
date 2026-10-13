import Image from "next/image";
import { Flame, MessageCircle, Swords, Trophy } from "lucide-react";
import { Embers } from "@/components/brand/Embers";
import { Divider } from "@/components/brand/Ornament";
import { HomeCta, ProchainesSeances } from "@/components/home/HomeSections";

export default function HomePage() {
    return (
        <div className="space-y-12 sm:space-y-16">
            {/* Hero */}
            <section className="relative -mx-4 overflow-hidden px-4 pt-4 pb-6 sm:-mx-6 sm:px-6">
                <Embers />
                <div className="relative mx-auto flex max-w-3xl flex-col items-center text-center">
                    <Image
                        src="/brand/carte.webp"
                        alt="Emblème Arcanix : une carte enflammée aux ornements dorés"
                        width={480}
                        height={601}
                        priority
                        className="animate-flicker h-auto w-36 sm:w-48"
                    />
                    <p className="text-ember mt-6 text-xs font-semibold tracking-[0.3em] uppercase">Association de TCG</p>
                    <h1 className="text-gilded mt-2 text-5xl font-bold tracking-[0.12em] sm:text-7xl">ARCANIX</h1>
                    <p className="text-muted-foreground mt-4 max-w-xl text-base sm:text-lg">
                        Tournois, drafts et soirées découverte : participe aux séances, gagne des points et grave ton nom au sommet du classement.
                    </p>
                    <div className="mt-8 w-full sm:w-auto">
                        <HomeCta />
                    </div>
                </div>
            </section>

            <Divider className="mx-auto max-w-md" />

            <ProchainesSeances />

            {/* Comment ça marche */}
            <section>
                <h2 className="text-gilded mb-6 text-center text-2xl font-bold">Le chemin du champion</h2>
                <ol className="grid gap-3 sm:grid-cols-3 sm:gap-4">
                    {[
                        { icon: Swords, titre: "Participe", texte: "Viens aux séances de l'asso : tournois, drafts, initiations…" },
                        { icon: Flame, titre: "Gagne des points", texte: "Chaque présence validée rapporte des points sur le semestre." },
                        { icon: Trophy, titre: "Grimpe au classement", texte: "Le podium du semestre est annoncé sur le Discord." },
                    ].map(({ icon: Icon, titre, texte }, i) => (
                        <li key={titre} className="bg-card relative rounded-xl border p-4 sm:p-5">
                            <span className="font-display text-gold/20 absolute top-2 right-4 text-4xl font-bold">{i + 1}</span>
                            <Icon className="text-ember mb-3 size-7" />
                            <h3 className="text-lg font-semibold">{titre}</h3>
                            <p className="text-muted-foreground mt-1 text-sm">{texte}</p>
                        </li>
                    ))}
                </ol>
                <p className="text-muted-foreground mt-6 text-center text-sm">
                    <MessageCircle className="text-gold mr-1.5 inline size-4 align-[-3px]" />
                    Sur le Discord, tape <code className="bg-muted text-gold rounded px-1.5 py-0.5">/register</code> pour créer ton compte en 30 secondes.
                </p>
            </section>
        </div>
    );
}
