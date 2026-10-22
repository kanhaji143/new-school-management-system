import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers/Providers";

const inter = Inter({ subsets: ["latin"] });

// Changes whenever the app is rebuilt, so the runtime config is never stale.
const buildId = process.env.NEXT_PUBLIC_BUILD_ID ?? "dev";

export const metadata: Metadata = {
  title: "Smart School Manager",
  description: "Smart School & College Management Automation System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Runtime configuration (API host) for static deployments.
            Cache-busted so a redeploy picks up a new API host immediately. */}
        <script src={`/runtime-config.js?v=${buildId}`} />
      </head>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
