import { api } from '../client'
import type { components } from '../schema'

type S = components['schemas']
export type CounsellorDash = S['CounsellorDashboard']
export type CaseloadItem = S['CaseloadItem']
export type FollowUp = S['FollowUpOut']
export type CounsellingSession = S['SessionOut']
export type RiskScorePage = S['RiskScorePage']
export type CaseDetail = S['CaseDetailResponse']

export const counsellorApi = {
  dashboard: (signal?: AbortSignal) => api.get<CounsellorDash>('/api/v1/counselling/dashboard', { signal }),
  caseload: (state?: string, signal?: AbortSignal) =>
    api.get<CaseloadItem[]>('/api/v1/counselling/caseload', { query: { state, limit: 100 }, signal }),
  followups: (signal?: AbortSignal) =>
    api.get<FollowUp[]>('/api/v1/counselling/followups', { query: { upcoming_only: true, limit: 50 }, signal }),
  sessions: (signal?: AbortSignal) =>
    api.get<CounsellingSession[]>('/api/v1/counselling/sessions', { query: { limit: 50 }, signal }),
  mlStudents: (tier: string | undefined, signal?: AbortSignal) =>
    api.get<RiskScorePage>('/api/v1/ml/students', { query: { tier, page_size: 50 }, signal }),
  cases: (state?: string, signal?: AbortSignal) =>
    api.get<CaseDetail[]>('/api/v1/cases/', { query: { state, limit: 100 }, signal }),
  /** One enforced workflow step (backend returns { status, case, event }). Counsellors cannot self-assign: an admin does that. */
  advance: (id: string, expectedVersion: number, target: string) =>
    api.post<{ case: CaseDetail }>(`/api/v1/cases/${id}/transition`, { target_state: target, expected_version: expectedVersion }),
  dismiss: (id: string, expectedVersion: number, notes?: string) =>
    api.post<CaseDetail>(`/api/v1/cases/${id}/dismiss`, { expected_version: expectedVersion, notes }),
}
