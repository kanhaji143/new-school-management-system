"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface AuditLogItem {
  id: number;
  actor_detail: { id: number; email: string; full_name: string } | null;
  action: string;
  model: string;
  object_id: string;
  object_repr: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  created_at: string;
}

export interface SystemSettingItem {
  id: number;
  key: string;
  value: Record<string, unknown>;
  description: string;
}

export function useAuditLogs() {
  return useQuery({
    queryKey: ["audit-logs"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<AuditLogItem>>("/audit-logs/", { params: { pageSize: 50 } });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useSystemSettings() {
  return useQuery({
    queryKey: ["system-settings"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<SystemSettingItem>>("/system-settings/", { params: { pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 30_000,
  });
}

export function useCreateSystemSetting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { key: string; value: Record<string, unknown>; description?: string }) => {
      const { data } = await api.post<ApiItem<SystemSettingItem>>("/system-settings/", payload);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["system-settings"] }),
  });
}
