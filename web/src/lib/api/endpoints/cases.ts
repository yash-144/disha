import { api } from '../client'

export interface CaseSummary {
  id: string
  student_id: string
  student_ref?: string
  student_name?: string
  campus_id: string
  state: string
  priority: string
  owner_id?: string | null
  owner_name?: string | null
  source_kind?: string
  summary?: string
  due_date?: string | null
  outcome?: string | null
  is_overdue?: boolean
  version: number
  created_at: string
  updated_at: string
}

export interface CaseDetail extends CaseSummary {
  risk_score?: number | null
  department?: string | null
  notes?: CaseNote[]
  interventions?: CaseIntervention[]
  followups?: CaseFollowup[]
}

export interface CaseNote {
  id: string
  case_id: string
  author_id: string
  author_name?: string
  note_type: string
  content: string
  is_confidential?: boolean
  created_at: string
}

export interface CaseIntervention {
  id: string
  case_id: string
  catalogue_id?: string | null
  title: string
  category: string
  status: string
  assigned_to?: string | null
  target_date?: string | null
  notes?: string | null
  created_at: string
}

export interface CaseFollowup {
  id: string
  case_id: string
  title: string
  scheduled_at: string
  status: string
  completed_at?: string | null
  notes?: string | null
}

export interface CaseEvent {
  id: string
  case_id: string
  from_state?: string | null
  to_state: string
  actor_id: string
  reason?: string | null
  metadata_snapshot?: Record<string, unknown>
  created_at: string
}

export interface AiReviewBrief {
  summary: string
  key_risk_factors: string[]
  recommended_actions: string[]
  academic_context?: string
  urgency_level: string
}

export const casesApi = {
  list: (params?: { state?: string; priority?: string; owner_id?: string }, signal?: AbortSignal) =>
    api.get<CaseSummary[]>('/api/v1/cases', { query: params, signal }),

  get: (id: string, signal?: AbortSignal) =>
    api.get<CaseDetail>(`/api/v1/cases/${id}`, { signal }),

  create: (data: { student_id: string; summary: string; priority?: string }) =>
    api.post<CaseSummary>('/api/v1/cases', data),

  transition: (
    id: string,
    data: { to_state: string; expected_version: number; reason?: string; notes?: string }
  ) => api.post<CaseSummary>(`/api/v1/cases/${id}/transition`, data),

  assign: (
    id: string,
    data: { owner_id: string; expected_version: number; notes?: string }
  ) => api.post<CaseSummary>(`/api/v1/cases/${id}/assign`, data),

  recordOutcome: (
    id: string,
    data: { outcome: 'helped' | 'mixed' | 'not_helped'; expected_version: number; notes?: string }
  ) => api.post<CaseSummary>(`/api/v1/cases/${id}/outcome`, data),

  events: (id: string, signal?: AbortSignal) =>
    api.get<CaseEvent[]>(`/api/v1/cases/${id}/events`, { signal }),

  interventions: (id: string, signal?: AbortSignal) =>
    api.get<CaseIntervention[]>(`/api/v1/cases/${id}/interventions`, { signal }),

  addIntervention: (
    id: string,
    data: { title: string; category: string; catalogue_id?: string; target_date?: string; notes?: string }
  ) => api.post<CaseIntervention>(`/api/v1/cases/${id}/interventions`, data),

  followups: (id: string, signal?: AbortSignal) =>
    api.get<CaseFollowup[]>(`/api/v1/cases/${id}/follow-ups`, { signal }),

  addFollowup: (
    id: string,
    data: { title: string; scheduled_at: string; notes?: string }
  ) => api.post<CaseFollowup>(`/api/v1/cases/${id}/follow-ups`, data),

  addConfidentialNote: (
    caseId: string,
    data: { content: string; session_id?: string }
  ) => api.post<{ id: string; created_at: string }>('/api/v1/counselling/notes', { case_id: caseId, ...data }),

  getAiReviewBrief: (caseId: string) =>
    api.post<AiReviewBrief>('/api/v1/ai/review-brief', { case_id: caseId }),
}

