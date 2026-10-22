"use client";

import { useRouter } from "next/navigation";
import { Bell, LogOut, Menu, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";

export function Header() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center gap-3 border-b bg-background px-4 md:px-6">
      <Button variant="ghost" size="icon" className="md:hidden">
        <Menu className="h-5 w-5" />
      </Button>
      <div className="ml-auto flex items-center gap-2">
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-2 text-sm">
          <User className="h-5 w-5 text-muted-foreground" />
          <span className="hidden sm:inline">{user?.full_name ?? "—"}</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            logout();
            document.cookie = "smart-school-auth=; path=/; max-age=0";
            router.push("/login");
          }}
        >
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
