import React from 'react'
import { ArrowUp } from 'lucide-react'

interface MyCasesProps {
  totalCases?: number
  weeklyDelta?: number
  highPriorityCount?: number
  onViewAll?: () => void
}

export function MyCases({
  totalCases = 18,
  weeklyDelta = 3,
  highPriorityCount = 6,
  onViewAll,
}: MyCasesProps) {
  const caseAvatars = [
    'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=120&q=80',
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&q=80',
    'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80',
  ]

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/60 font-sans flex flex-col justify-between">
      <div className="flex items-center justify-between pb-2">
        <h2 className="text-sm font-bold text-[#1E2433]">My Cases</h2>
        <button
          onClick={onViewAll}
          className="text-xs font-medium text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      {/* Metric & Trend */}
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-3xl font-bold tracking-tight text-[#1E2433]">
          {totalCases}
        </span>
        <span className="flex items-center gap-0.5 text-xs font-bold text-[#16A34A]">
          <ArrowUp className="w-3.5 h-3.5" />
          +{weeklyDelta} this week
        </span>
      </div>

      {/* High priority notice */}
      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-50">
        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#FEE2E2] text-[#DC2626] text-[10px] font-bold shrink-0">
          {highPriorityCount}
        </span>
        <span className="text-xs font-semibold text-[#1E2433]">
          high priority cases
        </span>
      </div>

      {/* Avatars Stack */}
      <div className="flex items-center justify-between mt-3 pt-1">
        <div className="flex items-center -space-x-2">
          {caseAvatars.map((url, i) => (
            <img
              key={i}
              src={url}
              alt="Student"
              className="w-7 h-7 rounded-full object-cover border-2 border-white ring-1 ring-gray-100"
            />
          ))}
        </div>
        <span className="flex items-center justify-center px-2 py-0.5 rounded-full bg-[#F1F3F9] text-[#64748B] text-[10px] font-bold border border-gray-100">
          +15
        </span>
      </div>
    </div>
  )
}

