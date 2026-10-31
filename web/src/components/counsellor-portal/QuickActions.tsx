import React from 'react'
import {
  FileText,
  Calendar,
  UserPlus,
  ClipboardCheck,
  ChevronRight,
} from 'lucide-react'

interface QuickActionsProps {
  onCreateSupportCase?: () => void
  onScheduleSession?: () => void
  onAddToWatchlist?: () => void
  onLogFollowUp?: () => void
}

export function QuickActions({
  onCreateSupportCase,
  onScheduleSession,
  onAddToWatchlist,
  onLogFollowUp,
}: QuickActionsProps) {
  const actions = [
    {
      id: 'create-case',
      label: 'Create Support Case',
      icon: FileText,
      iconBg: 'bg-[#F3E8FF]',
      iconColor: 'text-[#7C3AED]',
      onClick: onCreateSupportCase,
    },
    {
      id: 'schedule-session',
      label: 'Schedule a Session',
      icon: Calendar,
      iconBg: 'bg-[#EDE9FE]',
      iconColor: 'text-[#6366F1]',
      onClick: onScheduleSession,
    },
    {
      id: 'add-watchlist',
      label: 'Add Student to Watchlist',
      icon: UserPlus,
      iconBg: 'bg-[#E0F2FE]',
      iconColor: 'text-[#0284C7]',
      onClick: onAddToWatchlist,
    },
    {
      id: 'log-followup',
      label: 'Log a Follow-up',
      icon: ClipboardCheck,
      iconBg: 'bg-[#F5F3FF]',
      iconColor: 'text-[#8B5CF6]',
      onClick: onLogFollowUp,
    },
  ]

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col font-sans select-none">
      <h3 className="text-sm font-bold text-[#1E2433] mb-3">Quick Actions</h3>

      <div className="flex flex-col gap-2">
        {actions.map((act) => {
          const Icon = act.icon

          return (
            <button
              key={act.id}
              type="button"
              onClick={act.onClick}
              className="w-full flex items-center justify-between p-2.5 rounded-2xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/30 transition text-left group cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-8 h-8 rounded-xl ${act.iconBg} ${act.iconColor} flex items-center justify-center shrink-0`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition leading-tight">
                  {act.label}
                </span>
              </div>

              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#1E2433] group-hover:translate-x-0.5 transition" />
            </button>
          )
        })}
      </div>
    </div>
  )
}

