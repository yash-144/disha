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
} from 'lucide-react'
import { LogOut } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { UserAvatar } from './UserAvatar'

export type PortalRole = 'faculty' | 'instructor' | 'student' | 'counsellor' | 'admin'

export interface SidebarNavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

export const ROLE_NAV_ITEMS: Record<string, SidebarNavItem[]> = {
  faculty: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Schedule & Calls', icon: Calendar },
    { id: 'cases', label: 'My Cases', icon: FileText },
    { id: 'directory', label: 'Student Directory', icon: GraduationCap },
    { id: 'interventions', label: 'Interventions & Protocols', icon: MessageSquare },
    { id: 'integrity', label: 'Document Integrity', icon: ShieldCheck },
  ],
  student: [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'cases', label: 'My Cases', icon: FileText },
    { id: 'request-support', label: 'Request Support', icon: Heart },
    { id: 'assessment', label: 'Assessment', icon: Sparkles },
    { id: 'messages', label: 'Messages', icon: MessageSquare },
    { id: 'leaderboard', label: 'Leaderboard & Rewards', icon: Gift },
  ],
  counsellor: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Schedule & Calls', icon: Calendar },
    { id: 'students-in-need', label: 'Students in Need', icon: AlertCircle },
    { id: 'support-cases', label: 'Support Cases', icon: FolderKanban },
    { id: 'analytics', label: 'Counsellor Analytics', icon: LineChart },
    { id: 'document-integrity', label: 'Document Integrity', icon: ShieldCheck },
  ],
  admin: [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'schedule', label: 'Schedule & Calls', icon: Calendar },
    { id: 'case-management', label: 'Case Management', icon: FolderKanban },
    { id: 'student-directory', label: 'Student Directory', icon: GraduationCap },
    { id: 'interventions', label: 'Interventions & Protocols', icon: Sliders },
    { id: 'analytics', label: 'Institution Analytics', icon: BarChart3 },
    { id: 'document-integrity', label: 'Document Integrity', icon: ShieldCheck },
    { id: 'reward-fulfilment', label: 'Reward Fulfilment', icon: Award },
  ],
}

