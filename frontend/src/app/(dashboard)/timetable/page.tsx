"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useAcademicYears,
  useSections,
  useSubjects,
} from "@/hooks/useAcademics";
import {
  useAddTimetableEntry,
  useCreateTimetable,
  usePeriodTemplates,
  usePublishTimetable,
  useTimetableGrid,
  useTimetables,
  useValidateTimetable,
  type GridEntry,
  type ValidationReport,
} from "@/hooks/useTimetable";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

interface AxiosErrorLike {
  response?: { data?: { message?: string } };
}

function errorMessage(err: unknown, fallback: string): string {
  const axiosError = err as AxiosErrorLike;
  return axiosError?.response?.data?.message ?? fallback;
}

function gridHasEntries(grid: Record<string, GridEntry[]>): boolean {
  return Object.values(grid).some((entries) => entries.length > 0);
}

export default function TimetablePage() {
  const { data: years } = useAcademicYears();
  const { data: sections } = useSections();
  const activeYear = years?.find((year) => year.is_active);

  const [sectionId, setSectionId] = useState<number | null>(null);
  const [draftId, setDraftId] = useState<number | null>(null);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const effectiveSection = sectionId ?? sections?.[0]?.id ?? null;

  const { data: timetables, isLoading } = useTimetables({
    section: effectiveSection ?? undefined,
  });

  const draftList = timetables?.filter((item) => item.status === "DRAFT") ?? [];
  const publishedList = timetables?.filter((item) => item.status === "PUBLISHED") ?? [];
  const activeDraft =
    draftList.find((item) => item.id === draftId) ?? draftList[0] ?? null;

  const { data: gridData } = useTimetableGrid(activeDraft?.id ?? undefined);
  const validateTimetable = useValidateTimetable();
  const publishTimetable = usePublishTimetable();
  const createTimetable = useCreateTimetable();

  function handleValidate() {
    if (!activeDraft) return;
    void validateTimetable
      .mutateAsync(activeDraft.id)
      .then((result) => {
        setReport(result);
        setNotice(null);
        setError(null);
      })
      .catch((err) => setError(errorMessage(err, "Validation failed.")));
  }

  function handlePublish() {
    if (!activeDraft) return;
    void publishTimetable
      .mutateAsync(activeDraft.id)
      .then(() => {
        setNotice("Timetable published.");
        setReport(null);
        setError(null);
      })
      .catch((err) => setError(errorMessage(err, "Could not publish.")));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Timetable"
        description={`Draft → validate → publish. ${activeYear ? `Active year: ${activeYear.name}` : "No active academic year."}`}
      />

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3 space-y-0">
          <CardTitle className="text-base">
            {effectiveSection
              ? `Section: ${sections?.find((s) => s.id === effectiveSection)?.name ?? ""}`
              : "No sections yet"}
          </CardTitle>
          <div className="flex items-center gap-2">
            <select
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={effectiveSection ?? ""}
              onChange={(event) => {
                setSectionId(Number(event.target.value));
                setDraftId(null);
                setReport(null);
                setError(null);
                setNotice(null);
              }}
            >
              {(sections ?? []).map((section) => (
                <option key={section.id} value={section.id}>
                  {section.name}
                </option>
              ))}
            </select>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                if (!activeYear || !effectiveSection) {
                  setError("No active academic year or section available.");
                  return;
                }
                void createTimetable
                  .mutateAsync({ section: effectiveSection, academic_year: activeYear.id })
                  .then((created) => {
                    setDraftId(created.id);
                    setNotice(`Draft v${created.version} created.`);
                    setReport(null);
                    setError(null);
                  })
                  .catch((err) => setError(errorMessage(err, "Could not create the draft.")));
              }}
            >
              New draft
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {notice ? <p className="text-sm text-green-700">{notice}</p> : null}
          {error ? <p className="text-sm text-destructive">{error}</p> : null}

          {isLoading ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Loading timetables…</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {publishedList.length === 0 && draftList.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No timetables yet — create a draft to start.
                </p>
              ) : null}
              {publishedList.map((item) => (
                <Badge key={item.id} variant="secondary">
                  Published v{item.version} · {item.entry_count} periods
                </Badge>
              ))}
              {draftList.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setDraftId(item.id);
                    setReport(null);
                    setError(null);
                  }}
                >
                  <Badge variant={activeDraft?.id === item.id ? "default" : "outline"}>
                    Draft v{item.version} · {item.entry_count} periods
                  </Badge>
                </button>
              ))}
            </div>
          )}

          {activeDraft ? (
            <DraftPanel
              draftId={activeDraft.id}
              grid={gridData?.grid ?? {}}
              report={report}
              onValidate={handleValidate}
              onPublish={handlePublish}
              validating={validateTimetable.isPending}
              publishing={publishTimetable.isPending}
            />
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

interface DraftPanelProps {
  draftId: number;
  grid: Record<string, GridEntry[]>;
  report: ValidationReport | null;
  onValidate: () => void;
  onPublish: () => void;
  validating: boolean;
  publishing: boolean;
}

function DraftPanel({
  draftId,
  grid,
  report,
  onValidate,
  onPublish,
  validating,
  publishing,
}: DraftPanelProps) {
  const { data: subjects } = useSubjects();
  const { data: periods } = usePeriodTemplates();
  const addEntry = useAddTimetableEntry();
  const [formError, setFormError] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" onClick={onValidate} disabled={validating}>
          {validating ? "Checking…" : "Validate"}
        </Button>
        <Button size="sm" onClick={onPublish} disabled={publishing}>
          {publishing ? "Publishing…" : "Publish"}
        </Button>
      </div>

      {report ? (
        <div className="rounded-lg border bg-muted/40 p-3 text-sm">
          <p className="font-medium">
            {report.hardCount === 0
              ? "No hard conflicts"
              : `${report.hardCount} hard conflict(s)`}
            {report.softCount > 0 ? ` · ${report.softCount} soft warning(s)` : ""}
          </p>
          <p className={report.canPublish ? "mt-1 text-green-700" : "mt-1 text-destructive"}>
            {report.canPublish ? "Safe to publish." : "Resolve hard conflicts before publishing."}
          </p>
          {report.conflicts.length > 0 ? (
            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
              {report.conflicts.map((conflict) => (
                <li key={conflict.id}>
                  <Badge variant={conflict.severity === "HARD" ? "destructive" : "secondary"}>
                    {conflict.conflictType}
                  </Badge>{" "}
                  {conflict.description}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <form
        className="grid gap-3 rounded-lg border p-3 sm:grid-cols-2 lg:grid-cols-5"
        onSubmit={(event) => {
          event.preventDefault();
          const formData = new FormData(event.currentTarget);
          setFormError(null);
          void addEntry
            .mutateAsync({
              timetable: draftId,
              day: Number(formData.get("day")),
              period: Number(formData.get("period")),
              subject: Number(formData.get("subject")),
              room: String(formData.get("room") ?? ""),
            })
            .then(() => setFormError(null))
            .catch((err) => setFormError(errorMessage(err, "Could not add the entry.")));
          (event.target as HTMLFormElement).reset();
        }}
      >
        <div className="space-y-1">
          <Label htmlFor="entry-day">Day</Label>
          <select
            id="entry-day"
            name="day"
            className="h-9 w-full rounded-md border bg-background px-2 text-sm"
          >
            {DAYS.map((day, index) => (
              <option key={day} value={index + 1}>{day}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="entry-period">Period</Label>
          <select
            id="entry-period"
            name="period"
            className="h-9 w-full rounded-md border bg-background px-2 text-sm"
          >
            {(periods ?? [])
              .filter((period) => period.day === 1)
              .map((period, index) => (
                <option key={period.id} value={period.id}>
                  Period {index + 1} ({period.start_time})
                </option>
              ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="entry-subject">Subject</Label>
          <select
            id="entry-subject"
            name="subject"
            className="h-9 w-full rounded-md border bg-background px-2 text-sm"
          >
            {(subjects ?? []).map((subject) => (
              <option key={subject.id} value={subject.id}>{subject.name}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="entry-room">Room</Label>
          <Input id="entry-room" name="room" placeholder="101" />
        </div>
        <div className="flex items-end">
          <Button type="submit" disabled={addEntry.isPending}>
            {addEntry.isPending ? "Saving…" : "Add entry"}
          </Button>
        </div>
        {formError ? (
          <p className="text-xs text-destructive sm:col-span-2 lg:col-span-5">{formError}</p>
        ) : null}
      </form>

      <div className="overflow-x-auto">
        {gridHasEntries(grid) ? (
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                {DAYS.map((day) => (
                  <th key={day} className="py-2 pr-3 font-medium">{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                {DAYS.map((day) => (
                  <td key={day} className="align-top py-2 pr-3">
                    {(grid[day] ?? []).map((entry) => (
                      <div key={entry.id} className="mb-2 rounded border px-2 py-1 text-xs">
                        <div className="font-medium">{entry.subject?.name ?? "—"}</div>
                        <div className="text-muted-foreground">
                          {entry.period_start}–{entry.period_end}
                          {entry.teacher ? ` · ${entry.teacher.full_name}` : ""}
                        </div>
                        {entry.room ? (
                          <div className="text-muted-foreground">Room {entry.room}</div>
                        ) : null}
                      </div>
                    ))}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        ) : (
          <p className="py-6 text-center text-sm text-muted-foreground">
            This draft has no entries yet — add one above.
          </p>
        )}
      </div>
    </div>
  );
}
