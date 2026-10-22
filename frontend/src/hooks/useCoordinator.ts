"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface CoordinatorTask {
  id: number;
  task_type: string;
  title: string;
  payload: Record<string, unknown>;
  status: "OPEN" | "IN_PROGRESS" | "DONE";
  assignee: number | null;
  created_at: string;
}

export interface CoordinatorDashboard {
  pending: Record<string, number>;
  total_pending: number;
  widgets: { id: number; key: string; label: string; config: Record<string, unknown> }[];
}

export function useCoordinatorDashboard() {
  return useQuery({
    queryKey: ["coordinator-dashboard"],
    queryFn: async () => {
      const { data } = await api.get<ApiItem<CoordinatorDashboard>>("/coordinator/dashboard/");
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useCoordinatorTasks(params?: { status?: string }) {
  return useQuery({
    queryKey: ["coordinator-tasks", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<CoordinatorTask>>("/coordinator-tasks/", {
        params: { ...params, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateCoordinatorTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { task_type: string; title: string }) => {
      const { data } = await api.post<ApiItem<CoordinatorTask>>("/coordinator-tasks/", payload);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["coordinator-tasks"] });
      qc.invalidateQueries({ queryKey: ["coordinator-dashboard"] });
    },
  });
}

export function useCompleteCoordinatorTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ApiItem<CoordinatorTask>>(`/coordinator-tasks/${id}/complete/`);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["coordinator-tasks"] });
      qc.invalidateQueries({ queryKey: ["coordinator-dashboard"] });
    },
  });
}
