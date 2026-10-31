import React from 'react'
import { ChevronLeft, ChevronRight, ChevronDown, Check } from 'lucide-react'

export type ScheduleViewTab = 'my-schedule' | 'calls'
export type SessionCategory = 'all' | 'mentor' | 'review' | 'intervention' | 'other'

interface ScheduleToolbarProps {
  viewTab: ScheduleViewTab
  onViewTabChange: (tab: ScheduleViewTab) => void
  dateRangeLabel: string
  onPrevWeek: () => void
  onNextWeek: () => void
  onToday: () => void
  calendarView: 'week' | 'month'
  onCalendarViewChange: (v: 'week' | 'month') => void
  selectedCategory: SessionCategory
  onCategoryChange: (cat: SessionCategory) => void
}

export function ScheduleToolbar({
  viewTab,
  onViewTabChange,
  dateRangeLabel,
  onPrevWeek,
  onNextWeek,
  onToday,
  calendarView,
  onCalendarViewChange,
  selectedCategory,
  onCategoryChange,
}: ScheduleToolbarProps) {
  const categories: { id: SessionCategory; label: string }[] = [
    { id: 'all', label: 'All Sessions' },
    { id: 'mentor', label: 'Mentor Check-in' },
    { id: 'review', label: 'Case Review' },
    { id: 'intervention', label: 'Intervention' },
    { id: 'other', label: 'Other' },
  ]

  return (
    <div className="space-y-3 font-sans">
      {/* Top Toolbar Row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Segmented Toggle: My Schedule / Calls */}
        <div className="inline-flex items-center rounded-2xl bg-white p-1 border border-gray-100/80 shadow-2xs">
          <button
            type="button"
            onClick={() => onViewTabChange('my-schedule')}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              viewTab === 'my-schedule'
                ? 'bg-[#1E2433] text-white shadow-xs'
                : 'text-[#64748B] hover:text-[#1E2433]'
            }`}
          >
            My Schedule
          </button>
          <button
            type="button"
            onClick={() => onViewTabChange('calls')}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              viewTab === 'calls'
                ? 'bg-[#1E2433] text-white shadow-xs'
                : 'text-[#64748B] hover:text-[#1E2433]'
            }`}
          >
            Calls
          </button>
        </div>

        {/* Date Navigation & View Selector */}
        <div className="flex items-center gap-2">
          {/* Week range navigation */}
          <div className="inline-flex items-center gap-2 bg-white rounded-2xl px-2.5 py-1.5 border border-gray-100/80 shadow-2xs">
            <button
              type="button"
              onClick={onPrevWeek}
              aria-label="Previous week"
              className="p-1 rounded-lg text-gray-500 hover:text-[#1E2433] hover:bg-gray-50 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-bold text-[#1E2433] px-1">
              {dateRangeLabel}
            </span>
            <button
              type="button"
              onClick={onNextWeek}
              aria-label="Next week"
              className="p-1 rounded-lg text-gray-500 hover:text-[#1E2433] hover:bg-gray-50 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Week/Month Selector Dropdown */}
          <button
            type="button"
            onClick={() => onCalendarViewChange(calendarView === 'week' ? 'month' : 'week')}
            className="inline-flex items-center gap-1.5 bg-white rounded-2xl px-3 py-1.5 border border-gray-100/80 text-xs font-semibold text-[#1E2433] shadow-2xs hover:bg-gray-50 transition"
          >
            <span>{calendarView === 'week' ? 'Week' : 'Month'}</span>
            <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          </button>

          {/* Today Button */}
          <button
            type="button"
            onClick={onToday}
            className="bg-white rounded-2xl px-3.5 py-1.5 border border-gray-100/80 text-xs font-semibold text-[#1E2433] shadow-2xs hover:bg-gray-50 transition"
          >
            Today
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 pt-0.5">
        {categories.map((cat) => {
          const isSelected = selectedCategory === cat.id
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onCategoryChange(cat.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isSelected
                  ? 'bg-[#1E2433] text-white font-semibold shadow-xs'
                  : 'bg-transparent text-[#64748B] hover:text-[#1E2433] hover:bg-white/60'
              }`}
            >
              {isSelected && <Check className="w-3 h-3 stroke-[2.5]" />}
              <span>{cat.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

