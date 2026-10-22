"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Paginated } from "@/types";

/** Backend list responses use the `{ success, data: { items, ... } }` envelope. */
export interface ApiList<T> {
  success: boolean;
  data: Paginated<T>;
}

/** Backend detail responses use the `{ success, data }` envelope. */
export interface ApiItem<T> {
  success: boolean;
  data: T;
}

export interface AcademicYearItem {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  term_count: number;
}

export interface TermItem {
  id: number;
  academic_year: number;
  name: string;
  term_type: "TERM" | "SEMESTER";
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface GradeLevelItem {
  id: number;
  name: string;
  level_type: "SCHOOL" | "COLLEGE";
  order_index: number;
}

export interface SchoolClassItem {
  id: number;
  name: string;
  capacity: number;
  grade_level: number;
  grade_level_detail: GradeLevelItem;
  section_count: number;
}

export interface SectionItem {
  id: number;
  name: string;
  school_class: number;
  school_class_detail: SchoolClassItem;
  student_count: number;
}

export interface SubjectItem {
  id: number;
  code: string;
  name: string;
  subject_type: "THEORY" | "PRACTICAL" | "ELECTIVE";
}

export interface CourseItem {
  id: number;
  code: string;
  name: string;
}

export async function listItems<T>(url: string, params?: Record<string, unknown>): Promise<T[]> {  const { data } = await api.get<ApiList<T>>(url, { params });
  return data.data.items;
}

export function useAcademicYears() {
  return useQuery({
    queryKey: ["academic-years"],
    queryFn: () => listItems<AcademicYearItem>("/academic-years/", { pageSize: 200 }),
    staleTime: 60_000,
  });
}

export function useCurrentAcademicYear() {
  return useQuery({
    queryKey: ["academic-years", "current"],
    queryFn: async () => {
      const { data } = await api.get<ApiItem<AcademicYearItem | null>>(
        "/academic-years/current/"
      );
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useTerms(academicYear?: number) {
  return useQuery({
    queryKey: ["terms", academicYear],
    enabled: Boolean(academicYear),
    queryFn: () => listItems<TermItem>("/terms/", { academic_year: academicYear, pageSize: 100 }),
    staleTime: 60_000,
  });
}

export function useSchoolClasses() {
  return useQuery({
    queryKey: ["classes"],
    queryFn: () => listItems<SchoolClassItem>("/classes/", { pageSize: 200 }),
    staleTime: 60_000,
  });
}

export function useSections(schoolClass?: number) {
  return useQuery({
    queryKey: ["sections", schoolClass],
    queryFn: () =>
      listItems<SectionItem>("/sections/", {
        school_class: schoolClass,
        pageSize: 200,
      }),
    staleTime: 60_000,
  });
}

export function useSubjects() {
  return useQuery({
    queryKey: ["subjects"],
    queryFn: () => listItems<SubjectItem>("/subjects/", { pageSize: 200 }),
    staleTime: 60_000,
  });
}

export function useCourses() {
  return useQuery({
    queryKey: ["courses"],
    queryFn: () => listItems<CourseItem>("/courses/", { pageSize: 200 }),
    staleTime: 60_000,
  });
}
