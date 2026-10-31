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
