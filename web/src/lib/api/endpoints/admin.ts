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

export const adminApi = {
  analyticsOverview: (signal?: AbortSignal) => api.get<Record<string, unknown>>('/api/v1/analytics/overview', { signal }),
  cases: (signal?: AbortSignal) => api.get<CaseDetail[]>('/api/v1/cases/', { query: { limit: 200 }, signal }),
  catalogue: (signal?: AbortSignal) => api.get<CatalogueItem[]>('/api/v1/interventions/catalog', { query: { include_inactive: true }, signal }),
  memberships: (signal?: AbortSignal) => api.get<Membership[]>('/api/v1/campus/memberships', { query: { limit: 200 }, signal }),
  invitations: (signal?: AbortSignal) => api.get<Invite[]>('/api/v1/campus/invitations', { query: { limit: 100 }, signal }),
  invite: (body: { email: string; role: string; department?: string | null; expires_in_days: number }) =>
    api.post<Invite>('/api/v1/campus/invitations', body),
  redemptions: (signal?: AbortSignal) => api.get<Redemption[]>('/api/v1/rewards/redemptions', { query: { limit: 200 }, signal }),
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
