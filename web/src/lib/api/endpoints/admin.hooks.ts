import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminApi, type RunRequest } from './admin'

export const adminKeys = {
  schema: ['ingestion', 'schema'] as const,
  imports: ['ingestion', 'imports'] as const,
  modelInfo: ['ml', 'model-info'] as const,
  runs: ['ml', 'runs'] as const,
  drift: ['ml', 'drift'] as const,
}

export const useIngestionSchema = () =>
  useQuery({ queryKey: adminKeys.schema, queryFn: ({ signal }) => adminApi.ingestionSchema(signal), staleTime: 10 * 60_000 })
export const useImports = () =>
  useQuery({ queryKey: adminKeys.imports, queryFn: ({ signal }) => adminApi.listImports(signal) })
export const useModelInfo = () =>
  useQuery({ queryKey: adminKeys.modelInfo, queryFn: ({ signal }) => adminApi.modelInfo(signal) })
export const useRuns = () => useQuery({ queryKey: adminKeys.runs, queryFn: ({ signal }) => adminApi.listRuns(signal) })
export const useDrift = () => useQuery({ queryKey: adminKeys.drift, queryFn: ({ signal }) => adminApi.drift(signal), retry: false })

export function useCreateImport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { files: Record<string, File>; dryRun: boolean }) => adminApi.createImport(v.files, v.dryRun),
    onSettled: () => void qc.invalidateQueries({ queryKey: adminKeys.imports }),
  })
}
export function useTriggerRun() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: RunRequest) => adminApi.triggerRun(body),
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: adminKeys.runs })
      void qc.invalidateQueries({ queryKey: adminKeys.drift })
      void qc.invalidateQueries({ queryKey: ['ml'] })
    },
  })
}

export const useAnalyticsOverview = () =>
  useQuery({ queryKey: ['analytics', 'overview'], queryFn: ({ signal }) => adminApi.analyticsOverview(signal) })
export const useAdminCases = () => useQuery({ queryKey: ['cases', 'admin'], queryFn: ({ signal }) => adminApi.cases(signal) })
export const useCatalogue = () => useQuery({ queryKey: ['interventions', 'catalog'], queryFn: ({ signal }) => adminApi.catalogue(signal) })
export const useMemberships = () => useQuery({ queryKey: ['campus', 'memberships'], queryFn: ({ signal }) => adminApi.memberships(signal) })
export const useInvitations = () => useQuery({ queryKey: ['campus', 'invitations'], queryFn: ({ signal }) => adminApi.invitations(signal) })
export const useAdminRedemptions = () => useQuery({ queryKey: ['rewards', 'admin-redemptions'], queryFn: ({ signal }) => adminApi.redemptions(signal) })

export function useInvite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (b: Parameters<typeof adminApi.invite>[0]) => adminApi.invite(b),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['campus'] }),
  })
}
export function useSetRedemptionStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; status: string }) => adminApi.setRedemptionStatus(v.id, v.status),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['rewards'] }),
  })
}

export const useRiskStudents = (tier?: string) =>
  useQuery({ queryKey: ['ml', 'students', tier ?? 'all'], queryFn: ({ signal }) => adminApi.riskStudents(tier, signal), retry: false })
export const useCohorts = () =>
  useQuery({ queryKey: ['ml', 'cohorts'], queryFn: ({ signal }) => adminApi.cohorts(signal), retry: false })

export const useEarlyWarning = () =>
  useQuery({ queryKey: ['ml', 'early-warning'], queryFn: ({ signal }) => adminApi.earlyWarning(signal), retry: false, staleTime: 60_000 })
