import { api } from '../client'
import type { components } from '../schema'

type S = components['schemas']
export type FacultyCase = S['CaseDetailResponse']
export interface FacultyDashboard {
  metrics: { active_courses: number; active_sections: number; total_students_monitored: number; unreviewed_signals: number }
  sections: { id: string; section_code: string; name: string; course_title: string; enrollment_count: number }[]
}
export interface FacultySection { id: string; section_code: string; name: string; course_title: string }
export interface SectionStudent {
  id: string
  student_uid: string
  full_name: string
  department?: string | null
  cohort_code?: string | null
  attendance_rate?: number | null
  quiz_score_avg?: number | null
  enrollment_status?: string | null
}

export const facultyApi = {
  dashboard: (signal?: AbortSignal) => api.get<FacultyDashboard>('/api/v1/faculty/dashboard', { signal }),
  cases: (signal?: AbortSignal) => api.get<FacultyCase[]>('/api/v1/faculty/cases', { signal }),
  sections: (signal?: AbortSignal) => api.get<FacultySection[]>('/api/v1/faculty/sections', { signal }),
  sectionStudents: (id: string, signal?: AbortSignal) =>
    api.get<SectionStudent[]>(`/api/v1/faculty/sections/${id}/students`, { signal }),
}
