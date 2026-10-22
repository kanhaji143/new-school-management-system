/** Shared TypeScript types mirroring the backend API contracts. */

export type InstitutionType = "SCHOOL" | "COLLEGE";

export interface Institution {
  id: string;
  name: string;
  slug: string;
  code: string;
  type: InstitutionType;
  email?: string;
  phone?: string;
  is_active: boolean;
}

export type RoleName =
  | "SUPER_ADMIN"
  | "SCHOOL_ADMIN"
  | "COORDINATOR"
  | "TEACHER"
  | "ACCOUNTANT"
  | "PARENT"
  | "STUDENT";

export interface AuthUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  institution: string | null;
  roles: RoleName[];
  is_active: boolean;
}

export interface AcademicYear {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface Term {
  id: string;
  academic_year: string;
  name: string;
  term_type: "TERM" | "SEMESTER";
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface Student {
  id: string;
  roll_number: string;
  admission_number: string;
  user: { id: string; full_name: string; email: string };
  section?: string | null;
  status: "ACTIVE" | "GRADUATED" | "TRANSFERRED" | "SUSPENDED" | "DROPPED";
}

export interface Teacher {
  id: string;
  employee_id: string;
  department: string;
  max_periods_per_week: number;
  status: "ACTIVE" | "ON_LEAVE" | "RESIGNED";
  user: { id: string; full_name: string; email: string };
}

export interface TimetableEntry {
  id: string;
  day: number;
  period: { id: string; name: string; start_time: string; end_time: string };
  subject: { id: string; name: string };
  teacher?: { id: string; user: { full_name: string } } | null;
  room: string;
  status: "SCHEDULED" | "CANCELLED" | "SUBSTITUTED";
}

export type SubstitutionStatus =
  | "OPEN"
  | "PROPOSED"
  | "APPROVED"
  | "COMPLETED"
  | "UNRESOLVED"
  | "CANCELLED";

export interface SubstitutionRequest {
  id: string;
  absent_teacher: string;
  entry: string;
  date: string;
  reason: string;
  status: SubstitutionStatus;
}

export interface SubstituteRecommendation {
  id: string;
  teacher: string;
  score: number;
  rank: number;
  reasons: Record<string, number>;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface ApiSuccess<T> {
  success: true;
  message?: string;
  data: T;
}

export interface ApiError {
  success: false;
  message: string;
  errors: { fieldErrors: Record<string, string[]>; formErrors: string[] };
}
