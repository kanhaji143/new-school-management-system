"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface SyllabusItem {
  id: number;
  title: string;
  subject: number;
  subject_detail: { id: number; code: string; name: string } | null;
  section: number | null;
  section_detail: { id: number; name: string } | null;
  academic_year: number;
  academic_year_detail: { id: number; name: string } | null;
  term: number | null;
  chapter_count: number;
}

export interface ChapterItem {
  id: number;
  syllabus: number;
  title: string;
  order_index: number;
  planned_hours: number;
  lesson_plan_count: number;
  completion_status: "PLANNED" | "IN_PROGRESS" | "COMPLETED";
}

export interface LessonPlanItem {
  id: number;
  chapter: number;
  title: string;
  objectives: string;
  content: string;
  duration_minutes: number;
  resources: unknown[];
}

export interface SessionLogItem {
  id: number;
  subject: number;
  subject_detail: { id: number; code: string; name: string } | null;
  section: number | null;
  section_detail: { id: number; name: string } | null;
  chapter: number | null;
  topic: string;
  date: string;
  status: "COMPLETED" | "PARTIAL" | "SKIPPED";
  teacher: number | null;
  teacher_detail: { id: number; employee_id: string; full_name: string } | null;
  notes: string;
}

export function useSyllabi(params?: { subject?: number; section?: number }) {
  return useQuery({
    queryKey: ["syllabi", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<SyllabusItem>>("/syllabi/", {
        params: { ...params, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateSyllabus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { title: string; subject: number; section?: number | null; academic_year: number; term?: number | null }) => {
      const { data } = await api.post<ApiItem<SyllabusItem>>("/syllabi/", payload);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["syllabi"] }),
  });
}

export function useChapters(syllabusId?: number) {
  return useQuery({
    queryKey: ["chapters", syllabusId],
    enabled: Boolean(syllabusId),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<ChapterItem[]>>(
        `/syllabi/${syllabusId}/chapters/`
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useCreateChapter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ syllabusId, title, order_index, planned_hours }: { syllabusId: number; title: string; order_index?: number; planned_hours?: number }) => {
      const { data } = await api.post<ApiItem<ChapterItem>>(
        `/syllabi/${syllabusId}/chapters/`,
        { title, order_index: order_index ?? 1, planned_hours: planned_hours ?? 0 }
      );
      return data.data;
    },
    onSuccess: (_d, v) => qc.invalidateQueries({ queryKey: ["chapters", v.syllabusId] }),
  });
}

export function useCompleteChapter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ chapterId, status, completed_date }: { chapterId: number; status?: string; completed_date?: string }) => {
      const { data } = await api.post<ApiItem<unknown>>(`/chapters/${chapterId}/complete/`, {
        status: status ?? "COMPLETED",
        completed_date,
      });
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chapters"] }),
  });
}

export function useLessonPlans(chapterId?: number) {
  return useQuery({
    queryKey: ["lesson-plans", chapterId],
    enabled: Boolean(chapterId),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<LessonPlanItem[]>>(
        `/chapters/${chapterId}/lesson-plans/`
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useCreateLessonPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ chapterId, title, duration_minutes }: { chapterId: number; title: string; duration_minutes?: number }) => {
      const { data } = await api.post<ApiItem<LessonPlanItem>>(
        `/chapters/${chapterId}/lesson-plans/`,
        { title, duration_minutes: duration_minutes ?? 40 }
      );
      return data.data;
    },
    onSuccess: (_d, v) => qc.invalidateQueries({ queryKey: ["lesson-plans", v.chapterId] }),
  });
}

export function useSessionLogs(params?: { subject?: number; section?: number }) {
  return useQuery({
    queryKey: ["session-logs", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<SessionLogItem>>("/class-session-logs/", {
        params: { ...params, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateSessionLog() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { subject: number; section?: number | null; chapter?: number | null; topic: string; date: string; status?: string; teacher?: number | null; notes?: string }) => {
      const { data } = await api.post<ApiItem<SessionLogItem>>("/class-session-logs/", payload);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["session-logs"] }),
  });
}
