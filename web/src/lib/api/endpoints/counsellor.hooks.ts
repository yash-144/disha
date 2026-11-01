import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { counsellorApi } from './counsellor'

export const useCounsellorDashboard = () =>
  useQuery({ queryKey: ['counselling', 'dashboard'], queryFn: ({ signal }) => counsellorApi.dashboard(signal) })
export const useCaseload = () =>
  useQuery({ queryKey: ['counselling', 'caseload'], queryFn: ({ signal }) => counsellorApi.caseload(undefined, signal) })
export const useFollowups = () =>
  useQuery({ queryKey: ['counselling', 'followups'], queryFn: ({ signal }) => counsellorApi.followups(signal) })
export const useCounsellingSessions = () =>
  useQuery({ queryKey: ['counselling', 'sessions'], queryFn: ({ signal }) => counsellorApi.sessions(signal) })
/** 404/409 (no scoring run yet) is surfaced as an error the page turns into an empty state. */
export const useMlStudents = (tier: string) =>
  useQuery({
    queryKey: ['ml', 'students', tier],
    queryFn: ({ signal }) => counsellorApi.mlStudents(tier, signal),
    retry: false,
  })
export const useCases = (state?: string) =>
  useQuery({ queryKey: ['cases', 'list', state ?? 'all'], queryFn: ({ signal }) => counsellorApi.cases(state, signal) })

export function useCaseDecision() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; version: number; action: 'advance' | 'dismiss'; target?: string }) =>
      v.action === 'advance' ? counsellorApi.advance(v.id, v.version, v.target!) : counsellorApi.dismiss(v.id, v.version).then((c) => ({ case: c })),
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: ['cases'] })
      void qc.invalidateQueries({ queryKey: ['counselling'] })
    },
  })
}
