import React from 'react'
import { Calendar, Users, ClipboardCheck } from 'lucide-react'

export interface UpcomingEvent {
  id: string
  title: string
  time: string
  iconType: 'calendar' | 'users' | 'assessment'
}

interface UpcomingTimelineProps {
  events: UpcomingEvent[]
}

export function UpcomingTimeline({ events }: UpcomingTimelineProps) {
  const getEventIcon = (type: UpcomingEvent['iconType']) => {
    switch (type) {
      case 'calendar':
        return <Calendar className="w-3.5 h-3.5 text-[#7C3AED]" />
      case 'users':
        return <Users className="w-3.5 h-3.5 text-[#6366F1]" />
      case 'assessment':
        return <ClipboardCheck className="w-3.5 h-3.5 text-[#8B5CF6]" />
      default:
        return <Calendar className="w-3.5 h-3.5 text-[#7C3AED]" />
    }
  }

  return (
    <div className="bg-white rounded-2xl p-4.5 border border-gray-100/90 shadow-2xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-3.5">
        <h3 className="text-sm font-bold text-[#1E2433]">Upcoming</h3>
        <button
          type="button"
          className="text-xs font-semibold text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      {/* Timeline Layout */}
      <div className="relative pl-6">
        {/* Continuous vertical timeline connector line */}
        <div className="absolute left-[11px] top-3 bottom-4 w-[2px] bg-[#DDD6FE]" />

        <div className="flex flex-col gap-4">
          {events.map((ev) => (
            <div key={ev.id} className="relative flex items-center justify-between group">
              {/* Timeline Node Icon */}
              <div className="absolute -left-6 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-[#F5F2FE] border-2 border-white shadow-2xs flex items-center justify-center z-10">
                {getEventIcon(ev.iconType)}
              </div>

              {/* Event Content */}
              <div className="pl-3">
                <p className="text-xs font-bold text-[#1E2433] group-hover:text-[#4338CA] transition-colors">
                  {ev.title}
                </p>
                <p className="text-[11px] text-[#717E95] mt-0.5 font-medium">
                  {ev.time}
                </p>
              </div>

              {/* Subtle badge or indicator */}
              <div className="w-2 h-2 rounded-full bg-[#C4B5FD] opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

