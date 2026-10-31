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

export const adminApi = {
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
