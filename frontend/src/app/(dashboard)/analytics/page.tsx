"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Student progress, teacher workload and institution overview." />
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Analytics</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This module is wired to the <code>/analytics/</code> API endpoints. Implement the
          screens here once the corresponding backend work is complete.
        </CardContent>
      </Card>
    </div>
  );
}
