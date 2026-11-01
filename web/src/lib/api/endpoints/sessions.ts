import { api } from '../client'

export interface CounsellingSession {
  id: string
  case_id?: string | null
  student_id: string
  student_name?: string
  counsellor_id: string
  counsellor_name?: string
  scheduled_at: string
  duration_minutes: number
  location?: string | null
  mode: string
  status: string
  notes?: string | null
  created_at: string
}

export const sessionsApi = {
  list: (signal?: AbortSignal) =>
    api.get<CounsellingSession[]>('/api/v1/counselling/sessions', { signal }),

  get: (id: string, signal?: AbortSignal) =>
    api.get<CounsellingSession>(`/api/v1/counselling/sessions/${id}`, { signal }),

  create: (data: {
    student_id: string
    scheduled_at: string
    case_id?: string
    duration_minutes?: number
    mode?: string
    location?: string
    notes?: string
  }) => api.post<CounsellingSession>('/api/v1/counselling/sessions', data),

  reschedule: (id: string, data: { scheduled_at: string; reason?: string }) =>
    api.patch<CounsellingSession>(`/api/v1/counselling/sessions/${id}`, data),

  complete: (id: string, data?: { notes?: string }) =>
    api.post<CounsellingSession>(`/api/v1/counselling/sessions/${id}/complete`, data),

  cancel: (id: string, data?: { reason?: string }) =>
    api.post<CounsellingSession>(`/api/v1/counselling/sessions/${id}/cancel`, data),

  noShow: (id: string) =>
    api.post<CounsellingSession>(`/api/v1/counselling/sessions/${id}/no-show`),
}

