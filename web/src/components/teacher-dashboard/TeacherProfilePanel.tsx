import React from 'react'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { UserAvatar } from '../common/UserAvatar'
import { useSessionsList } from '../../lib/api/endpoints/sessions.hooks'
import { Calendar, Clock, Video, MapPin } from 'lucide-react'

export function TeacherProfilePanel() {
  const { user, role } = useSession()
  const { data: sessions = [], isLoading } = useSessionsList()

  const upcomingSessions = sessions
    .filter((s) => s.status === 'scheduled')
    .slice(0, 3)

  return (
    <aside className="w-72 shrink-0 bg-[#F1F3FA] rounded-3xl p-5 flex flex-col gap-5 font-sans border border-gray-100/40">
      <div className="flex flex-col items-center">
        <UserAvatar name={user?.full_name} />
        <h2 className="text-base font-bold text-[#1E2433] mt-2.5">{user?.full_name}</h2>
        <p className="text-xs text-[#717E95] font-medium mt-0.5">{role ? roleLabel(role) : ''}</p>
      </div>

      {/* Agenda Section */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-blue-600" />
            <span>Consultation Agenda</span>
          </h3>
          <span className="text-[11px] font-semibold text-blue-600">
            {upcomingSessions.length} upcoming
          </span>
        </div>

        {isLoading ? (
          <p className="text-xs text-gray-400 py-3 text-center">Loading agenda...</p>
        ) : upcomingSessions.length === 0 ? (
          <div className="p-4 bg-white/70 rounded-2xl text-center text-xs text-gray-500 border border-gray-100">
            <p className="font-medium text-gray-700">No calls scheduled</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Office hours are open</p>
          </div>
        ) : (
          <div className="space-y-2">
            {upcomingSessions.map((s) => {
              const d = new Date(s.scheduled_at)
              const timeStr = d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
              const dateStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

              return (
                <div
                  key={s.id}
                  className="p-3 bg-white rounded-2xl border border-gray-100 shadow-2xs text-xs space-y-1"
                >
                  <p className="font-bold text-gray-900 truncate">
                    {s.student_name || `Student ${s.student_id.slice(0, 8)}`}
                  </p>
                  <div className="flex items-center justify-between text-[11px] text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-gray-400" />
                      {dateStr} • {timeStr}
                    </span>
                    <span className="capitalize text-blue-600 font-medium">
                      {s.mode.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </aside>
  )
}
