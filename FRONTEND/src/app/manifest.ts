import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
    return {
        name: "Arcanix — Association TCG",
        short_name: "Arcanix",
        description: "Séances, présences et classement de l'association Arcanix.",
        start_url: "/dashboard",
        display: "standalone",
        background_color: "#0b0a0c",
        theme_color: "#0b0a0c",
        lang: "fr",
        icons: [
            { src: "/brand/carte-192.png", sizes: "192x192", type: "image/png" },
            { src: "/brand/carte-512.png", sizes: "512x512", type: "image/png" },
            { src: "/brand/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
    };
}
