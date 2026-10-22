"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth";
import { useStudentCounts } from "@/hooks/useStudents";
import { useTeachersSnapshot } from "@/hooks/useTeachers";
import { useSections } from "@/hooks/useAcademics";
import { useMyAssignedAssessments } from "@/hooks/useAssessments";
import { useMyAttendanceRecords, useMyAttendanceSummary } from "@/hooks/useAttendance";

const QUICK_LINKS = [
  { href: "/timetable", label: "Timetable", hint: "Create & publish schedules" },
  { href: "/attendance", label: "Attendance", hint: "Daily & period-wise marking" },
  { href: "/substitution", label: "Substitution", hint: "Smart substitute workflow" },
  { href: "/assessments", label: "Assessments", hint: "Question banks & results" },
  { href: "/analytics", label: "Analytics", hint: "Progress & workload reports" },
  { href: "/ai", label: "AI Studio", hint: "Generate content with human review" },
];

function MetricCard({
  label,
  value,
  href,
  loading,
}: {
  label: string;
  value: number | null;
  href: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {loading ? "…" : value === null || value === undefined ? "—" : value}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  if (!user) {
    return <p className="text-sm text-muted-foreground">Loading your dashboard…</p>;
  }

  if (user?.roles.includes("STUDENT")) {
    return <StudentDashboard name={user.full_name} />;
  }

  return <InstitutionDashboard name={user?.full_name ?? "there"} roles={user?.roles ?? []} />;
}

function InstitutionDashboard({ name, roles }: { name: string; roles: string[] }) {
  const counts = useStudentCounts();
  const teachers = useTeachersSnapshot();
  const sections = useSections();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Welcome, {name}</h1>
          <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening today.</p>
        </div>
        <div className="flex gap-2">
          {roles.map((role) => (
            <Badge key={role} variant="secondary">
              {role}
            </Badge>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Students"
          value={counts.data?.students ?? null}
          href="/students"
          loading={counts.isLoading}
        />
        <MetricCard
          label="Teachers"
          value={teachers.data ?? null}
          href="/students"
          loading={teachers.isLoading}
        />
        <MetricCard
          label="Guardians"
          value={counts.data?.guardians ?? null}
          href="/students"
          loading={counts.isLoading}
        />
        <MetricCard
          label="Sections"
          value={sections.data?.length ?? null}
          href="/timetable"
          loading={sections.isLoading}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {QUICK_LINKS.map((item) => (
          <Link key={item.href} href={item.href}>
            <Card className="h-full transition-colors hover:border-primary">
              <CardHeader>
                <CardTitle className="text-base">{item.label}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{item.hint}</CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StudentDashboard({ name }: { name: string }) {
  const today = new Date().toISOString().slice(0, 10);
  const { data: attendance } = useMyAttendanceSummary(today);
  const { data: attendanceRows } = useMyAttendanceRecords();
  const { data: assignments } = useMyAssignedAssessments();
  const pending = (assignments ?? []).filter((row) => row.status === "PENDING").length;
  const submitted = (assignments ?? []).filter((row) => row.status === "SUBMITTED").length;
  const attendanceStatus = attendance?.counts.PRESENT
    ? "Present"
    : attendance?.counts.ABSENT
      ? "Absent"
      : attendance?.counts.LATE
        ? "Late"
        : attendance?.marked
          ? "Marked"
          : "Not marked";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {name}</h1>
        <p className="text-sm text-muted-foreground">Your attendance and assigned assessments.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Today&apos;s attendance</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{attendanceStatus}</div><div className="mt-1 text-xs text-muted-foreground">{attendance?.date ?? today}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">My assessments</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{assignments?.length ?? 0}</div><div className="mt-1 text-xs text-muted-foreground">{pending} to take · {submitted} submitted</div></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Assigned assessments</CardTitle>
          <Link href="/assessments" className="text-sm text-primary hover:underline">Open assessments</Link>
        </CardHeader>
        <CardContent>
          {!assignments || assignments.length === 0 ? (
            <p className="py-4 text-sm text-muted-foreground">No assessments assigned yet.</p>
          ) : (
            <ul className="space-y-2">
              {assignments.slice(0, 5).map((row) => (
                <li key={row.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <div><div className="font-medium">{row.assessment_detail.title}</div><div className="text-xs text-muted-foreground">{row.assessment_detail.date} · {row.assessment_detail.total_marks} marks</div></div>
                  <Badge variant={row.status === "GRADED" ? "default" : "secondary"}>{row.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Recent attendance</CardTitle></CardHeader>
        <CardContent>
          {!attendanceRows || attendanceRows.length === 0 ? (
            <p className="py-3 text-sm text-muted-foreground">No attendance has been recorded yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {attendanceRows.slice(0, 5).map((row) => <li key={row.id} className="flex justify-between border-b pb-2 last:border-0"><span>{row.date}</span><Badge variant={row.status === "PRESENT" ? "default" : "secondary"}>{row.status_display}</Badge></li>)}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
