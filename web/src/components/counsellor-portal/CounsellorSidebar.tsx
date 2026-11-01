import React from 'react'
import {
  LayoutGrid,
  Calendar,
  AlertCircle,
  FolderKanban,
  LineChart,
  ShieldCheck,
} from 'lucide-react'
import { AppSidebar } from '../common/AppSidebar'

export type CounsellorNavId =
  | 'overview'
  | 'schedule'
  | 'students-in-need'
  | 'support-cases'
  | 'analytics'

export interface CounsellorSidebarProps {
  activeTab: CounsellorNavId
  onSelectTab: (tab: CounsellorNavId) => void
}

export interface NavItem {
  id: CounsellorNavId
  label: string
  route: string
  icon: React.ComponentType<{ className?: string }>
}

export const COUNSELLOR_NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', route: '/counsellor/overview', icon: LayoutGrid },
  { id: 'schedule', label: 'Schedule & Calls', route: '/counsellor/schedule', icon: Calendar },
  { id: 'students-in-need', label: 'Students in Need', route: '/counsellor/students-in-need', icon: AlertCircle },
  { id: 'support-cases', label: 'Support Cases', route: '/counsellor/support-cases', icon: FolderKanban },
  { id: 'analytics', label: 'Counsellor Analytics', route: '/counsellor/analytics', icon: LineChart },
]

export function CounsellorSidebar({ activeTab, onSelectTab }: CounsellorSidebarProps) {
  return (
    <AppSidebar
      role="counsellor"
      activeTab={activeTab}
      onSelectTab={(tab) => onSelectTab(tab as CounsellorNavId)}
    />
  )
}
