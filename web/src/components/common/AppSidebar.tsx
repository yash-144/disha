import React from 'react'
import {
  LayoutGrid,
  Calendar,
  FileText,
  GraduationCap,
  MessageSquare,
  ShieldCheck,
  Home,
  Heart,
  Sparkles,
  Gift,
  AlertCircle,
  FolderKanban,
  LineChart,
  BarChart3,
  Sliders,
  Award,
  UploadCloud,
  Cpu,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { AccountMenu } from './AccountMenu'
import { useT } from '../../i18n'

export type PortalRole = 'faculty' | 'instructor' | 'student' | 'counsellor' | 'admin'

export interface SidebarNavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

export const ROLE_NAV_ITEMS: Record<string, SidebarNavItem[]> = {
  faculty: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'cases', label: 'My Cases', icon: FileText },
    { id: 'directory', label: 'My students', icon: GraduationCap },
    { id: 'interventions', label: 'Ways to help', icon: MessageSquare },
    { id: 'assessment', label: 'Classroom', icon: Sparkles },
  ],
  student: [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'cases', label: 'My requests', icon: FileText },
    { id: 'request-support', label: 'Ask for help', icon: Heart },
    { id: 'assessment', label: 'Wellbeing check-in', icon: Sparkles },
    { id: 'messages', label: 'Messages', icon: MessageSquare },
  ],
  counsellor: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Sessions and calls', icon: Calendar },
    { id: 'students-in-need', label: 'Students in Need', icon: AlertCircle },
    { id: 'support-cases', label: 'My cases', icon: FolderKanban },
    { id: 'analytics', label: 'Results', icon: LineChart },
  ],
  admin: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'case-management', label: 'Cases', icon: FolderKanban },
    { id: 'student-directory', label: 'Students & staff', icon: GraduationCap },
    { id: 'interventions', label: 'Support options', icon: Sliders },
    { id: 'analytics', label: 'Reports', icon: BarChart3 },
    { id: 'data-import', label: 'Upload data', icon: UploadCloud },
    { id: 'risk-model', label: 'Early warning', icon: Cpu },
  ],
}

export interface AppSidebarProps {
  role?: PortalRole
  activeTab: string
  onSelectTab: (tab: string) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function Wordmark({ light = true }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <svg viewBox="0 0 28 28" className="h-7 w-7 shrink-0" aria-hidden="true">
        <rect width="28" height="28" rx="6" fill="var(--color-accent)" />
        <path d="M6 19 L11 13 L15 16 L22 8" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="22" cy="8" r="2.2" fill="#fff" />
      </svg>
      <span className={`font-display text-[26px] leading-none tracking-tight ${light ? 'text-white' : 'text-ink'}`}>Disha</span>
    </span>
  )
}

export function AppSidebar({ role = 'faculty', activeTab, onSelectTab }: AppSidebarProps) {
  const { navigateTo } = useApp()
  const t = useT()
  const normalizedRole = role === 'instructor' ? 'faculty' : role
  const navItems = ROLE_NAV_ITEMS[normalizedRole] || ROLE_NAV_ITEMS.faculty

  return (
    <aside
      className="sticky top-0 z-30 flex h-screen w-16 shrink-0 flex-col bg-night px-2.5 py-5 font-sans text-white select-none lg:w-60 lg:px-4"
      aria-label="Main navigation"
    >
      <button type="button" onClick={() => navigateTo('landing')} className="mb-8 flex items-center justify-center px-1 text-left lg:justify-start" title="Back to home">
        <span className="lg:hidden"><svg viewBox="0 0 28 28" className="h-8 w-8" aria-hidden="true"><rect width="28" height="28" rx="6" fill="var(--color-accent)" /><path d="M6 19 L11 13 L15 16 L22 8" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /><circle cx="22" cy="8" r="2.2" fill="#fff" /></svg></span>
        <span className="hidden lg:block"><Wordmark /></span>
      </button>

      <nav className="flex-1 space-y-0.5 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectTab(item.id)}
              title={t(item.label)}
              aria-current={isActive ? 'page' : undefined}
              className={`relative flex w-full cursor-pointer items-center justify-center gap-3 rounded-md px-3 py-2.5 text-left text-sm transition-colors lg:justify-start ${
                isActive ? 'bg-night-2 font-semibold text-white' : 'font-medium text-white/60 hover:bg-night-2/60 hover:text-white'
              }`}
            >
              {isActive && <span className="absolute -left-2.5 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-accent lg:-left-4" />}
              <Icon className={`h-[18px] w-[18px] shrink-0 ${isActive ? 'text-white' : ''}`} />
              <span className="hidden truncate lg:inline">{t(item.label)}</span>
            </button>
          )
        })}
      </nav>

      <div className="mt-3 border-t border-white/10 pt-3">
        <AccountMenu variant="sidebar" />
      </div>
    </aside>
  )
}
