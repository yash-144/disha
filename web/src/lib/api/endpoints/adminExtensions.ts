import { api } from '../client'

export interface PolicyVersion {
  id: string
  version_number: number
  status: 'draft' | 'active' | 'archived'
  rules: Record<string, unknown>
  created_by?: string
  created_at: string
  published_at?: string | null
}

export interface AuditEvent {
  id: string
  campus_id: string
  actor_id: string
  actor_email?: string
  action: string
  entity_type: string
  entity_id: string
  event_hash: string
  previous_hash?: string | null
  metadata?: Record<string, unknown>
  created_at: string
}

export interface AuditVerificationResult {
  is_valid: boolean
  total_events: number
  verified_events: number
  genesis_hash?: string
  head_hash?: string
  error_message?: string
}

export interface CampusSettings {
  name: string
  code: string
  sla_hours_high_priority: number
  sla_hours_critical_priority: number
  max_caseload_per_counsellor: number
  auto_escalation_enabled: boolean
}

export interface MembershipInvite {
  id: string
  campus_id: string
  email: string
  role: string
  department?: string | null
  expires_at: string
  accepted_at?: string | null
  created_at: string
}

export interface CampusMembership {
  id: string
  user_id: string
  user_email?: string
  full_name?: string
  campus_id: string
  role: string
  department?: string | null
  is_active: boolean
  created_at: string
}

export interface StudentIdentityRecord {
  disha_id: string
  status: 'issued' | 'anchored' | 'unminted'
  transaction_hash?: string | null
  contract_address?: string | null
  art_svg?: string
}

export const adminExtensionsApi = {
  // Policy
  listPolicies: (signal?: AbortSignal) =>
    api.get<PolicyVersion[]>('/api/v1/policy/versions', { signal }),

  createPolicy: (data: { rules: Record<string, unknown> }) =>
    api.post<PolicyVersion>('/api/v1/policy/versions', data),

  publishPolicy: (versionId: string) =>
    api.post<PolicyVersion>(`/api/v1/policy/versions/${versionId}/publish`),

  dryRunPolicy: (data: { student_data: Record<string, unknown> }) =>
    api.post<{ decision: string; matched_rules: string[]; calibrated_risk: number }>('/api/v1/policy/evaluations/dry-run', data),

  // Audit
  listAudit: (signal?: AbortSignal) =>
    api.get<AuditEvent[]>('/api/v1/audit', { signal }),

  verifyAuditChain: () =>
    api.get<AuditVerificationResult>('/api/v1/audit/verify'),

  // Campus & Governance
  getSettings: (signal?: AbortSignal) =>
    api.get<CampusSettings>('/api/v1/campus/settings', { signal }),

  updateSettings: (data: Partial<CampusSettings>) =>
    api.patch<CampusSettings>('/api/v1/campus/settings', data),

  listInvitations: (signal?: AbortSignal) =>
    api.get<MembershipInvite[]>('/api/v1/campus/invitations', { signal }),

  createInvitation: (data: { email: string; role: string; department?: string }) =>
    api.post<MembershipInvite>('/api/v1/campus/invitations', data),

  revokeInvitation: (id: string) =>
    api.delete(`/api/v1/campus/invitations/${id}`),

  listMemberships: (signal?: AbortSignal) =>
    api.get<CampusMembership[]>('/api/v1/campus/memberships', { signal }),

  // Student Identity
  getMyIdentity: (signal?: AbortSignal) =>
    api.get<StudentIdentityRecord>('/api/v1/student-identity/me', { signal }),

  issueIdentity: () =>
    api.post<StudentIdentityRecord>('/api/v1/student-identity/me/issue'),
}

