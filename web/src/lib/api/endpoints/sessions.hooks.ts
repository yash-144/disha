import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi, CounsellingSession } from './sessions'

export const useSessionsList = () =>
  useQuery({
    queryKey: ['counselling', 'sessions'],
    queryFn: ({ signal }) => sessionsApi.list(signal),
  })

export function useCreateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof sessionsApi.create>[0]) => sessionsApi.create(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['counselling', 'sessions'] })
    },
  })
}

export function useRescheduleSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; scheduled_at: string; reason?: string }) =>
      sessionsApi.reschedule(v.id, { scheduled_at: v.scheduled_at, reason: v.reason }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['counselling', 'sessions'] })
    },
  })
}

export function useCompleteSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; notes?: string }) =>
      sessionsApi.complete(v.id, { notes: v.notes }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['counselling', 'sessions'] })
    },
  })
}

export function useCancelSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; reason?: string }) =>
      sessionsApi.cancel(v.id, { reason: v.reason }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['counselling', 'sessions'] })
    },
  })
}

