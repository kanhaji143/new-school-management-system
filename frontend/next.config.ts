import type { NextConfig } from "next";

// Static export is used for Firebase Hosting (no Node server available there).
// The backend URL is resolved at runtime from /runtime-config.js so the same
// build can be pointed at a different API host without rebuilding.
const isStaticExport = process.env.NEXT_STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(isStaticExport
    ? {
        output: "export" as const,
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {
        images: {
          remotePatterns: [{ protocol: "https", hostname: "**" }],
        },
        async rewrites() {
          // Proxy API calls to the Django backend in development.
          const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
          return [{ source: "/backend-api/:path*", destination: `${api}/:path*` }];
        },
      }),
};

export default nextConfig;