export interface AppSidebarProps {
  role?: PortalRole
  activeTab: string
  onSelectTab: (tab: string) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function AppSidebar({
  role = 'faculty',
  activeTab,
  onSelectTab,
  isCollapsed = false,
  onToggleCollapse,
}: AppSidebarProps) {
  const { navigateTo } = useApp()

  // Normalize role key
  const normalizedRole = role === 'instructor' ? 'faculty' : role
  const navItems = ROLE_NAV_ITEMS[normalizedRole] || ROLE_NAV_ITEMS.faculty
  const { user, role: serverRole, signOut } = useSession()

  return (
    <aside
      className={`shrink-0 py-5 flex flex-col justify-between font-sans select-none min-h-full transition-all duration-300 ${
        isCollapsed
          ? 'w-20 min-w-[80px] max-w-[80px] px-2.5'
          : 'w-60 min-w-[240px] max-w-[240px] px-3.5'
      }`}
      aria-label="Application sidebar navigation"
    >
      <div className="flex flex-col flex-1 min-h-0">
        {/* DISHA Brand Logo (Standardized scale across all portals) */}
        <button
          type="button"
          onClick={() => navigateTo('landing')}
          className={`flex items-center gap-3 px-2 mb-7 text-left group cursor-pointer focus:outline-none ${
            isCollapsed ? 'justify-center px-0' : ''
          }`}
          title="Return to Home"
        >
          {/* 4-petal colored flower/leaf logo */}
          <div className="relative w-7 h-7 shrink-0 transition-transform group-hover:scale-105">
            <span className="absolute top-0 left-0 w-3.5 h-3.5 rounded-tl-full rounded-br-full bg-[#22C55E]" />
            <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-tr-full rounded-bl-full bg-[#3B82F6]" />
            <span className="absolute bottom-0 left-0 w-3.5 h-3.5 rounded-bl-full rounded-tr-full bg-[#8B5CF6]" />
            <span className="absolute bottom-0 right-0 w-3.5 h-3.5 rounded-br-full rounded-tl-full bg-[#06B6D4]" />
          </div>

          {!isCollapsed && (
            <span className="text-xl font-black tracking-tight text-[#1E2433] leading-none">
              DISHA
            </span>
          )}
        </button>

        {/* Navigation Items (Standardized item height, font size, active indicator & icon scale) */}
        <nav
          className="space-y-1.5 flex-1 overflow-y-auto pr-0.5"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTab(item.id)}
                title={item.label}
                className={`relative w-full flex items-center rounded-2xl text-left text-[13px] transition-all cursor-pointer ${
                  isCollapsed
                    ? 'justify-center p-2.5'
                    : 'gap-3 px-3.5 py-2.5'
                } ${
                  isActive
                    ? 'bg-[#EDE9FE]/70 text-[#1E2433] font-bold shadow-2xs'
                    : 'text-[#64748B] hover:text-[#1E2433] hover:bg-black/5 font-medium'
                }`}
              >
                {/* Active vertical bar indicator on left */}
                {isActive && (
                  <span
                    className={`absolute top-1/2 -translate-y-1/2 w-1.5 h-5 bg-[#1E2433] rounded-full ${
                      isCollapsed ? '-left-1' : '-left-2'
                    }`}
                  />
                )}

                {/* Active Icon Pill vs Inactive Icon */}
                {isActive ? (
                  <span className="flex items-center justify-center w-7 h-7 rounded-xl bg-[#1E2433] text-white shadow-xs shrink-0">
                    <Icon className="w-4 h-4 text-white" />
                  </span>
                ) : (
                  <span className="flex items-center justify-center w-7 h-7 shrink-0 text-[#64748B]">
                    <Icon className="w-4 h-4" />
                  </span>
                )}

                {!isCollapsed && (
                  <span className="truncate leading-tight">
                    {item.label}
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Decorative foliage matching DISHA design reference */}
      {!isCollapsed && (
        <div className="relative mt-auto pt-2 px-1 pointer-events-none opacity-60">
          <svg viewBox="0 0 160 70" className="w-full h-auto text-[#C7D2FE]" fill="none">
            <path d="M-10 70 C20 45 70 50 110 62 C130 68 150 70 170 70 Z" fill="#E0E7FF" opacity="0.8" />
            <path d="M-20 70 C30 35 80 40 140 60 C160 66 170 70 180 70 Z" fill="#DDD6FE" opacity="0.6" />
            <path d="M25 65 C28 42 35 28 50 15" stroke="#A5B4FC" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M32 42 C22 38 18 28 25 24 C33 28 35 36 32 42 Z" fill="#818CF8" opacity="0.75" />
            <path d="M37 30 C45 25 55 26 57 32 C50 36 41 35 37 30 Z" fill="#A78BFA" opacity="0.8" />
            <path d="M48 16 C46 8 56 4 64 10 C64 15 56 18 48 16 Z" fill="#C084FC" opacity="0.75" />
          </svg>
        </div>
      )}

      {/* Bottom Profile Section (Standardized avatar dimensions, typography & divider) */}
      <div
        className={`pt-3 border-t border-gray-100/70 mt-2 flex items-center ${
          isCollapsed ? 'justify-center px-0' : 'gap-2.5 px-1.5'
        }`}
      >
        <div className="relative shrink-0">
          <UserAvatar name={user?.full_name} />
        </div>

        {!isCollapsed && (
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-[#1E2433] truncate leading-tight">
              {user?.full_name}
            </p>
            <p className="text-[11px] text-[#717E95] leading-tight mt-0.5 truncate font-medium">
              {roleLabel(serverRole)}
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={() => void signOut()}
          title="Sign out"
          aria-label="Sign out"
          className="shrink-0 rounded-full p-1.5 text-[#64748B] hover:bg-black/5 hover:text-[#1E2433] cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  )
}
