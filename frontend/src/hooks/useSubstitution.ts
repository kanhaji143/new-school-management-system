"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export type SubstitutionStatus =
  | "OPEN"
  | "PROPOSED"
  | "APPROVED"
  | "COMPLETED"
  | "UNRESOLVED"
  | "CANCELLED";

export interface SubstitutionRequestItem {
  id: number;
  absent_teacher: number;
  absent_teacher_detail: { id: number; employee_id: string; full_name: string; department: string } | null;
  entry: number;
  entry_detail: {
    id: number;
    day: number;
    period: number;
    period_name: string | null;
    subject: { id: number; name: string | null; code: string | null } | null;
    teacher: { id: number; full_name: string | null } | null;
    room: string;
    timetable: number;
  } | null;
  date: string;
  reason: string;
  status: SubstitutionStatus;
  recommendation_count: number;
  assignment: SubstituteAssignmentItem | null;
  created_at: string;
}

export interface SubstituteRecommendationItem {
  id: number;
  teacher: number;
  teacher_detail: { id: number; employee_id: string; full_name: string; department: string } | null;
  score: number;
  reasons: Record<string, number>;
  rank: number;
}

export interface SubstituteAssignmentItem {
  id: number;
  substitute_teacher: number;
  substitute_teacher_detail: { id: number; employee_id: string; full_name: string; department: string } | null;
  status: "PROPOSED" | "APPROVED" | "REJECTED" | "COMPLETED";
  approved_at: string | null;
  handover: HandoverMaterialItem | null;
  outcome: ClassOutcomeItem | null;
}

export interface HandoverMaterialItem {
  id: number;
  notes: string;
  attachments: { id: number; file: string; filename: string }[];
}

export interface ClassOutcomeItem {
  id: number;
  status: "COMPLETED" | "PARTIAL" | "SKIPPED";
  notes: string;
}

export function useSubstitutionRequests(params?: { status?: string; date?: string }) {
  return useQuery({
    queryKey: ["substitution-requests", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<SubstitutionRequestItem>>(
        "/substitution-requests/",
        { params: { ...params, pageSize: 200 } }
      );
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useSubstitutionRequest(id?: number) {
  return useQuery({
    queryKey: ["substitution-requests", id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<SubstitutionRequestItem>>(
        `/substitution-requests/${id}/`
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useRecommendations(requestId: number) {
  return useQuery({
    queryKey: ["substitution-requests", requestId, "recommendations"],
    enabled: Boolean(requestId),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<SubstituteRecommendationItem[]>>(
        `/substitution-requests/${requestId}/recommendations/`
      );
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useGenerateRecommendations() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, limit, strict_subject }: { id: number; limit?: number; strict_subject?: boolean }) => {
      const { data } = await api.post<ApiItem<SubstituteRecommendationItem[]>>(
        `/substitution-requests/${id}/recommend/`,
        { limit, strict_subject }
      );
      return data.data;
    },
    onSuccess: (_d, v) => {
      queryClient.invalidateQueries({ queryKey: ["substitution-requests", v.id, "recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["substitution-requests", v.id] });
      queryClient.invalidateQueries({ queryKey: ["substitution-requests"] });
    },
  });
}

export function useAssignSubstitute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, substitute_teacher, recommendation }: { id: number; substitute_teacher?: number; recommendation?: number }) => {
      const { data } = await api.post<ApiItem<SubstituteAssignmentItem>>(
        `/substitution-requests/${id}/assign/`,
        { substitute_teacher, recommendation }
      );
      return data.data;
    },
    onSuccess: (_d, v) => {
      queryClient.invalidateQueries({ queryKey: ["substitution-requests", v.id] });
      queryClient.invalidateQueries({ queryKey: ["substitution-requests"] });
    },
  });
}

export function useHandover() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes, file }: { id: number; notes?: string; file?: File | null }) => {
      const form = new FormData();
      if (notes) form.append("notes", notes);
      if (file) form.append("file", file);
      const { data } = await api.post<ApiItem<HandoverMaterialItem>>(
        `/substitution-requests/${id}/handover/`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data.data;
    },
    onSuccess: (_d, v) => {
      queryClient.invalidateQueries({ queryKey: ["substitution-requests", v.id] });
    },
  });
}

export function useRecordOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status, notes }: { id: number; status: string; notes?: string }) => {
      const { data } = await api.post<ApiItem<ClassOutcomeItem>>(
        `/substitution-requests/${id}/outcome/`,
        { status, notes }
      );
      return data.data;
    },
    onSuccess: (_d, v) => {
      queryClient.invalidateQueries({ queryKey: ["substitution-requests", v.id] });
      queryClient.invalidateQueries({ queryKey: ["substitution-requests"] });
    },
  });
}

export function useCancelSubstitution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ApiItem<unknown>>(`/substitution-requests/${id}/cancel/`);
      return data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["substitution-requests"] }),
  });
}
