import { fetchClient } from '@/lib/api/client';

export interface AdminDashboardData {
  total_students: number;
  total_faculty: number;
  total_counsellors: number;
  total_active_cases: number;
  pending_cases: number;
  overdue_cases: number;
  resolved_cases: number;
  counsellor_workload: Array<{
    user_id: string;
    full_name: string;
    email: string;
    department?: string;
    active_cases: number;
    overdue_cases: number;
    resolved_cases: number;
    availability_status: string;
  }>;
  recent_activities: Array<any>;
  administrative_notifications: Array<any>;
}

export interface AdminUserItem {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  campus_id: string;
  department?: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminCaseItem {
  id: string;
  student_id: string;
  student_name?: string;
  student_ref?: string;
  department?: string;
  priority: string;
  state: string;
  primary_owner_user_id?: string;
  counsellor_name?: string;
  due_at?: string;
  is_overdue: boolean;
  is_escalated: boolean;
  selected_intervention_key?: string;
  version: number;
  created_at: string;
}

export interface AdminImportItem {
  id: string;
  campus_id: string;
  file_name: string;
  source_type: string;
  status: string;
  total_records: number;
  processed_records: number;
  error_count: number;
  created_at: string;
}

export interface AdminAuditItem {
  id: string;
  actor_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  metadata: Record<string, any>;
  curr_hash?: string;
  created_at: string;
}

export const adminApi = {
  getDashboard: (token?: string, campusId?: string): Promise<AdminDashboardData> =>
    fetchClient('/api/v1/admin/dashboard', {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    }),

  getUsers: (role?: string, search?: string, token?: string, campusId?: string) => {
    const params = new URLSearchParams();
    if (role) params.append('role', role);
    if (search) params.append('search', search);
    return fetchClient(`/api/v1/admin/users?${params.toString()}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    });
  },

  getCases: (overdueOnly: boolean = false, token?: string, campusId?: string): Promise<AdminCaseItem[]> =>
    fetchClient(overdueOnly ? '/api/v1/admin/cases/overdue' : '/api/v1/admin/cases', {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    }),

  reassignCase: (
    caseId: string,
    payload: { new_counsellor_user_id: string; reassignment_reason: string; expected_version: number },
    token?: string,
    campusId?: string
  ) =>
    fetchClient(`/api/v1/admin/cases/${caseId}/reassign`, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    }),

  getImports: (token?: string, campusId?: string): Promise<AdminImportItem[]> =>
    fetchClient('/api/v1/admin/imports', {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    }),

  getAuditLogs: (token?: string, campusId?: string): Promise<AdminAuditItem[]> =>
    fetchClient('/api/v1/admin/audit', {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(campusId ? { 'X-Campus-ID': campusId } : {}),
      },
    }),
};

