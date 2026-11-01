import { api } from '../client'
import type { components } from '../schema'

type S = components['schemas']
export type CanonicalSchema = S['CanonicalSchemaResponse']
export type ImportBatch = S['ImportBatchResponse']
export type ImportBatchPage = S['ImportBatchPage']
export type ImportIssue = S['ImportIssue']
export type ModelInfo = S['ModelInfoResponse']
export type ScoringRun = S['ScoringRunResponse']
export type RunPage = S['RunPage']
export type RunRequest = S['ScoringRunRequest']
export type DriftReport = S['DriftResponse']

export type Membership = S['MembershipItem']
export type Invite = S['InviteResponse']
export type CatalogueItem = S['CatalogueItem']
export type Redemption = S['RedemptionResponse']
export type CaseDetail = S['CaseDetailResponse']

export interface RiskStudentRow {
  id: string
  student_ref: string
  student_id: string | null
  course_id: string
  probability: number
  tier: 'HIGH' | 'MEDIUM' | 'WATCH' | 'ON_TRACK'
  direction: string | null
  previous_probability: number | null
  reasons: { text: string; group: string }[]
}
export interface CohortRow {
  course_id: string
  term_id: string
  n_enrolled: number
  n_active: number
  mean_risk: number
  at_risk_share: number
  tier_distribution: Record<string, { n: number; share: number }>
  time_to_risk?: { day: number; cumulative_signalled_share: number; signalled_share: number }[]
  hotspot?: { label: string; due_day: number; n_students: number | null; share_of_at_risk: number | null } | null
}

export interface EarlyWarning {
  campus: {
    enrolments_scored: number
    enrolments_flagged: number
    median_first_flag_day: number | null
    median_first_flag_pct_of_term: number | null
    flagged_in_first_half_of_term: number | null
    left_course: number | null
    left_after_flag: number | null
    median_days_warning_before_leaving: number | null
    cumulative_flagged: { day: number; flagged_students: number; share_of_scored: number }[]
    resolution?: string
  }
  benchmark: {
    source: string
    left_course: number
    flagged_before_leaving: number
    detection_rate: number
    median_days_warning: number
    p25_days: number
    p75_days: number
    struggling_students_caught: number | null
    flagged_who_really_struggled: number | null
  }
}

export const adminApi = {
  earlyWarning: (signal?: AbortSignal) => api.get<EarlyWarning>('/api/v1/ml/early-warning', { signal }),
  riskStudents: (tier?: string, signal?: AbortSignal) =>
    api.get<{ run_id: string; as_of_day: number; items: RiskStudentRow[]; total?: number }>('/api/v1/ml/students', {
      query: { tier, page_size: 8 },
      signal,
    }),
  cohorts: (signal?: AbortSignal) =>
    api.get<{ run_id: string; as_of_day: number; cohorts: CohortRow[] }>('/api/v1/ml/cohorts', { signal }),
  analyticsOverview: (signal?: AbortSignal) => api.get<Record<string, unknown>>('/api/v1/analytics/overview', { signal }),
  cases: (signal?: AbortSignal) => api.get<CaseDetail[]>('/api/v1/cases/', { query: { limit: 100 }, signal }),
  catalogue: (signal?: AbortSignal) => api.get<CatalogueItem[]>('/api/v1/interventions/catalog', { query: { include_inactive: true }, signal }),
  memberships: (signal?: AbortSignal) => api.get<Membership[]>('/api/v1/campus/memberships', { query: { limit: 100 }, signal }),
  invitations: (signal?: AbortSignal) => api.get<Invite[]>('/api/v1/campus/invitations', { query: { limit: 100 }, signal }),
  invite: (body: { email: string; role: string; department?: string | null; expires_in_days: number }) =>
    api.post<Invite>('/api/v1/campus/invitations', body),
  redemptions: (signal?: AbortSignal) => api.get<Redemption[]>('/api/v1/rewards/redemptions', { query: { limit: 100 }, signal }),
  setRedemptionStatus: (id: string, status: string) =>
    api.post<Redemption>(`/api/v1/rewards/redemptions/${id}/status`, { status }),

  ingestionSchema: (signal?: AbortSignal) => api.get<CanonicalSchema>('/api/v1/ingestion/schema', { signal }),
  listImports: (signal?: AbortSignal) =>
    api.get<ImportBatchPage>('/api/v1/ingestion/imports', { query: { page_size: 20 }, signal }),
  /** multipart; field names are the canonical table names (or `workbook`). */
  createImport: (files: Record<string, File>, dryRun: boolean) => {
    const form = new FormData()
    for (const [field, file] of Object.entries(files)) form.append(field, file)
    return api.post<ImportBatch>('/api/v1/ingestion/imports', form, { query: { dry_run: dryRun } })
  },
  modelInfo: (signal?: AbortSignal) => api.get<ModelInfo>('/api/v1/ml/model-info', { signal }),
  listRuns: (signal?: AbortSignal) => api.get<RunPage>('/api/v1/ml/runs', { query: { page_size: 20 }, signal }),
  triggerRun: (body: RunRequest) => api.post<ScoringRun>('/api/v1/ml/runs', body),
  drift: (signal?: AbortSignal) => api.get<DriftReport>('/api/v1/ml/drift', { signal }),
}
