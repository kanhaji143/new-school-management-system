"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ApiItem, ApiList } from "@/hooks/useAcademics";

export interface AssessmentItem {
  id: number;
  title: string;
  assessment_type: "QUIZ" | "TEST" | "EXAM" | "ASSIGNMENT";
  subject: number | null;
  subject_detail: { id: number; code: string; name: string } | null;
  section: number | null;
  section_detail: { id: number; name: string } | null;
  academic_year: number;
  date: string;
  total_marks: number;
  pass_marks: number;
  status: "DRAFT" | "SCHEDULED" | "COMPLETED";
  question_count: number;
  marks_entered: number;
}

export interface ResultRow {
  student: number;
  student_detail: { id: number; roll_number: string; full_name: string };
  obtained_marks: string | null;
  total_marks: number;
  percentage: number | null;
  grade: string;
  passed: boolean;
  status: string;
  remarks: string;
  rank: number | null;
}

export interface ResultsPayload {
  assessment: { id: number; title: string; total_marks: number; pass_marks: number };
  results: ResultRow[];
  summary: { total: number; graded: number; passed: number; failed: number; average: number };
}

export interface StudentAssignedAssessment {
  id: number;
  assessment: number;
  assessment_detail: {
    id: number;
    title: string;
    assessment_type: string;
    date: string;
    subject_detail: { code: string; name: string } | null;
    total_marks: number;
    pass_marks: number;
  };
  obtained_marks: string | null;
  grade: string;
  status: string;
  remarks: string;
  answers: Record<string, unknown>;
  questions: {
    id: number;
    question_type: "MCQ" | "TRUE_FALSE" | "SHORT" | "LONG";
    text: string;
    marks: number;
    options: string[];
    vocabulary_terms: string[];
  }[];
}

export interface ParsedQuestionItem {
  question_type: string;
  text: string;
  marks: number;
  options: string[];
  correct_answer: string;
  difficulty: string;
  vocabulary_terms: string[];
}

export interface QuestionImportItem {
  id: number;
  assessment: number;
  original_file_name: string;
  pasted_text: string;
  extraction_warning: string;
  parsed_questions: ParsedQuestionItem[];
  status: "PREVIEW" | "IMPORTED";
  imported_count: number;
}

export function useAssessments(params?: { subject?: number; section?: number; status?: string }) {
  return useQuery({
    queryKey: ["assessments", params],
    queryFn: async () => {
      const { data } = await api.get<ApiList<AssessmentItem>>("/assessments/", {
        params: { ...params, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useCreateAssessment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      assessment_type?: string;
      subject?: number | null;
      section?: number | null;
      academic_year: number;
      date: string;
      total_marks?: number;
      pass_marks?: number;
    }) => {
      const { data } = await api.post<ApiItem<AssessmentItem>>("/assessments/", payload);
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assessments"] }),
  });
}

export function useAssessmentResults(id?: number) {
  return useQuery({
    queryKey: ["assessments", id, "results"],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<ApiItem<ResultsPayload>>(`/assessments/${id}/results/`);
      return data.data;
    },
    staleTime: 15_000,
  });
}

export interface AssessmentQuestionItem {
  id: number;
  assessment: number;
  question: number;
  marks_override: number | null;
  question_detail: {
    id: number;
    question_type: string;
    text: string;
    marks: number;
    options: string[];
    correct_answer: string;
    difficulty: string;
    vocabulary_terms: string[];
  };
}

export function useAssessmentQuestions(assessmentId?: number) {
  return useQuery({
    queryKey: ["assessment-questions", assessmentId],
    enabled: Boolean(assessmentId),
    queryFn: async () => {
      const { data } = await api.get<ApiList<AssessmentQuestionItem>>("/assessment-questions/", {
        params: { assessment: assessmentId, pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 15_000,
  });
}

export function useSubmitMarks() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, records }: { id: number; records: { student: number; obtained_marks: string; status?: string; remarks?: string }[] }) => {
      const { data } = await api.post<ApiItem<{ created: number; corrected: number; total: number }>>(
        `/assessments/${id}/marks/`,
        { records }
      );
      return data.data;
    },
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ["assessments", v.id, "results"] });
      qc.invalidateQueries({ queryKey: ["assessments"] });
    },
  });
}

export function useAssessmentAssignments(assessmentId: number) {
  return useQuery({
    queryKey: ["student-assessments", assessmentId],
    enabled: Boolean(assessmentId),
    queryFn: async () => {
      const { data } = await api.get<ApiList<{
        id: number;
        student: number;
        student_detail: { id: number; roll_number: string; full_name: string };
        obtained_marks: string | null;
        status: string;
        remarks: string;
        answers: Record<string, unknown>;
        questions: {
          id: number;
          question_type: "MCQ" | "TRUE_FALSE" | "SHORT" | "LONG";
          text: string;
          marks: number;
          options: string[];
          vocabulary_terms: string[];
        }[];
      }>>("/student-assessments/", { params: { assessment: assessmentId, pageSize: 200 } });
      return data.data.items;
    },
    staleTime: 10_000,
  });
}

export function useSubmitStudentAnswers() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ assignmentId, answers }: { assignmentId: number; answers: Record<string, string> }) => {
      const { data } = await api.post<ApiItem<unknown>>(
        `/student-assessments/${assignmentId}/submit/`, { answers }
      );
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["student-assessments", "mine"] }),
  });
}

export function useMyAssignedAssessments() {
  return useQuery({
    queryKey: ["student-assessments", "mine"],
    queryFn: async () => {
      const { data } = await api.get<ApiItem<StudentAssignedAssessment[]>>("/student-assessments/mine/");
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useAssignStudents() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ assessmentId, students }: { assessmentId: number; students: number[] }) => {
      const { data } = await api.post<ApiItem<{ created: number; already_assigned: number; total: number }>>(
        `/assessments/${assessmentId}/assign/`, { students }
      );
      return data.data;
    },
    onSuccess: (_result, variables) => {
      qc.invalidateQueries({ queryKey: ["student-assessments", variables.assessmentId] });
      qc.invalidateQueries({ queryKey: ["assessments"] });
    },
  });
}

export function usePreviewQuestionImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ assessmentId, text, file }: { assessmentId: number; text?: string; file?: File | null }) => {
      const form = new FormData();
      if (text) form.append("text", text);
      if (file) form.append("file", file);
      const { data } = await api.post<ApiItem<QuestionImportItem>>(
        `/assessments/${assessmentId}/question-imports/preview/`, form
      );
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assessments"] }),
  });
}

export function useRefreshQuestionImport() {
  return useMutation({
    mutationFn: async ({ id, text, file }: { id: number; text?: string; file?: File | null }) => {
      const form = new FormData();
      if (text) form.append("text", text);
      if (file) form.append("file", file);
      const { data } = await api.post<ApiItem<QuestionImportItem>>(
        `/question-imports/${id}/refresh/`, form
      );
      return data.data;
    },
  });
}

export function useConfirmQuestionImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ApiItem<QuestionImportItem>>(
        `/question-imports/${id}/confirm/`
      );
      return data.data;
    },
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      qc.invalidateQueries({ queryKey: ["question-imports", id] });
    },
  });
}

export function useGradeScales() {
  return useQuery({
    queryKey: ["grade-scales"],
    queryFn: async () => {
      const { data } = await api.get<ApiList<{ id: number; grade: string; min_mark: number; max_mark: number }>>("/grade-scales/", {
        params: { pageSize: 200 },
      });
      return data.data.items;
    },
    staleTime: 60_000,
  });
}
