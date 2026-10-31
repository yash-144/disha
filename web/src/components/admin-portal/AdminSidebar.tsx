import React from 'react'
import {
  LayoutGrid,
  Calendar,
  FolderKanban,
  GraduationCap,
  Sliders,
  BarChart3,
  ShieldCheck,
  Award,
} from 'lucide-react'
import { AppSidebar } from '../common/AppSidebar'

export type AdminNavId =
  | 'overview'
  | 'schedule'
  | 'case-management'
  | 'student-directory'
  | 'interventions'
  | 'analytics'
  | 'document-integrity'
  | 'reward-fulfilment'

export interface AdminSidebarProps {
  activeTab: AdminNavId
  onSelectTab: (tab: AdminNavId) => void
}

export interface NavItem {
  id: AdminNavId
  label: string
  route: string
  icon: React.ComponentType<{ className?: string }>
}

export const ADMIN_NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', route: '/admin/overview', icon: LayoutGrid },
  { id: 'schedule', label: 'Schedule & Calls', route: '/admin/schedule', icon: Calendar },
  { id: 'case-management', label: 'Case Management', route: '/admin/case-management', icon: FolderKanban },
  { id: 'student-directory', label: 'Student Directory', route: '/admin/student-directory', icon: GraduationCap },
  { id: 'interventions', label: 'Interventions & Protocols', route: '/admin/interventions', icon: Sliders },
  { id: 'analytics', label: 'Institution Analytics', route: '/admin/analytics', icon: BarChart3 },
  { id: 'document-integrity', label: 'Document Integrity', route: '/admin/document-integrity', icon: ShieldCheck },
  { id: 'reward-fulfilment', label: 'Reward Fulfilment', route: '/admin/reward-fulfilment', icon: Award },
]

export function AdminSidebar({ activeTab, onSelectTab }: AdminSidebarProps) {
  return (
    <AppSidebar
      role="admin"
      activeTab={activeTab}
      onSelectTab={(tab) => onSelectTab(tab as AdminNavId)}
    />
  )
}
