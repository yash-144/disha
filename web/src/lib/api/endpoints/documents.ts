import { api } from '../client'
import type { components } from '../schema'

type S = components['schemas']
export type DocumentRecord = S['DocumentResponse']
export type Verification = S['VerificationResponse']
export type AnchoringStatus = S['AnchoringStatusResponse']

export const documentsApi = {
  list: (signal?: AbortSignal) => api.get<DocumentRecord[]>('/api/v1/documents', { query: { limit: 100 }, signal }),
  anchoring: (signal?: AbortSignal) => api.get<AnchoringStatus>('/api/v1/documents/anchoring/status', { signal }),
  upload: (file: File, kind: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('kind', kind)
    return api.post<DocumentRecord>('/api/v1/documents', form)
  },
  verify: (id: string) => api.post<Verification>(`/api/v1/documents/${id}/verify`),
}
