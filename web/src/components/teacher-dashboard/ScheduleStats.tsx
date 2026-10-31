import React from 'react'

interface ScheduleStatsProps {
  todaySessions?: number
  upcomingCalls?: number
  pendingRequests?: number
}

export function ScheduleStats({
  todaySessions = 4,
  upcomingCalls = 7,
  pendingRequests = 2,
}: ScheduleStatsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 font-sans">
      {/* Today's Sessions - Pastel Yellow */}
      <div className="bg-[#FDF2D5] rounded-2xl p-4 flex flex-col justify-between shadow-2xs transition-transform hover:-translate-y-0.5 duration-150">
        <span className="text-xs font-bold text-[#614F23]">
          Today's Sessions
        </span>
        <div className="mt-3">
          <span className="text-3xl font-bold tracking-tight text-[#1E2433]">
            {todaySessions}
          </span>
        </div>
      </div>

      {/* Upcoming Calls - Pastel Blue */}
      <div className="bg-[#E5EEFB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs transition-transform hover:-translate-y-0.5 duration-150">
        <span className="text-xs font-bold text-[#284873]">
          Upcoming Calls
        </span>
        <div className="mt-3">
          <span className="text-3xl font-bold tracking-tight text-[#1E2433]">
            {upcomingCalls}
          </span>
        </div>
      </div>

      {/* Pending Requests - Pastel Purple */}
      <div className="bg-[#ECE8FB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs transition-transform hover:-translate-y-0.5 duration-150">
        <span className="text-xs font-bold text-[#524077]">
          Pending Requests
        </span>
        <div className="mt-3">
          <span className="text-3xl font-bold tracking-tight text-[#1E2433]">
            {pendingRequests}
          </span>
        </div>
      </div>
    </div>
  )
}
