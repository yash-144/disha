import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { studentApi } from './student'

export const useSupportRequests = () =>
  useQuery({ queryKey: ['student', 'support-requests'], queryFn: ({ signal }) => studentApi.supportRequests(signal) })
export const useStudentAcademics = () =>
  useQuery({ queryKey: ['student', 'academics'], queryFn: ({ signal }) => studentApi.academics(signal) })
export const useStudentAttendance = () =>
  useQuery({ queryKey: ['student', 'attendance'], queryFn: ({ signal }) => studentApi.attendance(signal) })
export const useStudentCourses = () =>
  useQuery({ queryKey: ['student', 'courses'], queryFn: ({ signal }) => studentApi.courses(signal) })

export function useCreateSupportRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof studentApi.createSupportRequest>[0]) =>
      studentApi.createSupportRequest(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['student', 'support-requests'] })
    },
  })
}
export const usePulseCurrent = () =>
  useQuery({ queryKey: ['wellbeing', 'current'], queryFn: ({ signal }) => studentApi.pulseCurrent(signal), retry: false })
export const usePulseStatus = () =>
  useQuery({ queryKey: ['wellbeing', 'status'], queryFn: ({ signal }) => studentApi.pulseStatus(signal), retry: false })
export const usePulseTrends = () =>
  useQuery({ queryKey: ['wellbeing', 'trends'], queryFn: ({ signal }) => studentApi.pulseTrends(signal), retry: false })

export const useStudentNotifications = () =>
  useQuery({
    queryKey: ['student', 'notifications'],
    queryFn: ({ signal }) => studentApi.notifications(signal),
  })

export function useMarkNotificationRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => studentApi.markNotificationRead(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['student', 'notifications'] })
      void qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => studentApi.markAllNotificationsRead(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['student', 'notifications'] })
      void qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useSubmitPulse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { responses: Record<string, number>; reflection?: string }) => studentApi.submitPulse(v.responses, v.reflection),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['wellbeing'] }),
  })
}
