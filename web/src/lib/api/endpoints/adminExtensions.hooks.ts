import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminExtensionsApi, CampusSettings } from './adminExtensions'

export const usePolicies = () =>
  useQuery({
    queryKey: ['policy', 'versions'],
    queryFn: ({ signal }) => adminExtensionsApi.listPolicies(signal),
  })

export function usePublishPolicy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (versionId: string) => adminExtensionsApi.publishPolicy(versionId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['policy'] })
    },
  })
}

export const useAuditEvents = () =>
  useQuery({
    queryKey: ['audit', 'events'],
    queryFn: ({ signal }) => adminExtensionsApi.listAudit(signal),
  })

export function useVerifyAuditChain() {
  return useMutation({
    mutationFn: () => adminExtensionsApi.verifyAuditChain(),
  })
}

export const useCampusSettings = () =>
  useQuery({
    queryKey: ['campus', 'settings'],
    queryFn: ({ signal }) => adminExtensionsApi.getSettings(signal),
  })

export function useUpdateCampusSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<CampusSettings>) => adminExtensionsApi.updateSettings(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['campus', 'settings'] })
    },
  })
}

export const useInvitations = () =>
  useQuery({
    queryKey: ['campus', 'invitations'],
    queryFn: ({ signal }) => adminExtensionsApi.listInvitations(signal),
  })

export function useCreateInvitation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { email: string; role: string; department?: string }) =>
      adminExtensionsApi.createInvitation(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['campus', 'invitations'] })
    },
  })
}

export function useRevokeInvitation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => adminExtensionsApi.revokeInvitation(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['campus', 'invitations'] })
    },
  })
}

export const useMemberships = () =>
  useQuery({
    queryKey: ['campus', 'memberships'],
    queryFn: ({ signal }) => adminExtensionsApi.listMemberships(signal),
  })

export const useStudentIdentity = () =>
  useQuery({
    queryKey: ['student', 'identity'],
    queryFn: ({ signal }) => adminExtensionsApi.getMyIdentity(signal),
  })

export function useIssueStudentIdentity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => adminExtensionsApi.issueIdentity(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['student', 'identity'] })
    },
  })
}
