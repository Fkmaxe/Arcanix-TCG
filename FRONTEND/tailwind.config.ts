// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
    content: ["./src/app/**/*.{ts,tsx}", "./src/components/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                bg: "#0b0b0d",
                gold: "#f5c24b",
                ember1: "#ff3d2e",
                ember2: "#ff7a1a",
                ember3: "#ffd763",
                redDark: "#8b1e12",
                goldDark: "#b8902f",
                blackGold: "#1a1208",
            },
            backgroundImage: {
                "flame-gradient": "linear-gradient(135deg,#ff3d2e 0%,#ff7a1a 40%,#ffd763 100%)",
                "card-frame": "url('/images/flame-card-frame.svg')", // à extraire de ton logo si besoin
                "dark-flame": "radial-gradient(ellipse at center, #1a1208 0%, #0b0b0d 100%)"
            },
            boxShadow: {
                flame: "0 0 24px rgba(255, 122, 26, 0.25)",
            },
            fontFamily: {
                title: ['"Cinzel"', "serif"],
                body: ['"Inter"', "sans-serif"],
            },
            keyframes: {
                glow: { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.75 } },
                shimmer: {
                    "0%": { transform: "translateX(-100%)" },
                    "100%": { transform: "translateX(100%)" },
                },
                ember: {
                    "0%": { transform: "translateY(0) scale(1)", opacity: 0.0 },
                    "30%": { opacity: 0.8 },
                    "100%": { transform: "translateY(-120px) scale(0.6)", opacity: 0 },
                },
            },
            animation: {
                glow: "glow 3s ease-in-out infinite",
                ember: "ember 4s linear infinite",
            },
            borderRadius: { xl2: "1.25rem" },
        },
    },
    plugins: [],
};
export default config;