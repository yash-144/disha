import React from 'react'
import { CircleHelp, Bell } from 'lucide-react'
import { RoleSwitcher } from '../common/RoleSwitcher'
import { ADMIN_USER } from '../../mockData'

interface AdminHeaderProps {
  pageTitle?: string
  subtitle?: string
}

export function AdminHeader({ pageTitle, subtitle }: AdminHeaderProps) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 font-sans select-none">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
          {pageTitle || `Welcome, ${ADMIN_USER.name}!`}
        </h1>
        <p className="text-xs text-[#717E95] font-medium mt-1">
          {subtitle || ADMIN_USER.title}
        </p>
      </div>

      <div className="flex items-center gap-2.5">
        {/* Role Switcher across all 4 portals */}
        <RoleSwitcher />

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
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
        </button>

        {/* Profile Avatar */}
        <div className="relative ml-0.5">
          <img
            src={ADMIN_USER.avatar}
            alt={ADMIN_USER.name}
            className="w-8 h-8 rounded-full object-cover ring-2 ring-white shadow-2xs"
          />
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
        </div>
      </div>
    </header>
  )
}

