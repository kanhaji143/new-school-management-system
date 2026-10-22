"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAcademicYears, useSections, useSubjects } from "@/hooks/useAcademics";
import { useStudents } from "@/hooks/useStudents";
import { useAuthStore } from "@/store/auth";
import {
  useAssessments,
  useCreateAssessment,
  useAssessmentResults,
  useAssessmentQuestions,
  useSubmitMarks,
  usePreviewQuestionImport,
  useRefreshQuestionImport,
  useConfirmQuestionImport,
  useAssessmentAssignments,
  useAssignStudents,
  useSubmitStudentAnswers,
  useMyAssignedAssessments,
  type AssessmentItem,
  type QuestionImportItem,
  type StudentAssignedAssessment,
} from "@/hooks/useAssessments";

export default function AssessmentsPage() {
  const user = useAuthStore((state) => state.user);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: assessments } = useAssessments();
  const { data: subjects } = useSubjects();
  const { data: sections } = useSections();
  const { data: years } = useAcademicYears();
  const create = useCreateAssessment();

  async function handleCreate(formData: FormData) {
    setError(null); setMessage(null);
    try {
      await create.mutateAsync({
        title: String(formData.get("title") ?? ""),
        assessment_type: String(formData.get("assessment_type") ?? "TEST"),
        subject: formData.get("subject") ? Number(formData.get("subject")) : null,
        section: formData.get("section") ? Number(formData.get("section")) : null,
        academic_year: Number(formData.get("academic_year")),
        date: String(formData.get("date") ?? ""),
        total_marks: Number(formData.get("total_marks") ?? 100),
        pass_marks: Number(formData.get("pass_marks") ?? 40),
      });
      setMessage("Assessment created.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not create assessment.");
    }
  }

  if (user?.roles.includes("STUDENT")) return <StudentAssignmentsPage />;

  return (
    <div className="space-y-6">
      <PageHeader title="Assessments" description="Question banks, tests, marks entry and results." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create assessment</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void handleCreate(new FormData(e.currentTarget)); }}>
            <div className="space-y-1">
              <Label>Title</Label>
              <Input name="title" required />
            </div>
            <div className="space-y-1">
              <Label>Type</Label>
              <select name="assessment_type" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="TEST">Test</option>
                <option value="QUIZ">Quiz</option>
                <option value="EXAM">Exam</option>
                <option value="ASSIGNMENT">Assignment</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Subject</Label>
              <select name="subject" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="">— none —</option>
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
              <Label>Academic year</Label>
              <select name="academic_year" className="h-9 w-full rounded-md border bg-background px-2 text-sm" required>
                {(years ?? []).map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Date</Label>
              <Input name="date" type="date" required />
            </div>
            <div className="space-y-1">
              <Label>Total marks</Label>
              <Input name="total_marks" type="number" defaultValue={100} />
            </div>
            <div className="space-y-1">
              <Label>Pass marks</Label>
              <Input name="pass_marks" type="number" defaultValue={40} />
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={create.isPending}>{create.isPending ? "Saving…" : "Create assessment"}</Button>
            </div>
          </form>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Assessments</CardTitle>
        </CardHeader>
        <CardContent>
          {!assessments || assessments.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No assessments yet.</p>
          ) : (
            <ul className="space-y-2">
              {assessments.map((a) => (
                <li key={a.id} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <div>
                    <div className="font-medium">{a.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {a.assessment_type} · {a.subject_detail?.code ?? "General"} · {a.question_count} question(s) · {a.marks_entered} mark entries
                    </div>
                  </div>
                  <Button size="sm" variant={selectedId === a.id ? "default" : "outline"} onClick={() => setSelectedId(selectedId === a.id ? null : a.id)}>
                    {selectedId === a.id ? "Close" : "Manage questions & marks"}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {selectedId ? (() => {
        const selected = assessments?.find((item) => item.id === selectedId);
        return selected ? <ManagePanel assessment={selected} onClose={() => setSelectedId(null)} /> : null;
      })() : null}
    </div>
  );
}

function StudentAssignmentsPage() {
  const { data: assignments, isLoading, isError } = useMyAssignedAssessments();
  const [activeId, setActiveId] = useState<number | null>(null);
  const activeAssignment = assignments?.find((assignment) => assignment.id === activeId) ?? null;

  return (
    <div className="space-y-6">
      <PageHeader title="My assessments" description="Assessments assigned to you, their dates and results." />
      {isLoading ? <p className="text-sm text-muted-foreground">Loading your assessments…</p> : null}
      {isError ? <p className="text-sm text-destructive">Could not load your assessments.</p> : null}
      {!isLoading && !isError && (!assignments || assignments.length === 0) ? (
        <Card><CardContent className="py-8 text-center text-sm text-muted-foreground">No assessments have been assigned to you yet.</CardContent></Card>
      ) : null}
      <div className="grid gap-3 md:grid-cols-2">
        {(assignments ?? []).map((row) => (
          <Card key={row.id}>
            <CardHeader className="flex flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle className="text-base">{row.assessment_detail.title}</CardTitle>
                <p className="mt-1 text-xs text-muted-foreground">
                  {row.assessment_detail.assessment_type} · {row.assessment_detail.subject_detail?.name ?? "General"} · {row.assessment_detail.date}
                </p>
              </div>
              <Badge variant={row.status === "GRADED" ? "default" : "secondary"}>{row.status === "GRADED" ? "Graded" : "Assigned"}</Badge>
            </CardHeader>
            <CardContent className="text-sm">
              <p>Total marks: {row.assessment_detail.total_marks}</p>
              {row.status === "GRADED" ? (
                <p className="mt-1 font-medium">Your marks: {row.obtained_marks ?? "—"} · Grade: {row.grade || "—"}</p>
              ) : row.status === "SUBMITTED" ? (
                <p className="mt-1 text-green-700">Your answers have been submitted. Waiting for teacher review.</p>
              ) : (
                <p className="mt-1 text-muted-foreground">{row.questions.length} question(s) · ready to take</p>
              )}
              {row.status === "PENDING" ? (
                <Button className="mt-3" size="sm" disabled={!row.questions.length} onClick={() => setActiveId(row.id)}>
                  Take assessment
                </Button>
              ) : (
                <Button className="mt-3" size="sm" variant="outline" onClick={() => setActiveId(row.id)}>
                  View answer sheet
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      {activeAssignment ? (
        activeAssignment.status === "PENDING" ? (
          <StudentAttemptPanel assignment={activeAssignment} onClose={() => setActiveId(null)} />
        ) : (
          <StudentAnswerReview assignment={activeAssignment} onClose={() => setActiveId(null)} />
        )
      ) : null}
    </div>
  );
}

function StudentAnswerReview({ assignment, onClose }: { assignment: StudentAssignedAssessment; onClose: () => void }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">Answer sheet: {assignment.assessment_detail.title}</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Status: {assignment.status} · Marks: {assignment.obtained_marks ?? "Pending"} / {assignment.assessment_detail.total_marks} · Grade: {assignment.grade || "Pending"}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {assignment.questions.map((question, index) => (
          <div key={question.id} className="rounded-md border p-3 text-sm">
            <div className="font-medium">{index + 1}. {question.text}</div>
            <div className="mt-1 text-xs text-muted-foreground">{question.question_type.replace("_", " ")} · {question.marks} mark(s)</div>
            <div className="mt-2 rounded bg-muted/30 p-2">
              <span className="text-xs font-medium text-muted-foreground">Your answer: </span>
              <span>{String(assignment.answers?.[String(question.id)] ?? "Not answered")}</span>
            </div>
          </div>
        ))}
        {assignment.status === "SUBMITTED" ? (
          <p className="text-sm text-amber-700">Your answer sheet is awaiting teacher grading.</p>
        ) : (
          <p className="text-sm text-green-700">Teacher grading is complete. Marks and grade are shown above.</p>
        )}
      </CardContent>
    </Card>
  );
}

function StudentAttemptPanel({ assignment, onClose }: { assignment: StudentAssignedAssessment; onClose: () => void }) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const submit = useSubmitStudentAnswers();

  async function handleSubmit() {
    setError(null);
    try {
      await submit.mutateAsync({ assignmentId: assignment.id, answers });
      onClose();
    } catch (err) {
      setError((err as Error)?.message ?? "Could not submit answers.");
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{assignment.assessment_detail.title}</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {assignment.questions.map((question, index) => {
          const key = String(question.id);
          const options = question.options.length
            ? question.options
            : question.question_type === "TRUE_FALSE" ? ["True", "False"] : [];
          return (
            <div key={question.id} className="rounded-lg border p-4">
              <div className="font-medium">{index + 1}. {question.text}</div>
              <div className="mt-1 text-xs text-muted-foreground">{question.question_type.replace("_", " ")} · {question.marks} mark(s)</div>
              {options.length ? (
                <div className="mt-3 space-y-2">
                  {options.map((option) => (
                    <label key={option} className="flex items-center gap-2 text-sm">
                      <input type="radio" name={`answer-${question.id}`} value={option} checked={answers[key] === option} onChange={() => setAnswers((current) => ({ ...current, [key]: option }))} />
                      {option}
                    </label>
                  ))}
                </div>
              ) : (
                <textarea className="mt-3 min-h-24 w-full rounded-md border bg-background p-3 text-sm" placeholder="Write your answer" value={answers[key] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [key]: event.target.value }))} />
              )}
            </div>
          );
        })}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <Button onClick={handleSubmit} disabled={submit.isPending}>
          {submit.isPending ? "Submitting…" : "Submit assessment"}
        </Button>
      </CardContent>
    </Card>
  );
}

function ManagePanel({ assessment, onClose }: { assessment: AssessmentItem; onClose: () => void }) {
  const assessmentId = assessment.id;
  const panelRef = useRef<HTMLDivElement>(null);
  const { data: results } = useAssessmentResults(assessmentId);
  const { data: importedQuestions } = useAssessmentQuestions(assessmentId);
  const { data: studentsPage } = useStudents({ status: "ACTIVE", section: assessment.section ?? undefined, pageSize: 200 });
  const { data: assignments } = useAssessmentAssignments(assessmentId);
  const submitMarks = useSubmitMarks();
  const assignStudents = useAssignStudents();
  const previewImport = usePreviewQuestionImport();
  const refreshImport = useRefreshQuestionImport();
  const confirmImport = useConfirmQuestionImport();
  const [marks, setMarks] = useState<Record<number, string>>({});
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  const [assignmentMessage, setAssignmentMessage] = useState<string | null>(null);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [importText, setImportText] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [importPreview, setImportPreview] = useState<QuestionImportItem | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const rosterStudents = studentsPage?.items ?? [];
  const assignedIds = new Set((assignments ?? []).map((row) => row.student));
  const assignedStudents = rosterStudents.filter((student) => assignedIds.has(student.id));
  const descriptiveQuestionIds = useMemo(
    () => new Set(
      (importedQuestions ?? [])
        .filter((item) => ["SHORT", "LONG"].includes(item.question_detail.question_type))
        .map((item) => String(item.question))
    ),
    [importedQuestions],
  );
  const descriptiveAssignments = (assignments ?? []).filter((assignment) =>
    assignment.status === "SUBMITTED" &&
    Object.keys(assignment.answers ?? {}).some((questionId) => descriptiveQuestionIds.has(questionId))
  );

  useEffect(() => {
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  async function handleAssignStudents() {
    setAssignmentError(null); setAssignmentMessage(null);
    try {
      const result = await assignStudents.mutateAsync({ assessmentId, students: selectedStudentIds });
      setSelectedStudentIds([]);
      setAssignmentMessage(`${result.created} student(s) assigned; ${result.already_assigned} were already assigned.`);
    } catch (err) {
      setAssignmentError((err as Error)?.message ?? "Could not assign students.");
    }
  }

  async function handleQuestionPreview() {
    setImportError(null);
    try {
      const item = importPreview
        ? await refreshImport.mutateAsync({ id: importPreview.id, text: importText, file: importFile })
        : await previewImport.mutateAsync({ assessmentId, text: importText, file: importFile });
      setImportPreview(item);
      setImportFile(null);
      setFileInputKey((value) => value + 1);
    } catch (err) {
      setImportError((err as Error)?.message ?? "Could not read the questions.");
    }
  }

  async function handleConfirmImport() {
    if (!importPreview) return;
    setImportError(null);
    try {
      const item = await confirmImport.mutateAsync(importPreview.id);
      setImportPreview(item);
    } catch (err) {
      setImportError((err as Error)?.message ?? "Could not import questions.");
    }
  }

  async function handleSubmit() {
    setError(null); setMessage(null);
    if (descriptiveAssignments.length === 0) { setError("No submitted descriptive answers are awaiting grading."); return; }
    try {
      const result = await submitMarks.mutateAsync({
        id: assessmentId,
        records: descriptiveAssignments.map((assignment) => ({
          student: assignment.student,
          // This is the final total: objective auto-marks are prefilled and
          // the teacher can add the descriptive marks before saving.
          obtained_marks: marks[assignment.student] ?? "0",
          status: "GRADED",
        })),
      });
      setMessage(`Saved — ${result.created} created, ${result.corrected} corrected.`);
    } catch (err) {
      setError((err as Error)?.message ?? "Could not save marks.");
    }
  }

  return (
    <div ref={panelRef} className="scroll-mt-20">
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Manage assessment #{assessmentId}</CardTitle>
        <Button size="sm" variant="ghost" onClick={onClose}>Close</Button>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-semibold">Assign students</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {assessment.section_detail
              ? `Showing active students in section ${assessment.section_detail.name}.`
              : "This assessment has no section set; choose students from the institution roster."}
            {" "}Assigned students will appear in the marks table below.
          </p>
          {rosterStudents.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">No active students found for this assessment.</p>
          ) : (
            <div className="mt-3 max-h-48 space-y-1 overflow-y-auto">
              {rosterStudents.map((student) => {
                const alreadyAssigned = assignedIds.has(student.id);
                return (
                  <label key={student.id} className="flex items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-muted/60">
                    <input
                      type="checkbox"
                      checked={alreadyAssigned || selectedStudentIds.includes(student.id)}
                      disabled={alreadyAssigned}
                      onChange={(e) => setSelectedStudentIds((current) => e.target.checked
                        ? [...current, student.id]
                        : current.filter((id) => id !== student.id))}
                    />
                    <span className="font-mono text-xs">{student.roll_number}</span>
                    <span>{student.user.full_name}</span>
                    {alreadyAssigned ? <Badge variant="secondary" className="ml-auto">Assigned</Badge> : null}
                  </label>
                );
              })}
            </div>
          )}
          <Button className="mt-3" size="sm" onClick={handleAssignStudents} disabled={!selectedStudentIds.length || assignStudents.isPending}>
            {assignStudents.isPending ? "Assigning…" : `Assign selected (${selectedStudentIds.length})`}
          </Button>
          {assignmentMessage ? <p className="mt-2 text-sm text-green-700">{assignmentMessage}</p> : null}
          {assignmentError ? <p className="mt-2 text-sm text-destructive">{assignmentError}</p> : null}
        </div>

        <div className="rounded-lg border bg-muted/20 p-4">
          <h3 className="text-sm font-semibold">Import questions & vocabulary</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Paste the template or attach PDF, JPEG/PNG, DOC/DOCX, Excel, CSV or TXT. Review the preview before importing.
          </p>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`question-import-text-${assessmentId}`}>Copy/paste format</Label>
              <textarea
                id={`question-import-text-${assessmentId}`}
                className="min-h-48 w-full rounded-md border bg-background p-3 font-mono text-xs"
                placeholder={'Q: What is evaporation?\nType: SHORT\nMarks: 2\nDifficulty: EASY\nVocabulary: evaporation - liquid changing to gas; vapour - gas form\n\nQ: Which planet is known as the Red Planet?\nType: MCQ\nOptions: Earth | Mars | Venus\nAnswer: Mars\nMarks: 1'}
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Use blank lines between questions. Vocabulary terms are separated by semicolons.</p>
            </div>
            <div className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor={`question-import-file-${assessmentId}`}>Browse for a file (max 10 MB)</Label>
                <Input
                  key={fileInputKey}
                  id={`question-import-file-${assessmentId}`}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.csv,.txt"
                  onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
                />
                {importFile ? <p className="text-xs text-muted-foreground">Selected: {importFile.name}</p> : null}
              </div>
              <Button
                variant="outline"
                onClick={handleQuestionPreview}
                disabled={previewImport.isPending || refreshImport.isPending || (!importText.trim() && !importFile)}
              >
                {previewImport.isPending || refreshImport.isPending ? "Reading…" : importPreview ? "Update preview" : "Preview import"}
              </Button>
              {importError ? <p className="text-sm text-destructive">{importError}</p> : null}
              {importPreview?.extraction_warning ? (
                <p className="rounded-md bg-amber-500/10 p-2 text-xs text-amber-800">{importPreview.extraction_warning}</p>
              ) : null}
              {importPreview ? (
                <div className="space-y-2">
                  <div className="text-xs font-medium">
                    {importPreview.original_file_name ? `Attached: ${importPreview.original_file_name} · ` : ""}
                    {importPreview.parsed_questions.length} question(s) found · {importPreview.status}
                  </div>
                  <div className="max-h-56 space-y-2 overflow-y-auto">
                    {importPreview.parsed_questions.map((q, index) => (
                      <div key={`${index}-${q.text}`} className="rounded-md border bg-background p-2 text-xs">
                        <div className="font-medium">{index + 1}. {q.text}</div>
                        <div className="mt-1 text-muted-foreground">{q.question_type} · {q.marks} mark(s){q.options.length ? ` · ${q.options.join(" / ")}` : ""}</div>
                        {q.vocabulary_terms.length ? <div className="mt-1"><span className="font-medium">Vocabulary:</span> {q.vocabulary_terms.join("; ")}</div> : null}
                      </div>
                    ))}
                  </div>
                  {importPreview.status === "PREVIEW" ? (
                    <Button onClick={handleConfirmImport} disabled={!importPreview.parsed_questions.length || confirmImport.isPending}>
                      {confirmImport.isPending ? "Importing…" : `Confirm & import ${importPreview.parsed_questions.length} question(s)`}
                    </Button>
                  ) : (
                    <p className="text-sm text-green-700">{importPreview.imported_count} question(s) added to this assessment.</p>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-semibold">
            Imported questions ({importedQuestions?.length ?? 0})
          </h3>
          {!importedQuestions || importedQuestions.length === 0 ? (
            <p className="mt-2 text-sm text-muted-foreground">
              No questions have been confirmed for this assessment yet.
            </p>
          ) : (
            <div className="mt-3 max-h-80 space-y-2 overflow-y-auto">
              {importedQuestions.map((item, index) => (
                <div key={item.id} className="rounded-md border bg-muted/20 p-3 text-sm">
                  <div className="font-medium">{index + 1}. {item.question_detail.text}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {item.question_detail.question_type} · {item.marks_override ?? item.question_detail.marks} mark(s) · {item.question_detail.difficulty}
                  </div>
                  {item.question_detail.options?.length ? (
                    <div className="mt-1 text-xs">Options: {item.question_detail.options.join(" | ")}</div>
                  ) : null}
                  {item.question_detail.vocabulary_terms?.length ? (
                    <div className="mt-1 text-xs text-muted-foreground">
                      Vocabulary: {item.question_detail.vocabulary_terms.join("; ")}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-sm font-semibold">Descriptive answers awaiting grading</h3>
          <p className="mb-2 text-xs text-muted-foreground">
            Objective marks are already auto-calculated. The value below starts with those marks; add the descriptive marks and save the final total.
          </p>
          {descriptiveAssignments.length === 0 ? (
            <p className="text-sm text-muted-foreground">No submitted descriptive answers are awaiting grading. Objective-only submissions are already auto-graded.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="py-2 pr-3 font-medium">Roll no.</th>
                      <th className="py-2 pr-3 font-medium">Name</th>
                      <th className="py-2 pr-3 font-medium">Marks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {descriptiveAssignments.map((assignment) => (
                      <tr key={assignment.id} className="border-b last:border-0">
                        <td className="py-2 pr-3 font-mono">{assignment.student_detail.roll_number}</td>
                        <td className="py-2 pr-3">{assignment.student_detail.full_name}</td>
                        <td className="py-2 pr-3">
                          <Input
                            className="h-8 w-24"
                            type="number"
                            value={marks[assignment.student] ?? assignment.obtained_marks ?? ""}
                            onChange={(e) => setMarks((prev) => ({ ...prev, [assignment.student]: e.target.value }))}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <Button onClick={handleSubmit} disabled={submitMarks.isPending}>
                  {submitMarks.isPending ? "Saving…" : "Save marks"}
                </Button>
                {message ? <span className="text-sm text-green-700">{message}</span> : null}
                {error ? <span className="text-sm text-destructive">{error}</span> : null}
              </div>
            </>
          )}
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-semibold">Student answer sheets</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Submitted answers appear here student-wise. Review these answers, then enter marks above and save.
          </p>
          {!assignments || assignments.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">No students assigned yet.</p>
          ) : (
            <div className="mt-3 space-y-3">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="rounded-md border p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="font-medium">
                      {assignment.student_detail.roll_number} — {assignment.student_detail.full_name}
                    </div>
                    <Badge variant={assignment.status === "SUBMITTED" ? "default" : "secondary"}>
                      {assignment.status}
                    </Badge>
                  </div>
                  {assignment.status !== "PENDING" && Object.keys(assignment.answers ?? {}).length > 0 ? (
                    <div className="mt-3 space-y-2">
                      {Object.entries(assignment.answers ?? {}).map(([questionId, answer]) => {
                        const question = importedQuestions?.find((item) => String(item.question) === questionId);
                        return (
                        <div key={questionId} className="rounded border bg-muted/20 p-2 text-sm">
                          <div className="text-xs font-medium text-muted-foreground">Question #{questionId}{question ? ` — ${question.question_detail.text}` : ""}</div>
                          <div className="mt-1 whitespace-pre-wrap">{String(answer ?? "—")}</div>
                        </div>
                        );
                      })}
                    </div>
                  ) : assignment.status === "PENDING" ? (
                    <p className="mt-2 text-xs text-muted-foreground">Student has not submitted answers yet.</p>
                  ) : (
                    <p className="mt-2 text-xs text-muted-foreground">No answer content was saved for this graded record.</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {results ? (
          <div>
            <h3 className="mb-2 text-sm font-semibold">Results</h3>
            <div className="mb-3 text-xs text-muted-foreground">
              Total {results.summary.total} · Graded {results.summary.graded} · Passed {results.summary.passed} · Failed {results.summary.failed} · Avg {results.summary.average}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Rank</th>
                    <th className="py-2 pr-3 font-medium">Roll no.</th>
                    <th className="py-2 pr-3 font-medium">Name</th>
                    <th className="py-2 pr-3 font-medium">Marks</th>
                    <th className="py-2 pr-3 font-medium">%</th>
                    <th className="py-2 pr-3 font-medium">Grade</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.results.map((r) => (
                    <tr key={r.student} className="border-b last:border-0">
                      <td className="py-2 pr-3">{r.rank ?? "—"}</td>
                      <td className="py-2 pr-3 font-mono">{r.student_detail.roll_number}</td>
                      <td className="py-2 pr-3">{r.student_detail.full_name}</td>
                      <td className="py-2 pr-3">{r.obtained_marks ?? "—"}</td>
                      <td className="py-2 pr-3">{r.percentage ?? "—"}</td>
                      <td className="py-2 pr-3"><Badge variant={r.passed ? "default" : "secondary"}>{r.grade || "—"}</Badge></td>
                      <td className="py-2 pr-3 text-xs">
                        {r.status === "SUBMITTED"
                          ? "Submitted · grading pending"
                          : r.obtained_marks == null
                            ? "Pending assignment"
                            : r.passed
                              ? "Pass"
                              : "Fail"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
    </div>
  );
}
