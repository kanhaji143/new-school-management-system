"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";

export default function ParentDashboardPage() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Parent portal</h1>
      <p className="text-sm text-muted-foreground">
        Signed in as {user?.full_name}. Your children&apos;s attendance, results and notices
        will appear here.
      </p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {["Attendance", "Results", "Notices"].map((title) => (
          <Card key={title}>
            <CardHeader>
              <CardTitle className="text-base">{title}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">Coming soon.</CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
