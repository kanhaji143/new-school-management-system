"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Header } from "@/components/layout/Header";

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [hydrated, setHydrated] = useState(false);
  const isAuth = useAuthStore((s) => Boolean(s.accessToken));

  useEffect(() => setHydrated(true), []);
  useEffect(() => {
    if (hydrated && !isAuth) router.replace("/login");
  }, [hydrated, isAuth, router]);

  if (!hydrated || !isAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  return (
    <div className="min-h-screen">
      <Header />
      <main className="p-4 md:p-6">{children}</main>
    </div>
  );
}
