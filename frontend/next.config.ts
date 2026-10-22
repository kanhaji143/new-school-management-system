import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  async rewrites() {
    // Proxy API calls to the Django backend in development.
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
    return [{ source: "/backend-api/:path*", destination: `${api}/:path*` }];
  },
};

export default nextConfig;
