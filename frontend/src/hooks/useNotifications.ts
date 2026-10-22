"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface NotificationTemplateItem {
  id: number;
  event: string;
  channel: "EMAIL" | "SMS" | "WHATSAPP" | "PUSH";
  subject: string;
  body: string;
  is_active: boolean;
}

export interface NotificationItem {
  id: number;
  recipient: number;
  recipient_detail: { id: number; email: string; full_name: string } | null;
  channel: string;
  subject: string;
  body: string;
  status: "PENDING" | "SENT" | "FAILED" | "CANCELLED";
  attempts: number;
  sent_at: string | null;
  created_at: string;
}

export interface DeliveryLogItem {
  id: number;
  provider: string;
  attempt: number;
  status: string;
  provider_response: string;
  error: string;
  created_at: string;
}

export function useNotificationTemplates() {
  return useQuery({
    queryKey: ["notification-templates"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<NotificationTemplateItem>>("/notification-templates/", { params: { pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 30_000,
  });
}

export function useCreateNotificationTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { event: string; channel: string; subject?: string; body: string; is_active?: boolean }) => {
      const { data } = await api.post<ApiItem<NotificationTemplateItem>>("/notification-templates/", payload);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notification-templates"] }),
  });
}

export function useNotifications(params?: { status?: string }) {
  return useQuery({
    queryKey: ["notifications", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<NotificationItem>>("/notifications/", { params: { ...params, pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useNotificationLogs(id: number) {
  return useQuery({
    queryKey: ["notifications", id, "logs"],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<DeliveryLogItem[]>>(`/notifications/${id}/logs/`);
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useRetryNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ApiItem<NotificationItem>>(`/notifications/${id}/retry/`);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useProviderConfigs() {
  return useQuery({
    queryKey: ["provider-configs"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<{ id: number; channel: string; provider: string; is_active: boolean; priority: number }>>("/provider-configs/", { params: { pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 60_000,
  });
}
