"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export type AttendanceStatus = "PRESENT" | "ABSENT" | "LATE" | "EXCUSED";

export interface StudentAttendanceItem {
  id: number;
  student: number;
  student_detail: {
    id: number;
    roll_number: string;
    full_name: string;
    email: string;
    section: number | null;
    phone?: string | null;
    whatsapp_contacts?: {
      name: string;
      phone: string;
      relation: string;
      recipient_type: "PARENT" | "STUDENT";
      is_primary: boolean;
    }[];
  } | null;
  date: string;
  status: AttendanceStatus;
  status_display: string;
  remark: string;
  marked_by_detail: { id: number; email: string; full_name: string; phone: string | null } | null;
}

export interface DailySummary {
  date: string;
  section: number | null;
  enrolled: number;
  marked: number;
  unmarked: number;
  counts: Record<string, number>;
  attendanceRate: number;
}

export interface DailyAttendanceBulkPayload {
  date: string;
  records: { student: number; status: AttendanceStatus; remark?: string }[];
}

export function useStudentAttendance(params?: {
  date?: string;
  student?: number;
  status?: string;
  section?: number;
  course?: number;
  page?: number;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ["student-attendance", params],
    enabled: params?.enabled ?? true,
    queryFn: async () => {
      const { data } = await api.get<ApiList<StudentAttendanceItem>>(
        "/student-attendance/",
        { params: {
          date: params?.date,
          student: params?.student,
          status: params?.status,
          "student__section": params?.section,
          "student__course": params?.course,
          page: params?.page,
          pageSize: 200,
        } }
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useDailySummary(date?: string, section?: number, course?: number) {
  return useQuery({
    queryKey: ["student-attendance", "summary", date, section, course],
    enabled: Boolean(date && (section || course)),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<DailySummary>>(
        "/student-attendance/summary/",
        { params: { date, section: section ?? undefined, course: course ?? undefined } }
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useMyAttendanceSummary(date?: string) {
  return useQuery({
    queryKey: ["student-attendance", "mine-summary", date],
    enabled: Boolean(date),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<DailySummary>>("/student-attendance/summary/", { params: { date } });
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useMyAttendanceRecords() {
  return useQuery({
    queryKey: ["student-attendance", "mine"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<StudentAttendanceItem>>("/student-attendance/mine/", { params: { pageSize: 10 } });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export interface WhatsAppTemplateItem {
  id: number;
  event: string;
  channel: string;
  subject: string;
  body: string;
  is_active: boolean;
}

export function useWhatsAppAbsenceTemplate() {
  return useQuery({
    queryKey: ["notification-templates", "student.absent", "WHATSAPP"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<WhatsAppTemplateItem>>("/notification-templates/", {
        params: { event: "student.absent", channel: "WHATSAPP", pageSize: 20 },
      });
      return data.data.items[0] ?? null;
    },
    staleTime: 30_000,
  });
}

export function useWhatsAppGeneralTemplate() {
  return useQuery({
    queryKey: ["notification-templates", "student.general", "WHATSAPP"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<WhatsAppTemplateItem>>("/notification-templates/", {
        params: { event: "student.general", channel: "WHATSAPP", pageSize: 20 },
      });
      return data.data.items[0] ?? null;
    },
    staleTime: 30_000,
  });
}

export function useSaveWhatsAppAbsenceTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body, event = "student.absent" }: { id?: number; body: string; event?: string }) => {
      if (id) {
        const { data } = await api.patch<WhatsAppTemplateItem>(`/notification-templates/${id}/`, { body, is_active: true });
        return data;
      }
      const { data } = await api.post<ApiItem<WhatsAppTemplateItem>>("/notification-templates/", {
        event, channel: "WHATSAPP", subject: event === "student.absent" ? "Absence alert" : "General notice", body, is_active: true,
      });
      return data.data;
    },
    onSuccess: (_data, variables) => qc.invalidateQueries({
      queryKey: ["notification-templates", variables.event ?? "student.absent", "WHATSAPP"],
    }),
  });
}

export function useMarkDailyAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DailyAttendanceBulkPayload) => {
      const { data } = await api.post<
        ApiItem<{ created: number; corrected: number; unchanged: number }>
      >("/student-attendance/bulk/", payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-attendance"] });
    },
  });
}

export interface PeriodAttendanceItem {
  id: number;
  student: number;
  student_detail: StudentAttendanceItem["student_detail"];
  entry: number;
  date: string;
  status: AttendanceStatus;
  status_display: string;
}

export function useMarkPeriodAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      date: string;
      entry: number;
      records: { student: number; status: AttendanceStatus }[];
    }) => {
      const { data } = await api.post<
        ApiItem<{ created: number; corrected: number; unchanged: number }>
      >("/period-attendance/bulk/", payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["period-attendance"] });
    },
  });
}

export interface TeacherAttendanceItem {
  id: number;
  teacher: number;
  teacher_detail: { id: number; employee_id: string; full_name: string; department: string } | null;
  date: string;
  status: string;
  status_display: string;
  check_in: string | null;
  check_out: string | null;
}

export function useTeacherAttendance(params?: { date?: string; teacher?: number; status?: string }) {
  return useQuery({
    queryKey: ["teacher-attendance", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<TeacherAttendanceItem>>(
        "/teacher-attendance/",
        { params: { ...params, pageSize: 200 } }
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useMarkTeacherAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      date: string;
      records: { teacher: number; status: string; check_in?: string | null; check_out?: string | null }[];
    }) => {
      const { data } = await api.post<
        ApiItem<{ created: number; corrected: number; unchanged: number }>
      >("/teacher-attendance/bulk/", payload);
      return data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-attendance"] });
    },
  });
}

export interface LeaveTypeItem {
  id: number;
  name: string;
  paid: boolean;
  max_days: number;
}

export interface LeaveRequestItem {
  id: number;
  teacher: number;
  teacher_detail: { id: number; employee_id: string; full_name: string; department: string } | null;
  leave_type: number;
  leave_type_detail: LeaveTypeItem | null;
  start_date: string;
  end_date: string;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
  approved_by_detail: { id: number; email: string; full_name: string; phone: string | null } | null;
  approved_at: string | null;
}

export function useLeaveTypes() {
  return useQuery({
    queryKey: ["leave-types"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<LeaveTypeItem>>("/leave-types/", {
        params: { pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 60_000,
  });
}

export function useLeaveRequests(params?: { status?: string; teacher?: number }) {
  return useQuery({
    queryKey: ["leave-requests", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<LeaveRequestItem>>("/leave-requests/", {
        params: { ...params, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      leave_type: number;
      start_date: string;
      end_date: string;
      reason?: string;
      teacher?: number;
    }) => {
      const { data } = await api.post<ApiItem<LeaveRequestItem>>("/leave-requests/", payload);
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] }),
  });
}

export function useApproveLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ApiItem<LeaveRequestItem>>(
        `/leave-requests/${id}/approve/`
      );
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] }),
  });
}

export function useRejectLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: number; reason?: string }) => {
      const { data } = await api.post<ApiItem<LeaveRequestItem>>(
        `/leave-requests/${id}/reject/`,
        { reason }
      );
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] }),
  });
}
