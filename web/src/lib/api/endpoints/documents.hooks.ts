import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from './documents'

export const useDocuments = () => useQuery({ queryKey: ['documents', 'list'], queryFn: ({ signal }) => documentsApi.list(signal) })
export const useAnchoringStatus = () =>
  useQuery({ queryKey: ['documents', 'anchoring'], queryFn: ({ signal }) => documentsApi.anchoring(signal) })
export function useUploadDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { file: File; kind: string }) => documentsApi.upload(v.file, v.kind),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}
export function useVerifyDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => documentsApi.verify(id),
    onSettled: () => void qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}
