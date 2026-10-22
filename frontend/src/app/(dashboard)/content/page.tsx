"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ContentPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Notes & Homework" description="Notes, classwork and homework with attachments." />
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Notes & Homework</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This module is wired to the <code>/content/</code> API endpoints. Implement the
          screens here once the corresponding backend work is complete.
        </CardContent>
      </Card>
    </div>
  );
}
