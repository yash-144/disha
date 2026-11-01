import React from 'react'
import { Calendar, Clock } from 'lucide-react'
import { useSessionsList } from '../../lib/api/endpoints/sessions.hooks'

export function UpcomingSessionsCard({ onViewSchedule }: { onViewSchedule?: () => void }) {
  const { data: sessions = [], isLoading } = useSessionsList()
  const scheduled = sessions.filter((s) => s.status === 'scheduled')

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-line font-sans flex flex-col justify-between">
      <div className="flex items-center justify-between pb-2">
        <h2 className="text-sm font-bold text-ink flex items-center gap-1.5">
          <Calendar className="w-4 h-4 text-blue-600" />
          <span>Consultations &amp; Office Hours</span>
        </h2>
        <button
          type="button"
          onClick={onViewSchedule}
          className="text-xs font-medium text-muted hover:text-ink transition"
        >
          View schedule
        </button>
      </div>

      {isLoading ? (
        <p className="text-xs text-muted">Loading schedule...</p>
      ) : (
        <div>
          <span className="text-3xl font-bold tracking-tight text-ink">
            {scheduled.length}
          </span>
          <p className="text-xs text-muted mt-0.5">
            {scheduled.length === 1
              ? '1 upcoming appointment'
              : `${scheduled.length} upcoming appointments`}
          </p>
        </div>
      )}
    </div>
  )
}

