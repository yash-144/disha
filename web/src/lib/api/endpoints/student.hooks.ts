import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { studentApi } from './student'

export const useSupportRequests = () =>
  useQuery({ queryKey: ['student', 'support-requests'], queryFn: ({ signal }) => studentApi.supportRequests(signal) })
export const usePulseCurrent = () =>
  useQuery({ queryKey: ['wellbeing', 'current'], queryFn: ({ signal }) => studentApi.pulseCurrent(signal), retry: false })
export const usePulseStatus = () =>
  useQuery({ queryKey: ['wellbeing', 'status'], queryFn: ({ signal }) => studentApi.pulseStatus(signal), retry: false })
export const usePulseTrends = () =>
  useQuery({ queryKey: ['wellbeing', 'trends'], queryFn: ({ signal }) => studentApi.pulseTrends(signal), retry: false })
export const useRewardBalance = () =>
  useQuery({ queryKey: ['rewards', 'balance'], queryFn: ({ signal }) => studentApi.balance(signal) })
export const useRewardCatalog = () =>
  useQuery({ queryKey: ['rewards', 'catalog'], queryFn: ({ signal }) => studentApi.catalog(signal) })
export const useMyRedemptions = () =>
  useQuery({ queryKey: ['rewards', 'mine'], queryFn: ({ signal }) => studentApi.myRedemptions(signal) })

export function useSubmitPulse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { responses: Record<string, number>; reflection?: string }) => studentApi.submitPulse(v.responses, v.reflection),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['wellbeing'] }),
  })
}
export function useRedeem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => studentApi.redeem(itemId, crypto.randomUUID()),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['rewards'] }),
  })
}
