import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    output: "standalone",
    poweredByHeader: false,
    async redirects() {
        // Anciennes URLs -> nouvelle arborescence
        return [
            { source: "/me", destination: "/profil", permanent: true },
            { source: "/mod/seances", destination: "/gestion/seances", permanent: true },
            { source: "/admin/users", destination: "/gestion/membres", permanent: true },
            { source: "/admin/semestres", destination: "/gestion/semestres", permanent: true },
            { source: "/exports", destination: "/gestion/exports", permanent: true },
            { source: "/debug", destination: "/profil", permanent: false },
        ];
    },
    async headers() {
        return [
            {
                source: "/:path*",
                headers: [
                    { key: "X-Content-Type-Options", value: "nosniff" },
                    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
                    { key: "X-Frame-Options", value: "DENY" },
                ],
            },
        ];
    },
};

export default nextConfig;
