import HomeCta from "@/components/home/HomeCta";

export const metadata = {
    title: "Accueil — Arcanix",
    description: "Suivez vos points",
};

export default function HomePage() {
    return (
        <main className="min-h-screen">
            {/* Hero */}
            <section className="py-20 px-6 border-b">
                <div className="max-w-6xl mx-auto text-center">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                        Bienvenue sur <span className="text-primary">Arcanix</span>
                    </h1>
                    <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
                        Visualisez vos points par semestre et gérez vos participations facilement.
                    </p>

                    <div className="mt-8">
                        <HomeCta />
                    </div>
                </div>
            </section>
        </main>
    );
}