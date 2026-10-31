import React from 'react'
import { CircleHelp, Bell } from 'lucide-react'
import { RoleSwitcher } from '../common/RoleSwitcher'

interface TeacherHeaderProps {
  name?: string
  subtitle?: string
}

export function TeacherHeader({
  name = 'Prof. Sharma',
  subtitle = 'Course Instructor & Faculty Mentor at Apex University',
}: TeacherHeaderProps) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 font-sans select-none">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
          Welcome back, {name}!
        </h1>
        <p className="text-xs text-[#717E95] font-medium mt-1">
          {subtitle}
        </p>
      </div>

      <div className="flex items-center gap-2.5">
        {/* Role Switcher supporting all 4 portals */}
        <RoleSwitcher />

        {/* Help icon button */}
        <button
          type="button"
          aria-label="Help and resources"
          className="flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-sm transition cursor-pointer"
        >
          <CircleHelp className="w-4 h-4" />
        </button>

        {/* Notifications button with indicator */}
        <button
          type="button"
          aria-label="Notifications"
          className="relative flex items-center justify-center w-8 h-8 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-sm transition cursor-pointer"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
        </button>
      </div>
    </header>
  )
}


