import React from 'react'
import { CircleHelp, Bell } from 'lucide-react'
import { useSession } from '../../lib/auth/SessionProvider'
import { UserAvatar } from '../common/UserAvatar'
import { roleLabel } from '../../lib/auth/portals'

interface CounsellorHeaderProps {
  pageTitle?: string
  subtitle?: string
  showPageTitle?: boolean
}

export function CounsellorHeader({
  pageTitle,
  subtitle,
  showPageTitle = false,
}: CounsellorHeaderProps) {
  const { user } = useSession()
  return (
    <header className="flex flex-col gap-3 font-sans select-none mb-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 sm:gap-2.5">

        </div>

        {/* Right: Help icon + Notifications icon + Counsellor Avatar with green online dot */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Help icon button */}
          <button
            type="button"
            aria-label="Help and resources"
            className="flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-2xs border border-gray-200/90 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition cursor-pointer"
          >
            <CircleHelp className="w-4 h-4" />
          </button>

          {/* Notifications button with red indicator dot */}
          <button
            type="button"
            aria-label="Notifications"
            className="relative flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-2xs border border-gray-200/90 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition cursor-pointer"
          >
            <Bell className="w-4 h-4" />
          </button>

          {/* Counsellor Profile Avatar */}
          <div className="relative ml-0.5 cursor-pointer">
            <UserAvatar name={user?.full_name} />
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
          </div>
        </div>
      </div>

      {/* Page Title & Subtitle for subpages (if showPageTitle is true) */}
      {showPageTitle && pageTitle && (
        <div className="mt-1">
          <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
            {pageTitle}
          </h1>
          {subtitle && (
            <p className="text-xs text-[#717E95] font-medium mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      )}
    </header>
  )
}
