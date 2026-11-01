import { api } from '../client'
import type { components } from '../schema'

type S = components['schemas']
export type CurrentPulse = S['CurrentPulseResponse']
export type PulseStatus = S['PulseStatusResponse']
export type PulseTrendPoint = S['TrendPoint']
export type RewardBalance = S['BalanceResponse']
export type RewardItem = S['RewardItemResponse']
export type Redemption = S['RedemptionResponse']
export interface SupportRequest {
  id: string
  faculty_id: string
  course_id?: string | null
  category: string
  preferred_slot: string
  student_note: string
  status: string
  faculty_response?: string | null
  created_at: string
}

export interface StudentNotification {
  id: string
  title: string
  body: string
  notification_type: string
  is_read: boolean
  created_at: string
}

export const studentApi = {
  supportRequests: (signal?: AbortSignal) => api.get<SupportRequest[]>('/api/v1/student/support-requests', { signal }),
  createSupportRequest: (data: { category: string; preferred_slot: string; student_note: string; faculty_id?: string; course_id?: string }) =>
    api.post<SupportRequest>('/api/v1/student/support-requests', data),
  academics: (signal?: AbortSignal) => api.get<any>('/api/v1/student/academics', { signal }),
  attendance: (signal?: AbortSignal) => api.get<any>('/api/v1/student/attendance', { signal }),
  courses: (signal?: AbortSignal) => api.get<any[]>('/api/v1/student/courses', { signal }),
  notifications: (signal?: AbortSignal) => api.get<StudentNotification[]>('/api/v1/student/notifications', { signal }),
  markNotificationRead: (id: string) => api.patch<unknown>(`/api/v1/notifications/${id}/read`),
  markAllNotificationsRead: () => api.post<unknown>('/api/v1/notifications/read-all'),
  pulseCurrent: (signal?: AbortSignal) => api.get<CurrentPulse>('/api/v1/wellbeing/pulse/current', { signal }),
  pulseStatus: (signal?: AbortSignal) => api.get<PulseStatus>('/api/v1/wellbeing/pulse/status', { signal }),
  pulseTrends: (signal?: AbortSignal) => api.get<PulseTrendPoint[]>('/api/v1/wellbeing/pulse/trends', { signal }),
  submitPulse: (responses: Record<string, number>, reflection?: string) =>
    api.post<unknown>('/api/v1/wellbeing/pulse/submissions', { responses, reflection: reflection || null }),
}
