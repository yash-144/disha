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
  UploadCloud,
  Cpu,
} from 'lucide-react'
import { AppSidebar } from '../common/AppSidebar'

export type AdminNavId =
  | 'overview'
  | 'schedule'
  | 'case-management'
  | 'student-directory'
  | 'interventions'
  | 'analytics'
  | 'data-import'
  | 'risk-model'

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
  { id: 'schedule', label: 'Sessions and calls', route: '/admin/schedule', icon: Calendar },
  { id: 'case-management', label: 'Cases', route: '/admin/case-management', icon: FolderKanban },
  { id: 'student-directory', label: 'Students & staff', route: '/admin/student-directory', icon: GraduationCap },
  { id: 'interventions', label: 'Support options', route: '/admin/interventions', icon: Sliders },
  { id: 'analytics', label: 'Reports', route: '/admin/analytics', icon: BarChart3 },
  { id: 'data-import', label: 'Upload data', route: '/admin/data-import', icon: UploadCloud },
  { id: 'risk-model', label: 'Early warning', route: '/admin/risk-model', icon: Cpu },
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
