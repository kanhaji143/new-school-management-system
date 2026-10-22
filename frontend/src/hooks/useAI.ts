"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface AIJobItem {
  id: number;
  job_type: string;
  status: "QUEUED" | "RUNNING" | "SUCCESS" | "FAILED";
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error: string;
  created_at: string;
}

export interface GeneratedContentItem {
  id: number;
  content_type: "QUESTION" | "MATERIAL" | "SUMMARY";
  title: string;
  body: string;
  status: "DRAFT" | "PENDING_REVIEW" | "APPROVED" | "REJECTED";
  reviewed_at: string | null;
  review_note: string;
  created_at: string;
}

export function useAIJobs() {
  return useQuery({
    queryKey: ["ai-jobs"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<AIJobItem>>("/ai/jobs/", { params: { pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateAIJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { job_type: string; input: Record<string, unknown> }) => {
      const { data } = await api.post<ApiItem<AIJobItem>>("/ai/jobs/", payload);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-jobs"] });
      qc.invalidateQueries({ queryKey: ["generated-content"] });
    },
  });
}

export function useGeneratedContent(params?: { status?: string }) {
  return useQuery({
    queryKey: ["generated-content", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<GeneratedContentItem>>("/ai/generated-content/", { params: { ...params, pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useReviewContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, decision, note }: { id: number; decision: "approve" | "reject"; note?: string }) => {
      const { data } = await api.post<ApiItem<GeneratedContentItem>>(`/ai/generated-content/${id}/review/`, { decision, note });
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["generated-content"] }),
  });
}
