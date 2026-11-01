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

export const studentApi = {
  supportRequests: (signal?: AbortSignal) => api.get<SupportRequest[]>('/api/v1/student/support-requests', { signal }),
  pulseCurrent: (signal?: AbortSignal) => api.get<CurrentPulse>('/api/v1/wellbeing/pulse/current', { signal }),
  pulseStatus: (signal?: AbortSignal) => api.get<PulseStatus>('/api/v1/wellbeing/pulse/status', { signal }),
  pulseTrends: (signal?: AbortSignal) => api.get<PulseTrendPoint[]>('/api/v1/wellbeing/pulse/trends', { signal }),
  submitPulse: (responses: Record<string, number>, reflection?: string) =>
    api.post<unknown>('/api/v1/wellbeing/pulse/submissions', { responses, reflection: reflection || null }),
  balance: (signal?: AbortSignal) => api.get<RewardBalance>('/api/v1/rewards/balance', { signal }),
  catalog: (signal?: AbortSignal) => api.get<RewardItem[]>('/api/v1/rewards/catalog', { signal }),
  myRedemptions: (signal?: AbortSignal) => api.get<Redemption[]>('/api/v1/rewards/redemptions/mine', { signal }),
  redeem: (itemId: string, idempotencyKey: string) =>
    api.post<Redemption>('/api/v1/rewards/redemptions', { item_id: itemId }, { headers: { 'X-Idempotency-Key': idempotencyKey } }),
}
