import React from 'react'
import { CircleHelp, Bell, Sparkles } from 'lucide-react'
import { useSession } from '../../lib/auth/SessionProvider'
import { UserAvatar } from '../common/UserAvatar'
import { roleLabel } from '../../lib/auth/portals'

interface StudentHeaderProps {
  title?: string
  subtitle?: string
}

export function StudentHeader({
  title,
  subtitle,
}: StudentHeaderProps) {
  const { user } = useSession()
  const name = user?.full_name?.split(' ')[0] ?? ''

  return (
    <header className="flex flex-col gap-3 font-sans select-none mb-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 sm:gap-2.5">

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

