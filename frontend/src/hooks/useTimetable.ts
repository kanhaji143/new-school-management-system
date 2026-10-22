"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export type TimetableStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export interface TimetableItem {
  id: number;
  section: number | null;
  section_detail: { id: number; name: string; school_class: string } | null;
  course: number | null;
  course_detail: { id: number; code: string; name: string } | null;
  academic_year: number;
  academic_year_detail: { id: number; name: string };
  term: number | null;
  version: number;
  status: TimetableStatus;
  entry_count: number;
  published_at: string | null;
}

export interface GridEntry {
  id: number;
  day: number;
  period: number;
  period_name: string;
  period_start: string;
  period_end: string;
  subject: { id: number; name: string; code: string } | null;
  teacher: { id: number; employee_id: string; full_name: string; department: string } | null;
  room: string;
  status: "SCHEDULED" | "CANCELLED" | "SUBSTITUTED";
}

export interface ConflictItem {
  id: number;
  conflictType: string;
  severity: "HARD" | "SOFT";
  description: string;
  entry: number | null;
  clashesWith: number | null;
}

export interface ValidationReport {
  totalEntries: number;
  hardCount: number;
  softCount: number;
  canPublish: boolean;
  conflicts: ConflictItem[];
}

export function useTimetables(params?: { section?: number; status?: string }) {
  return useQuery({
    queryKey: ["timetables", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<TimetableItem>>("/timetables/", {
        params,
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateTimetable() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { section: number; academic_year: number; term?: number | null }) => {
      const { data } = await api.post<ApiItem<TimetableItem>>("/timetables/", payload);
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["timetables"] }),
  });
}

export function useAddTimetableEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      timetable: number;
      day: number;
      period: number;
      subject: number;
      teacher?: number | null;
      room?: string;
    }) => {
      const { data } = await api.post<ApiItem<GridEntry>>("/timetable-entries/", payload);
      return data.data;
    },
    onSuccess: (_data, payload) => {
      queryClient.invalidateQueries({ queryKey: ["timetables"] });
      queryClient.invalidateQueries({ queryKey: ["period-templates"] });
      if (payload?.timetable) {
        queryClient.invalidateQueries({ queryKey: ["timetables", payload.timetable, "grid"] });
      }
    },
  });
}

export function usePeriodTemplates() {
  return useQuery({
    queryKey: ["period-templates"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<{ id: number; name: string; day: number; start_time: string; end_time: string; order_index: number }>>(
        "/period-templates/",
        { params: { pageSize: 200 } }
      );
      return data.data.items;
    },
    staleTime: 60_000,
  });
}

export function useTimetableGrid(timetableId?: number) {
  return useQuery({
    queryKey: ["timetables", timetableId, "grid"],
    enabled: Boolean(timetableId),
    queryFn: async () => {
      const { data } = await api.get<
        ApiItem<{ id: number; version: number; status: TimetableStatus; grid: Record<string, GridEntry[]> }>
      >(`/timetables/${timetableId}/grid/`);
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useValidateTimetable() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (timetableId: number) => {
      const { data } = await api.post<ApiItem<ValidationReport>>(
        `/timetables/${timetableId}/validate/`
      );
      return data.data;
    },
  });
}

export function usePublishTimetable() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (timetableId: number) => {
      const { data } = await api.post<ApiItem<TimetableItem>>(
        `/timetables/${timetableId}/publish/`
      );
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["timetables"] }),
  });
}
