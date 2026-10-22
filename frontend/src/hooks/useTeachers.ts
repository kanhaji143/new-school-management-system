"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { listItems } from "@/hooks/useAcademics";

export interface TeacherProfile {
  id: number;
  employee_id: string;
  department: string;
  qualification: string;
  max_periods_per_week: number;
  status: "ACTIVE" | "ON_LEAVE" | "RESIGNED";
  user: { id: number; email: string; full_name: string; phone: string | null };
  class_subject_count: number;
}

export function useTeachers(params?: { search?: string; status?: string }) {
  return useQuery({
    queryKey: ["teachers", params],
    queryFn: () => listItems<TeacherProfile>("/teachers/", params),
    staleTime: 15_000,
  });
}

export function useTeachersSnapshot() {
  return useQuery({
    queryKey: ["teachers", "snapshot"],
    queryFn: async () => {
      const { data } = await api.get<{ data: { total: number } }>("/teachers/");
      return data.data.total;
    },
    staleTime: 30_000,
  });
}
