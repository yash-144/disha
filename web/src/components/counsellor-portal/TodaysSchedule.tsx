import React from 'react'
import { ArrowRight, Video } from 'lucide-react'
import { CounsellorAppointment } from './counsellorDemoData'

interface TodaysScheduleProps {
  schedule: CounsellorAppointment[]
  onViewCalendar?: () => void
  onSelectAppointment?: (app: CounsellorAppointment) => void
}

export function TodaysSchedule({
  schedule,
  onViewCalendar,
  onSelectAppointment,
}: TodaysScheduleProps) {
  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col justify-between font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-[#1E2433]">Today's Schedule</h3>

        {onViewCalendar && (
          <button
            type="button"
            onClick={onViewCalendar}
            className="inline-flex items-center gap-1 text-xs font-semibold text-purple-700 hover:text-purple-900 transition cursor-pointer"
          >
            <span>View Calendar</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Timeline List */}
      <div className="relative flex flex-col gap-3.5 pl-2">
        {schedule.map((item, idx) => (
          <div
            key={item.id}
            onClick={() => onSelectAppointment?.(item)}
            className="relative flex items-center justify-between py-1 group cursor-pointer"
          >
            {/* Left Timeline: Time + Connecting Dot */}
            <div className="flex items-center gap-3">
              {/* Time */}
              <span className="text-xs font-mono font-bold text-[#64748B] w-12 shrink-0">
                {item.time}
              </span>

              {/* Vertical node line & purple dot */}
              <div className="relative flex flex-col items-center">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6] ring-4 ring-[#EDE9FE] shrink-0" />
                {idx < schedule.length - 1 && (
                  <span className="absolute top-2.5 w-[2px] h-8 bg-[#E2E8F0]" />
                )}
              </div>

              {/* Event Content */}
              <div className="ml-2">
                <h4 className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition leading-tight">
                  {item.title}
                </h4>
                <p className="text-[11px] text-[#717E95] font-medium mt-0.5">
                  {item.studentName}
                </p>
              </div>
            </div>

            {/* Right: Video Session Icon */}
            <div className="w-8 h-8 rounded-xl bg-purple-50 text-[#8B5CF6] group-hover:bg-purple-100 flex items-center justify-center shrink-0 transition">
              <Video className="w-4 h-4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

