"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, CalendarDays, ClipboardCheck, Repeat,
  BookOpen, FileText, GraduationCap, BarChart3, Bell, Sparkles,
  Command, Settings, Baby,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/students", label: "Students", icon: Users },
  { href: "/timetable", label: "Timetable", icon: CalendarDays },
  { href: "/attendance", label: "Attendance", icon: ClipboardCheck },
  { href: "/substitution", label: "Substitution", icon: Repeat },
  { href: "/curriculum", label: "Curriculum", icon: BookOpen },
  { href: "/content", label: "Notes & HW", icon: FileText },
  { href: "/assessments", label: "Assessments", icon: GraduationCap },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/ai", label: "AI Studio", icon: Sparkles },
  { href: "/coordinator", label: "Coordinator", icon: Command },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const studentOnly = user?.roles.includes("STUDENT") ?? false;
  const visibleNav = studentOnly
    ? NAV.filter((item) => ["/dashboard", "/assessments"].includes(item.href))
    : NAV;
  return (
    <aside className="hidden w-64 flex-col border-r bg-card md:flex">
      <div className="flex h-16 items-center gap-2 border-b px-6 font-semibold">
        <Baby className="h-5 w-5 text-primary" />
        Smart School
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {visibleNav.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
