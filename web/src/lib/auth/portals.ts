/**
 * Maps server role names (api/app/core/permissions.py: Role) to the four web
 * portals. The role always comes from the server; never from URL or storage.
 */
export type Portal = 'instructor' | 'student' | 'counsellor' | 'admin'

const ROLE_TO_PORTAL: Record<string, Portal> = {
  student: 'student',
  faculty: 'instructor',
  mentor: 'instructor',
  hod: 'instructor',
  counsellor: 'counsellor',
  institution_admin: 'admin',
  platform_admin: 'admin',
}

export function portalForRole(role: string | null | undefined): Portal | null {
  return role ? ROLE_TO_PORTAL[role] ?? null : null
}

const ROLE_LABELS: Record<string, string> = {
  student: 'Student',
  faculty: 'Faculty',
  mentor: 'Mentor',
  hod: 'Head of Department',
  counsellor: 'Counsellor',
  finance: 'Finance',
  placement: 'Placement',
  leadership: 'Leadership',
  institution_admin: 'Institution Admin',
  platform_admin: 'Platform Admin',
}

export function roleLabel(role: string | null | undefined): string {
  if (!role) return ''
  return ROLE_LABELS[role] ?? role
}
