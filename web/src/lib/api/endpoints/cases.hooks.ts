import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { casesApi } from './cases'

export const useCasesList = (params?: { state?: string; priority?: string; owner_id?: string }) =>
  useQuery({
    queryKey: ['cases', params],
    queryFn: ({ signal }) => casesApi.list(params, signal),
  })

export const useCaseDetail = (id: string | null) =>
  useQuery({
    queryKey: ['cases', id],
    queryFn: ({ signal }) => (id ? casesApi.get(id, signal) : null),
    enabled: Boolean(id),
  })

export const useCaseEvents = (id: string | null) =>
  useQuery({
    queryKey: ['cases', id, 'events'],
    queryFn: ({ signal }) => (id ? casesApi.events(id, signal) : []),
    enabled: Boolean(id),
  })

export const useCaseInterventions = (id: string | null) =>
  useQuery({
    queryKey: ['cases', id, 'interventions'],
    queryFn: ({ signal }) => (id ? casesApi.interventions(id, signal) : []),
    enabled: Boolean(id),
  })

export const useCaseFollowups = (id: string | null) =>
  useQuery({
    queryKey: ['cases', id, 'followups'],
    queryFn: ({ signal }) => (id ? casesApi.followups(id, signal) : []),
    enabled: Boolean(id),
  })

export function useTransitionCase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; to_state: string; expected_version: number; reason?: string; notes?: string }) =>
      casesApi.transition(v.id, { to_state: v.to_state, expected_version: v.expected_version, reason: v.reason, notes: v.notes }),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ['cases'] })
      void qc.invalidateQueries({ queryKey: ['cases', v.id] })
    },
  })
}

export function useAssignCase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; owner_id: string; expected_version: number; notes?: string }) =>
      casesApi.assign(v.id, { owner_id: v.owner_id, expected_version: v.expected_version, notes: v.notes }),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ['cases'] })
      void qc.invalidateQueries({ queryKey: ['cases', v.id] })
    },
  })
}

export function useRecordCaseOutcome() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; outcome: 'helped' | 'mixed' | 'not_helped'; expected_version: number; notes?: string }) =>
      casesApi.recordOutcome(v.id, { outcome: v.outcome, expected_version: v.expected_version, notes: v.notes }),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ['cases'] })
      void qc.invalidateQueries({ queryKey: ['cases', v.id] })
    },
  })
}

export function useAddCaseIntervention() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; title: string; category: string; catalogue_id?: string; target_date?: string; notes?: string }) =>
      casesApi.addIntervention(v.id, v),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ['cases', v.id, 'interventions'] })
      void qc.invalidateQueries({ queryKey: ['cases', v.id] })
    },
  })
}

export function useAddCaseNote() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { caseId: string; content: string; session_id?: string }) =>
      casesApi.addConfidentialNote(v.caseId, { content: v.content, session_id: v.session_id }),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ['cases', v.caseId] })
    },
  })
}

export function useAiReviewBrief() {
  return useMutation({
    mutationFn: (caseId: string) => casesApi.getAiReviewBrief(caseId),
  })
}
