"use client";

import { useEffect, useMemo, useState } from "react";
import { MessageCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import { useCourses, useSections } from "@/hooks/useAcademics";
import { useStudents } from "@/hooks/useStudents";
import { useTeachers } from "@/hooks/useTeachers";
import { useAuthStore } from "@/store/auth";
import {
  useDailySummary,
  useStudentAttendance,
  useMarkDailyAttendance,
  useWhatsAppAbsenceTemplate,
  useWhatsAppGeneralTemplate,
  useSaveWhatsAppAbsenceTemplate,
  useMarkTeacherAttendance,
  useLeaveTypes,
  useLeaveRequests,
  useCreateLeaveRequest,
  useApproveLeave,
  useRejectLeave,
  type AttendanceStatus,
} from "@/hooks/useAttendance";

const STATUS_OPTIONS: AttendanceStatus[] = ["PRESENT", "ABSENT", "LATE", "EXCUSED"];

const STATUS_LABEL: Record<string, string> = {
  PRESENT: "Present",
  ABSENT: "Absent",
  LATE: "Late",
  EXCUSED: "Excused",
};

const STATUS_COLOR: Record<string, string> = {
  PRESENT: "bg-green-500/15 text-green-700",
  ABSENT: "bg-red-500/15 text-red-700",
  LATE: "bg-amber-500/15 text-amber-700",
  EXCUSED: "bg-blue-500/15 text-blue-700",
};

const ABSENCE_TEMPLATE = "Namaste [Parent/Student Name], [Student Name] aaj institute ([Course Name]) me anupasthit (Absent) rahe hain. Agar koi reason ho to kripya hume suchit karein. - [Institute Name]";
const GENERAL_TEMPLATE = "Dear [Student Name], yeh ek reminder hai aapke batch timing / fee status ke bare me. Sampark karein: [Phone Number]. - [Institute Name].";

interface WhatsAppTarget {
  studentId: number;
  studentName: string;
  contactName: string;
  relation: string;
  phone: string;
  message: string;
}

function makeWhatsAppUrl(phone: string, message: string) {
  let number = phone.replace(/\D/g, "");
  if (number.startsWith("00")) number = number.slice(2);
  if (number.length === 10) number = `91${number}`;
  return `https://wa.me/${number}?text=${encodeURIComponent(message)}`;
}

type Tab = "daily" | "teachers" | "leave";

export default function AttendancePage() {
  const [tab, setTab] = useState<Tab>("daily");

  return (
    <div className="space-y-6">
      <PageHeader title="Attendance" description="Daily + period-wise student attendance, staff attendance and leave." />

      <div className="flex gap-2">
        {(["daily", "teachers", "leave"] as Tab[]).map((t) => (
          <Button
            key={t}
            variant={tab === t ? "default" : "outline"}
            size="sm"
            onClick={() => setTab(t)}
          >
            {t === "daily" ? "Student daily" : t === "teachers" ? "Staff" : "Leave"}
          </Button>
        ))}
      </div>

      {tab === "daily" ? <DailyAttendancePanel /> : null}
      {tab === "teachers" ? <StaffAttendancePanel /> : null}
      {tab === "leave" ? <LeavePanel /> : null}
    </div>
  );
}

// --------------------------------------------------------------------- daily
function DailyAttendancePanel() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [groupSelection, setGroupSelection] = useState("");
  const [roster, setRoster] = useState<Record<number, AttendanceStatus>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const [absenceTemplateBody, setAbsenceTemplateBody] = useState(ABSENCE_TEMPLATE);
  const [generalTemplateBody, setGeneralTemplateBody] = useState(GENERAL_TEMPLATE);
  const [templateMessage, setTemplateMessage] = useState<string | null>(null);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [alertQueue, setAlertQueue] = useState<WhatsAppTarget[]>([]);

  const user = useAuthStore((state) => state.user);
  const { data: sections } = useSections();
  const { data: courses } = useCourses();
  const sectionId = groupSelection.startsWith("section:") ? Number(groupSelection.slice(8)) : undefined;
  const courseId = groupSelection.startsWith("course:") ? Number(groupSelection.slice(7)) : undefined;
  const groupSelected = Boolean(sectionId || courseId);
  const { data: studentPage, isLoading } = useStudents({
    section: sectionId,
    course: courseId,
    status: "ACTIVE",
    pageSize: 200,
  });
  const students = useMemo(() => studentPage?.items ?? [], [studentPage?.items]);
  const { data: savedAttendance } = useStudentAttendance({
    date, section: sectionId, course: courseId, enabled: groupSelected,
  });
  const { data: summary } = useDailySummary(date, sectionId, courseId);
  const markDaily = useMarkDailyAttendance();
  const { data: absenceTemplate } = useWhatsAppAbsenceTemplate();
  const { data: generalTemplate } = useWhatsAppGeneralTemplate();
  const saveTemplate = useSaveWhatsAppAbsenceTemplate();
  const currentSaveKey = `${date}|${groupSelection}`;
  const attendanceSaved = savedKey === currentSaveKey;

  useEffect(() => {
    if (!absenceTemplate?.body) return;
    setAbsenceTemplateBody(absenceTemplate.body);
  }, [absenceTemplate?.body]);

  useEffect(() => {
    if (!generalTemplate?.body) return;
    setGeneralTemplateBody(generalTemplate.body);
  }, [generalTemplate?.body]);

  useEffect(() => {
    if (!groupSelected || !savedAttendance) return;
    const byStudent = new Map(savedAttendance.items.map((row) => [row.student, row]));
    const nextRoster: Record<number, AttendanceStatus> = {};
    const nextRemarks: Record<number, string> = {};
    for (const student of students) {
      const row = byStudent.get(student.id);
      nextRoster[student.id] = row?.status ?? "PRESENT";
      nextRemarks[student.id] = row?.remark ?? "";
    }
    setRoster(nextRoster);
    setRemarks(nextRemarks);
    setSavedKey(students.length > 0 && students.every((student) => byStudent.has(student.id)) ? currentSaveKey : null);
  }, [groupSelected, savedAttendance, students, currentSaveKey]);

  function setAll(status: AttendanceStatus) {
    const next: Record<number, AttendanceStatus> = {};
    students.forEach((s) => (next[s.id] = status));
    setRoster(next);
    setSavedKey(null);
  }

  function attendanceContactTargets(student: (typeof students)[number], sourceTemplate = absenceTemplateBody): WhatsAppTarget[] {
    const contacts = student.whatsapp_contacts?.length
      ? student.whatsapp_contacts
      : student.user.phone
        ? [{ name: student.user.full_name, phone: student.user.phone, relation: "Student", recipient_type: "STUDENT" as const, is_primary: true }]
        : [];
    const courseName = student.course_detail?.name ?? student.section_detail?.school_class ?? "Class/Batch";
    return contacts.map((contact) => {
      const body = sourceTemplate
        .replaceAll("[Parent/Student Name]", contact.name || "Parent/Student")
        .replaceAll("[Student Name]", student.user.full_name)
        .replaceAll("[Course Name]", courseName)
        .replaceAll("[Institute Name]", user?.institution_name ?? "Institute")
        .replaceAll("[Phone Number]", user?.institution_phone ?? "");
      return {
        studentId: student.id,
        studentName: student.user.full_name,
        contactName: contact.name,
        relation: contact.relation,
        phone: contact.phone,
        message: body,
      };
    });
  }

  async function handleSubmit() {
    setError(null);
    setMessage(null);
    if (!groupSelected || students.length === 0) {
      setError("Choose a class/section or course/batch with students first.");
      return;
    }
    try {
      const result = await markDaily.mutateAsync({
        date,
        records: students.map((s) => ({
          student: s.id,
          status: roster[s.id] ?? "PRESENT",
          remark: remarks[s.id] ?? "",
        })),
      });
      setSavedKey(currentSaveKey);
      setMessage(
        `Saved — ${result.created} created, ${result.corrected} corrected, ${result.unchanged} unchanged.`
      );
    } catch (err) {
      setError((err as Error)?.message ?? "Could not save attendance.");
    }
  }

  async function handleSaveTemplate(event: "student.absent" | "student.general", body: string, id?: number) {
    setTemplateError(null);
    setTemplateMessage(null);
    try {
      await saveTemplate.mutateAsync({ id, body, event });
      setTemplateMessage(event === "student.absent" ? "Absence template saved." : "General notice template saved.");
    } catch (err) {
      setTemplateError((err as Error)?.message ?? "Could not save the template.");
    }
  }

  function prepareAbsentAlerts() {
    if (!attendanceSaved) {
      setError("Save attendance before preparing WhatsApp alerts.");
      return;
    }
    const targets = students
      .filter((student) => (roster[student.id] ?? "PRESENT") === "ABSENT")
      .flatMap((student) => attendanceContactTargets(student, absenceTemplateBody));
    setAlertQueue(targets);
    setMessage(targets.length
      ? `${targets.length} WhatsApp alert(s) ready. Open each draft and press Send in WhatsApp.`
      : "No absent students with a saved WhatsApp contact.");
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-wrap items-end gap-3 space-y-0">
          <div className="space-y-1">
            <Label htmlFor="att-date">Date</Label>
            <Input
              id="att-date"
              type="date"
              value={date}
              onChange={(e) => { setDate(e.target.value); setSavedKey(null); setAlertQueue([]); }}
              className="w-40"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="att-section">Class / Course / Batch</Label>
            <select
              id="att-section"
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={groupSelection}
              onChange={(e) => {
                setGroupSelection(e.target.value);
                setRoster({});
                setRemarks({});
                setSavedKey(null);
                setAlertQueue([]);
              }}
            >
              <option value="">— choose class / batch —</option>
              <optgroup label="Classes / Sections">
              {(sections ?? []).map((s) => (
                <option key={`section-${s.id}`} value={`section:${s.id}`}>
                  {s.school_class_detail?.name ?? ""} {s.name}
                </option>
              ))}
              </optgroup>
              {(courses ?? []).length ? (
                <optgroup label="Courses / Batches">
                  {(courses ?? []).map((course) => (
                    <option key={`course-${course.id}`} value={`course:${course.id}`}>
                      {course.code} — {course.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
            </select>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setAll("PRESENT")}>
              Mark all present
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {summary ? (
            <div className="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
              <SummaryPill label="Enrolled" value={summary.enrolled} />
              <SummaryPill label="Marked" value={summary.marked} />
              <SummaryPill label="Unmarked" value={summary.unmarked} />
              <SummaryPill label="Present" value={summary.counts.PRESENT ?? 0} />
              <SummaryPill label="Rate" value={`${summary.attendanceRate}%`} />
            </div>
          ) : null}

          {isLoading ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Loading students…</p>
          ) : !groupSelected ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Choose a class/section or course/batch to load its roster.
            </p>
          ) : students.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No active students found in this class or batch.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Roll no.</th>
                    <th className="py-2 pr-3 font-medium">Name</th>
                    <th className="py-2 pr-3 font-medium">Contact</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Remark</th>
                    <th className="py-2 pr-3 font-medium">WhatsApp</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id} className="border-b last:border-0">
                      <td className="py-2 pr-3 font-mono">{s.roll_number}</td>
                      <td className="py-2 pr-3">{s.user.full_name}</td>
                      <td className="py-2 pr-3 text-xs">{s.whatsapp_contacts?.[0]?.phone ?? s.user.phone ?? "—"}</td>
                      <td className="py-2 pr-3">
                        <div className="flex gap-1">
                          {STATUS_OPTIONS.map((st) => (
                            <Button
                              key={st}
                              type="button"
                              size="sm"
                              variant={(roster[s.id] ?? "PRESENT") === st ? "default" : "outline"}
                              className={`h-7 min-w-8 px-2 text-xs ${STATUS_COLOR[st]}`}
                              title={STATUS_LABEL[st]}
                              onClick={() => {
                                setRoster((prev) => ({ ...prev, [s.id]: st }));
                                setSavedKey(null);
                                setAlertQueue([]);
                              }}
                            >
                              {st === "PRESENT" ? "P" : st === "ABSENT" ? "A" : st === "LATE" ? "L" : "E"}
                            </Button>
                          ))}
                        </div>
                      </td>
                      <td className="py-2 pr-3">
                        <Input
                          className="h-8"
                          placeholder="optional"
                          value={remarks[s.id] ?? ""}
                          onChange={(e) =>
                            { setRemarks((prev) => ({ ...prev, [s.id]: e.target.value })); setSavedKey(null); }
                          }
                        />
                      </td>
                      <td className="py-2 pr-3">
                        <div className="flex gap-1">
                          {attendanceContactTargets(
                            s,
                            (roster[s.id] ?? "PRESENT") === "ABSENT" ? absenceTemplateBody : generalTemplateBody,
                          ).map((contact) => (
                            <a
                              key={`${contact.phone}-${contact.relation}`}
                              href={makeWhatsAppUrl(contact.phone, contact.message)}
                              target="_blank"
                              rel="noreferrer"
                              aria-label={`WhatsApp ${contact.relation} for ${s.user.full_name}`}
                              title={`Open ${contact.relation} WhatsApp draft`}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md border text-green-700 hover:bg-green-50"
                            >
                              <MessageCircle className="h-4 w-4" />
                            </a>
                          ))}
                          {!attendanceContactTargets(s).length ? <span className="text-xs text-muted-foreground">No phone</span> : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {groupSelected && students.length > 0 ? (
            <div className="mt-4 flex items-center gap-3">
              <Button onClick={handleSubmit} disabled={markDaily.isPending}>
                {markDaily.isPending ? "Saving…" : "Save attendance"}
              </Button>
              <Button variant="outline" onClick={prepareAbsentAlerts} disabled={!attendanceSaved}>
                Send Absent Alerts
              </Button>
              {attendanceSaved ? <span className="text-xs text-green-700">Attendance saved for this date and group.</span> : null}
              {message ? <span className="text-sm text-green-700">{message}</span> : null}
              {error ? <span className="text-sm text-destructive">{error}</span> : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Customizable WhatsApp templates</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5 lg:grid-cols-2">
          <div className="space-y-3">
            <h3 className="text-sm font-medium">Absent alert</h3>
            <textarea
              className="min-h-28 w-full rounded-md border bg-background p-3 text-sm"
              value={absenceTemplateBody}
              onChange={(e) => setAbsenceTemplateBody(e.target.value)}
            />
            <Button size="sm" onClick={() => handleSaveTemplate("student.absent", absenceTemplateBody, absenceTemplate?.id)} disabled={saveTemplate.isPending || !absenceTemplateBody.trim()}>
              Save absent template
            </Button>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-medium">Fee / general notice</h3>
            <textarea
              className="min-h-28 w-full rounded-md border bg-background p-3 text-sm"
              value={generalTemplateBody}
              onChange={(e) => setGeneralTemplateBody(e.target.value)}
            />
            <Button size="sm" variant="outline" onClick={() => handleSaveTemplate("student.general", generalTemplateBody, generalTemplate?.id)} disabled={saveTemplate.isPending || !generalTemplateBody.trim()}>
              Save general template
            </Button>
          </div>
          <div className="space-y-3 lg:col-span-2">
          <p className="text-xs text-muted-foreground">
            Placeholders: [Parent/Student Name], [Student Name], [Course Name], [Institute Name], [Phone Number]. Save to reuse this template.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            {saveTemplate.isPending ? <span className="text-sm text-muted-foreground">Saving template…</span> : null}
            {templateMessage ? <span className="text-sm text-green-700">{templateMessage}</span> : null}
            {templateError ? <span className="text-sm text-destructive">{templateError}</span> : null}
          </div>
          </div>
        </CardContent>
      </Card>

      {alertQueue.length ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Absent alert queue ({alertQueue.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">Each link opens a WhatsApp draft. Review it and press Send in WhatsApp; this zero-cost flow does not send messages in the background.</p>
            {alertQueue.map((target, index) => (
              <div key={`${target.studentId}-${target.phone}`} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2 text-sm">
                <span>{target.studentName} → {target.contactName} ({target.relation})</span>
                <a
                  className="inline-flex h-8 items-center gap-2 rounded-md bg-green-600 px-3 text-xs font-medium text-white hover:bg-green-700"
                  href={makeWhatsAppUrl(target.phone, target.message)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <MessageCircle className="h-4 w-4" /> Open WhatsApp {index + 1}
                </a>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function SummaryPill({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border bg-muted/40 px-3 py-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  );
}

// --------------------------------------------------------------------- staff
function StaffAttendancePanel() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [statuses, setStatuses] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: teachers } = useTeachers();
  const mark = useMarkTeacherAttendance();

  async function handleSubmit() {
    setError(null);
    setMessage(null);
    if (!teachers || teachers.length === 0) return;
    try {
      const result = await mark.mutateAsync({
        date,
        records: teachers.map((t) => ({
          teacher: t.id,
          status: statuses[t.id] ?? "PRESENT",
        })),
      });
      setMessage(`Saved — ${result.created} created, ${result.corrected} corrected.`);
    } catch (err) {
      setError((err as Error)?.message ?? "Could not save staff attendance.");
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-wrap items-end gap-3 space-y-0">
        <div className="space-y-1">
          <Label htmlFor="staff-date">Date</Label>
          <Input
            id="staff-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-40"
          />
        </div>
        <Button onClick={handleSubmit} disabled={mark.isPending}>
          {mark.isPending ? "Saving…" : "Save staff attendance"}
        </Button>
      </CardHeader>
      <CardContent>
        {message ? <p className="mb-3 text-sm text-green-700">{message}</p> : null}
        {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
        {!teachers || teachers.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No teachers found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">Employee</th>
                  <th className="py-2 pr-3 font-medium">Name</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((t) => (
                  <tr key={t.id} className="border-b last:border-0">
                    <td className="py-2 pr-3 font-mono">{t.employee_id}</td>
                    <td className="py-2 pr-3">{t.user.full_name}</td>
                    <td className="py-2 pr-3">
                      <select
                        className="h-8 rounded-md border px-2 text-xs"
                        value={statuses[t.id] ?? "PRESENT"}
                        onChange={(e) =>
                          setStatuses((prev) => ({ ...prev, [t.id]: e.target.value }))
                        }
                      >
                        {["PRESENT", "ABSENT", "ON_LEAVE"].map((st) => (
                          <option key={st} value={st}>
                            {st}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------- leave
function LeavePanel() {
  const { data: leaveTypes } = useLeaveTypes();
  const { data: requests } = useLeaveRequests();
  const createLeave = useCreateLeaveRequest();
  const approve = useApproveLeave();
  const reject = useRejectLeave();
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setFormError(null);
    setSuccess(null);
    try {
      await createLeave.mutateAsync({
        leave_type: Number(formData.get("leave_type")),
        start_date: String(formData.get("start_date") ?? ""),
        end_date: String(formData.get("end_date") ?? ""),
        reason: String(formData.get("reason") ?? ""),
      });
      setSuccess("Leave request submitted.");
    } catch (err) {
      setFormError((err as Error)?.message ?? "Could not submit leave request.");
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Apply for leave</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
            onSubmit={(e) => {
              e.preventDefault();
              void handleSubmit(new FormData(e.currentTarget));
            }}
          >
            <div className="space-y-1">
              <Label>Leave type</Label>
              <select name="leave_type" className="h-9 w-full rounded-md border bg-background px-2 text-sm" required>
                {(leaveTypes ?? []).map((lt) => (
                  <option key={lt.id} value={lt.id}>
                    {lt.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Start date</Label>
              <Input name="start_date" type="date" required />
            </div>
            <div className="space-y-1">
              <Label>End date</Label>
              <Input name="end_date" type="date" required />
            </div>
            <div className="space-y-1">
              <Label>Reason</Label>
              <Input name="reason" />
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={createLeave.isPending}>
                {createLeave.isPending ? "Submitting…" : "Submit request"}
              </Button>
            </div>
          </form>
          {formError ? <p className="mt-3 text-sm text-destructive">{formError}</p> : null}
          {success ? <p className="mt-3 text-sm text-green-700">{success}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Leave requests</CardTitle>
        </CardHeader>
        <CardContent>
          {!requests || requests.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No leave requests yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Teacher</th>
                    <th className="py-2 pr-3 font-medium">Type</th>
                    <th className="py-2 pr-3 font-medium">Dates</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((r) => (
                    <tr key={r.id} className="border-b last:border-0">
                      <td className="py-2 pr-3">
                        {r.teacher_detail?.full_name ?? `#${r.teacher}`}
                      </td>
                      <td className="py-2 pr-3">{r.leave_type_detail?.name ?? ""}</td>
                      <td className="py-2 pr-3 font-mono text-xs">
                        {r.start_date} → {r.end_date}
                      </td>
                      <td className="py-2 pr-3">
                        <Badge variant={r.status === "APPROVED" ? "default" : "secondary"}>
                          {r.status}
                        </Badge>
                      </td>
                      <td className="py-2 pr-3">
                        {r.status === "PENDING" ? (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={async () => {
                                try {
                                  await approve.mutateAsync(r.id);
                                } catch (err) {
                                  alert((err as Error)?.message ?? "Approve failed");
                                }
                              }}
                            >
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                const reason = prompt("Rejection reason (optional)") ?? "";
                                try {
                                  await reject.mutateAsync({ id: r.id, reason });
                                } catch (err) {
                                  alert((err as Error)?.message ?? "Reject failed");
                                }
                              }}
                            >
                              Reject
                            </Button>
                          </div>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
