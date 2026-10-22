"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface StudentProfile {
  id: number;
  roll_number: string;
  admission_number: string;
  admission_date: string | null;
  user: { id: number; email: string; full_name: string; phone: string | null };
  whatsapp_contacts: {
    name: string;
    phone: string;
    relation: string;
    recipient_type: "PARENT" | "STUDENT";
    is_primary: boolean;
  }[];
  date_of_birth: string | null;
  gender: string;
  section: number | null;
  section_detail: { id: number; name: string; school_class: string } | null;
  course: number | null;
  course_detail: { id: number; code: string; name: string } | null;
  status: "ACTIVE" | "GRADUATED" | "TRANSFERRED" | "SUSPENDED" | "DROPPED";
}

export interface CreateStudentPayload {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  roll_number: string;
  admission_number: string;
  section?: number | null;
  status?: string;
}

export function useStudents(params?: { page?: number; pageSize?: number; search?: string; status?: string; section?: number; course?: number }) {
  return useQuery({
    queryKey: ["students", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<StudentProfile>>("/students/", { params });
      // response body is the `{ success, data }` envelope �?" unwrap it
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useStudentCounts() {
  return useQuery({
    queryKey: ["students", "counts"],
    queryFn: async () => {
      const [students, teachers, guardians] = await Promise.all([
        api.get<ApiList<StudentProfile>>("/students/"),
        api.get<ApiList<TeacherListing>>("/teachers/"),
        api.get<ApiList<unknown>>("/guardians/"),
      ]);
      return {
        students: students.data.data.total,
        teachers: teachers.data.data.total,
        guardians: guardians.data.data.total,
      };
    },
    staleTime: 30_000,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateStudentPayload) => {
      const { data } = await api.post<ApiItem<StudentProfile>>(
        "/students/", payload
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["students"] }),
  });
}

export function useChangeStudentStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const { data } = await api.patch<StudentProfile>(`/students/${id}/`, { status });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["students"] }),
  });
}

interface TeacherListing {
  id: number;
}
