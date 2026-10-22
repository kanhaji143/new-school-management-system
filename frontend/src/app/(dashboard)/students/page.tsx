"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useStudents,
  useCreateStudent,
  useChangeStudentStatus,
} from "@/hooks/useStudents";
import { useAcademicYears, useSections } from "@/hooks/useAcademics";

const STATUS_OPTIONS = ["ACTIVE", "GRADUATED", "TRANSFERRED", "SUSPENDED", "DROPPED"] as const;

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Active",
  GRADUATED: "Graduated",
  TRANSFERRED: "Transferred",
  SUSPENDED: "Suspended",
  DROPPED: "Dropped",
};

export default function StudentsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading, isError, error } = useStudents({
    page,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const students = data?.items ?? [];
  const totalPages = data?.totalPages ?? 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Students"
        description="Enrolment records — the login account and STUDENT role are created automatically."
      />

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3 space-y-0">
          <CardTitle className="text-base">
            All students
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {data ? `${data.total} total` : ""}
            </span>
          </CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Search roll no. / name"
              className="w-56"
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
            <select
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={statusFilter}
              onChange={(e) => {
                setPage(1);
                setStatusFilter(e.target.value);
              }}
            >
              <option value="">Any status</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABEL[s]}
                </option>
              ))}
            </select>
            <Button onClick={() => setShowForm((v) => !v)}>
              {showForm ? "Close" : "Add student"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showForm ? (
            <StudentForm onDone={() => setShowForm(false)} />
          ) : null}

          {isLoading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Loading students…</p>
          ) : isError ? (
            <p className="py-8 text-center text-sm text-destructive">
              {(error as Error)?.message ?? "Could not load students."}
            </p>
          ) : students.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No students yet. Use &quot;Add student&quot; to enrol the first one.
            </p>
          ) : (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Roll no.</th>
                    <th className="py-2 pr-4 font-medium">Name</th>
                    <th className="py-2 pr-4 font-medium">Email</th>
                    <th className="py-2 pr-4 font-medium">Section</th>
                    <th className="py-2 pr-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-mono">{student.roll_number}</td>
                      <td className="py-2 pr-4">{student.user.full_name}</td>
                      <td className="py-2 pr-4 text-muted-foreground">{student.user.email}</td>
                      <td className="py-2 pr-4">
                        {student.section_detail
                          ? `${student.section_detail.school_class} ${student.section_detail.name}`
                          : "—"}
                      </td>
                      <td className="py-2 pr-4">
                        <StatusBadge status={student.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {totalPages > 1 ? (
            <div className="mt-4 flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant = status === "ACTIVE" ? "default" : "secondary";
  return <Badge variant={variant}>{STATUS_LABEL[status] ?? status}</Badge>;
}

function StudentForm({ onDone }: { onDone: () => void }) {
  const { data: sections } = useSections();
  const createStudent = useCreateStudent();
  const [formError, setFormError] = useState<string | null>(null);
  const [createdEmail, setCreatedEmail] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setFormError(null);
    setCreatedEmail(null);
    try {
      const response = await createStudent.mutateAsync({
        email: String(formData.get("email") ?? ""),
        first_name: String(formData.get("first_name") ?? ""),
        last_name: String(formData.get("last_name") ?? ""),
        password: String(formData.get("password") ?? ""),
        roll_number: String(formData.get("roll_number") ?? ""),
        admission_number: String(formData.get("admission_number") ?? ""),
        section: formData.get("section") ? Number(formData.get("section")) : null,
        status: "ACTIVE",
      });
      // The backend creates the login account + STUDENT role automatically.
      setCreatedEmail(response.data.user.email);
    } catch (err) {
      setFormError((err as Error)?.message ?? "Could not create the student.");
    }
  }

  return (
    <div className="mb-6 rounded-lg border bg-muted/40 p-4">
      <h3 className="text-sm font-semibold">Enrol a new student</h3>
      <p className="mt-1 text-xs text-muted-foreground">
        A login account and the STUDENT role are created automatically.
      </p>

      <form
        className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit(new FormData(e.currentTarget));
        }}
      >
        <Field label="First name" name="first_name" required />
        <Field label="Last name" name="last_name" required />
        <Field label="Email" name="email" type="email" required />
        <Field label="Temp password" name="password" type="password" required />
        <Field label="Roll no." name="roll_number" required />
        <Field label="Admission no." name="admission_number" required />
        <div className="space-y-1">
          <Label htmlFor="student-section">Section</Label>
          <select
            id="student-section"
            name="section"
            className="h-9 w-full rounded-md border bg-background px-2 text-sm"
          >
            <option value="">Unassigned</option>
            {(sections ?? []).map((section) => (
              <option key={section.id} value={section.id}>
                {section.school_class_detail.grade_level_detail?.name ?? ""} · {section.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
          <Button type="submit" disabled={createStudent.isPending}>
            {createStudent.isPending ? "Saving…" : "Create student"}
          </Button>
          <Button type="button" variant="outline" onClick={onDone}>
            Cancel
          </Button>
        </div>
      </form>

      {formError ? (
        <p className="mt-3 text-sm text-destructive">{formError}</p>
      ) : null}
      {createdEmail ? (
        <p className="mt-3 text-sm text-green-700">
          Student created — login email: <strong>{createdEmail}</strong>
        </p>
      ) : null}
    </div>
  );
}

function Field({ label, name, type = "text", required }: { label: string; name: string; type?: string; required?: boolean }) {
  return (
    <div className="space-y-1">
      <Label htmlFor={`student-${name}`}>{label}</Label>
      <Input id={`student-${name}`} name={name} type={type} required={required} />
    </div>
  );
}
