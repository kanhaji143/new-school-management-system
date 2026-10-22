"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAcademicYears, useSections, useSubjects } from "@/hooks/useAcademics";
import {
  useSyllabi,
  useCreateSyllabus,
  useChapters,
  useCreateChapter,
  useCompleteChapter,
  useLessonPlans,
  useCreateLessonPlan,
  useSessionLogs,
  useCreateSessionLog,
} from "@/hooks/useCurriculum";

export default function CurriculumPage() {
  const [selectedSyllabus, setSelectedSyllabus] = useState<number | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: syllabi } = useSyllabi();
  const { data: chapters } = useChapters(selectedSyllabus ?? undefined);
  const { data: lessonPlans } = useLessonPlans(selectedChapter ?? undefined);
  const { data: sessionLogs } = useSessionLogs();
  const { data: subjects } = useSubjects();
  const { data: sections } = useSections();
  const { data: years } = useAcademicYears();

  const createSyllabus = useCreateSyllabus();
  const createChapter = useCreateChapter();
  const completeChapter = useCompleteChapter();
  const createSessionLog = useCreateSessionLog();

  async function handleCreateSyllabus(formData: FormData) {
    setError(null); setMessage(null);
    try {
      await createSyllabus.mutateAsync({
        title: String(formData.get("title") ?? ""),
        subject: Number(formData.get("subject")),
        section: formData.get("section") ? Number(formData.get("section")) : null,
        academic_year: Number(formData.get("academic_year")),
      });
      setMessage("Syllabus created.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not create syllabus.");
    }
  }

  async function handleCreateChapter(formData: FormData) {
    if (!selectedSyllabus) return;
    setError(null); setMessage(null);
    try {
      await createChapter.mutateAsync({
        syllabusId: selectedSyllabus,
        title: String(formData.get("title") ?? ""),
        order_index: Number(formData.get("order_index") ?? 1),
      });
      setMessage("Chapter added.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not add chapter.");
    }
  }

  async function handleCreateLog(formData: FormData) {
    setError(null); setMessage(null);
    try {
      await createSessionLog.mutateAsync({
        subject: Number(formData.get("subject")),
        section: formData.get("section") ? Number(formData.get("section")) : null,
        topic: String(formData.get("topic") ?? ""),
        date: String(formData.get("date") ?? ""),
        status: String(formData.get("status") ?? "COMPLETED"),
        notes: String(formData.get("notes") ?? ""),
      });
      setMessage("Session log recorded.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not record session log.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Curriculum" description="Syllabi, chapters, lesson plans, session logs and completion." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create syllabus</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void handleCreateSyllabus(new FormData(e.currentTarget)); }}>
            <div className="space-y-1">
              <Label>Title</Label>
              <Input name="title" required />
            </div>
            <div className="space-y-1">
              <Label>Subject</Label>
              <select name="subject" className="h-9 w-full rounded-md border bg-background px-2 text-sm" required>
                {(subjects ?? []).map((s) => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Section</Label>
              <select name="section" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="">— none —</option>
                {(sections ?? []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Academic year</Label>
              <select name="academic_year" className="h-9 w-full rounded-md border bg-background px-2 text-sm" required>
                {(years ?? []).map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
              </select>
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={createSyllabus.isPending}>{createSyllabus.isPending ? "Saving…" : "Create syllabus"}</Button>
            </div>
          </form>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Syllabi</CardTitle>
          </CardHeader>
          <CardContent>
            {!syllabi || syllabi.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">No syllabi yet.</p>
            ) : (
              <ul className="space-y-2">
                {syllabi.map((s) => (
                  <li key={s.id}>
                    <button
                      className={`w-full rounded-md border p-2 text-left text-sm ${selectedSyllabus === s.id ? "bg-muted" : ""}`}
                      onClick={() => { setSelectedSyllabus(s.id); setSelectedChapter(null); }}
                    >
                      <div className="font-medium">{s.title}</div>
                      <div className="text-xs text-muted-foreground">
                        {s.subject_detail?.code} · {s.chapter_count} chapters
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">Chapters</CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedSyllabus ? (
              <p className="py-4 text-center text-sm text-muted-foreground">Select a syllabus.</p>
            ) : (
              <>
                <form className="mb-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); void handleCreateChapter(new FormData(e.currentTarget)); (e.currentTarget as HTMLFormElement).reset(); }}>
                  <Input name="title" placeholder="Chapter title" required className="flex-1" />
                  <Input name="order_index" type="number" placeholder="#" className="w-16" defaultValue={1} />
                  <Button type="submit" size="sm" disabled={createChapter.isPending}>Add</Button>
                </form>
                {!chapters || chapters.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">No chapters yet.</p>
                ) : (
                  <ul className="space-y-2">
                    {chapters.map((c) => (
                      <li key={c.id} className="rounded-md border p-2 text-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{c.order_index}. {c.title}</div>
                            <div className="text-xs text-muted-foreground">{c.lesson_plan_count} lesson plans</div>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant={c.completion_status === "COMPLETED" ? "default" : "secondary"}>
                              {c.completion_status}
                            </Badge>
                            {c.completion_status !== "COMPLETED" ? (
                              <Button size="sm" variant="outline" onClick={async () => {
                                try { await completeChapter.mutateAsync({ chapterId: c.id }); setMessage("Chapter completed."); }
                                catch (err) { setError((err as Error)?.message ?? "Failed."); }
                              }}>
                                Complete
                              </Button>
                            ) : null}
                            <Button size="sm" variant="ghost" onClick={() => setSelectedChapter(c.id)}>
                              {selectedChapter === c.id ? "Hide" : "Plans"}
                            </Button>
                          </div>
                        </div>
                        {selectedChapter === c.id ? (
                          <LessonPlansPanel chapterId={c.id} />
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Record class session</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void handleCreateLog(new FormData(e.currentTarget)); }}>
            <div className="space-y-1">
              <Label>Subject</Label>
              <select name="subject" className="h-9 w-full rounded-md border bg-background px-2 text-sm" required>
                {(subjects ?? []).map((s) => <option key={s.id} value={s.id}>{s.code}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Section</Label>
              <select name="section" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="">— none —</option>
                {(sections ?? []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Topic</Label>
              <Input name="topic" required />
            </div>
            <div className="space-y-1">
              <Label>Date</Label>
              <Input name="date" type="date" required />
            </div>
            <div className="space-y-1">
              <Label>Status</Label>
              <select name="status" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="COMPLETED">Completed</option>
                <option value="PARTIAL">Partial</option>
                <option value="SKIPPED">Skipped</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <Input name="notes" />
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={createSessionLog.isPending}>{createSessionLog.isPending ? "Saving…" : "Record session"}</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent session logs</CardTitle>
        </CardHeader>
        <CardContent>
          {!sessionLogs || sessionLogs.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No session logs yet.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {sessionLogs.slice(0, 10).map((l) => (
                <li key={l.id} className="flex items-center justify-between border-b py-1 last:border-0">
                  <span>{l.topic}</span>
                  <span className="text-xs text-muted-foreground">{l.date} · {l.status}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LessonPlansPanel({ chapterId }: { chapterId: number }) {
  const { data: plans } = useLessonPlans(chapterId);
  const createPlan = useCreateLessonPlan();
  const [title, setTitle] = useState("");

  return (
    <div className="mt-3 rounded-md bg-muted/40 p-2">
      <div className="mb-2 flex gap-2">
        <Input placeholder="Lesson plan title" value={title} onChange={(e) => setTitle(e.target.value)} className="flex-1" />
        <Button size="sm" onClick={async () => {
          if (!title.trim()) return;
          try { await createPlan.mutateAsync({ chapterId, title }); setTitle(""); }
          catch { /* ignore */ }
        }}>
          Add plan
        </Button>
      </div>
      {!plans || plans.length === 0 ? (
        <p className="text-xs text-muted-foreground">No lesson plans.</p>
      ) : (
        <ul className="space-y-1 text-xs">
          {plans.map((p) => (
            <li key={p.id} className="rounded border bg-background px-2 py-1">{p.title} ({p.duration_minutes}m)</li>
          ))}
        </ul>
      )}
    </div>
  );
}
