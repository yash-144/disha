import React, { useState, useRef, useEffect } from 'react'
import { CircleHelp, Bell, ChevronDown, Sparkles } from 'lucide-react'
import { useSession } from '../../lib/auth/SessionProvider'
import { UserAvatar } from '../common/UserAvatar'
import { roleLabel } from '../../lib/auth/portals'
import { DemoMode } from './studentDemoData'

interface StudentHeaderProps {
  title?: string
  subtitle?: string
  demoMode: DemoMode
  onSelectDemoMode: (mode: DemoMode) => void
}

const DEMO_MODE_OPTIONS: { id: DemoMode; label: string; badge: string; color: string }[] = [
  { id: 'normalStudent', label: 'Normal Student', badge: 'Stable', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { id: 'needsAttention', label: 'Needs Attention', badge: 'Alert', color: 'bg-amber-50 text-amber-700 border-amber-200' },
  { id: 'activeSupport', label: 'Active Support', badge: 'Intervention', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
]

export function StudentHeader({
  title,
  subtitle,
  demoMode,
  onSelectDemoMode,
}: StudentHeaderProps) {
  const { user } = useSession()
  const name = user?.full_name?.split(' ')[0] ?? ''
  const [demoDropdownOpen, setDemoDropdownOpen] = useState(false)
  const demoRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (demoRef.current && !demoRef.current.contains(e.target as Node)) {
        setDemoDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const currentScenario = DEMO_MODE_OPTIONS.find((opt) => opt.id === demoMode) || DEMO_MODE_OPTIONS[0]

  return (
    <header className="flex flex-col gap-3 font-sans select-none mb-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 sm:gap-2.5">

          {/* Vertical Divider */}
          <div className="h-4 w-px bg-gray-300/70 hidden sm:block" />

          {/* Demo Mode Switcher Dropdown */}
          <div className="relative" ref={demoRef}>
            <button
              type="button"
              onClick={() => {
                setDemoDropdownOpen(!demoDropdownOpen)
              }}
              className="flex items-center gap-1.5 sm:gap-2 px-3 py-1.5 bg-white border border-gray-200/90 rounded-full shadow-2xs hover:border-gray-300 transition text-xs font-semibold text-[#1E2433]"
              title="Switch demo scenarios to evaluate different student states"
            >
              <span className="text-[#64748B] font-normal hidden sm:inline">Demo Mode:</span>
              <span className="text-sm">🌿</span>
              <span>{currentScenario.label}</span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {demoDropdownOpen && (
              <div className="absolute left-0 top-full mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3 py-1.5 border-b border-gray-100 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                    Select Demo Mode
                  </span>
                </div>
                {DEMO_MODE_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      onSelectDemoMode(opt.id)
                      setDemoDropdownOpen(false)
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
                      demoMode === opt.id
                        ? 'bg-purple-50 text-purple-900 font-bold'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${demoMode === opt.id ? 'bg-purple-600' : 'bg-gray-300'}`} />
                      <span>{opt.label}</span>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${opt.color}`}>
                      {opt.badge}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Help icon + Notifications icon + Student Avatar with online dot */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Help icon button */}
          <button
            type="button"
            aria-label="Help and resources"
            className="flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-2xs border border-gray-200/90 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition"
          >
            <CircleHelp className="w-4 h-4" />
          </button>

          {/* Notifications button with red indicator dot */}
          <button
            type="button"
            aria-label="Notifications"
            className="relative flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-2xs border border-gray-200/90 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
          </button>

          {/* Student Profile Avatar with green online dot */}
          <div className="relative cursor-pointer ml-0.5">
            <UserAvatar name={user?.full_name} />
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
          </div>
        </div>
      </div>

      {/* Page Title & Subtitle */}
      <div>
        {title ? (
          <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
            {title}
          </h1>
        ) : (
          <h1 className="text-2xl font-bold tracking-tight text-[#1E2433] flex items-center gap-1.5">
            <span>Hi, {name}!</span>
            <span className="text-2xl">👋</span>
          </h1>
        )}
        <p className="text-xs text-[#717E95] font-medium mt-0.5">
          {subtitle || "Here's your wellbeing overview for this week."}
        </p>
      </div>
    </header>
  )
}

