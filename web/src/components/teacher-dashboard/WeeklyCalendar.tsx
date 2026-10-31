import React from 'react'

export interface CalendarEventItem {
  id: string
  title: string
  student?: string
  time: string
  dayIndex: number // 0: Mon, 1: Tue, ... 6: Sun
  startHour: number // e.g. 10.0 for 10:00, 12.5 for 12:30, 14.5 for 14:30, 18.0 for 18:00
  durationHours: number // e.g. 0.5 for 30m, 1.0 for 1h, 0.75 for 45m
  category: 'mentor' | 'review' | '1-on-1' | 'sync' | 'intervention' | 'other'
  color: 'blue' | 'purple' | 'green' | 'yellow'
}

export const INITIAL_CALENDAR_EVENTS: CalendarEventItem[] = [
  {
    id: 'evt-1',
    title: 'Mentor Check-in',
    student: 'Asha Verma',
    time: '10:00 – 10:30',
    dayIndex: 1, // Tuesday
    startHour: 10.0,
    durationHours: 0.8,
    category: 'mentor',
    color: 'blue',
  },
  {
    id: 'evt-2',
    title: 'Case Review',
    time: '12:30 – 13:30',
    dayIndex: 0, // Monday
    startHour: 12.5,
    durationHours: 1.0,
    category: 'review',
    color: 'purple',
  },
  {
    id: 'evt-3',
    title: '1-on-1',
    student: 'Rohan Mehta',
    time: '14:30 – 15:15',
    dayIndex: 1, // Tuesday
    startHour: 14.5,
    durationHours: 0.9,
    category: '1-on-1',
    color: 'green',
  },
  {
    id: 'evt-4',
    title: 'Mentor Sync',
    time: '18:00 – 19:00',
    dayIndex: 1, // Tuesday
    startHour: 18.0,
    durationHours: 1.0,
    category: 'sync',
    color: 'yellow',
  },
]

const DAYS = [
  { day: 'Mon', date: '01 Jan', index: 0 },
  { day: 'Tue', date: '02 Jan', index: 1, isSelected: true },
  { day: 'Wed', date: '03 Jan', index: 2 },
  { day: 'Thu', date: '04 Jan', index: 3 },
  { day: 'Fri', date: '05 Jan', index: 4 },
  { day: 'Sat', date: '06 Jan', index: 5 },
  { day: 'Sun', date: '07 Jan', index: 6 },
]

const TIME_SLOTS = [
  '09:00',
  '10:00',
  '11:00',
  '12:00',
  '13:00',
  '14:00',
  '15:00',
  '16:00',
  '17:00',
  '18:00',
  '19:00',
]

interface WeeklyCalendarProps {
  events?: CalendarEventItem[]
  selectedDayIndex?: number
  onSelectDay?: (dayIndex: number) => void
  onEventClick?: (event: CalendarEventItem) => void
}

export function WeeklyCalendar({
  events = INITIAL_CALENDAR_EVENTS,
  selectedDayIndex = 1,
  onSelectDay,
  onEventClick,
}: WeeklyCalendarProps) {
  const START_HOUR = 9 // 09:00
  const ROW_HEIGHT_PX = 46 // Height of each 1-hour slot in px

  const getColorStyles = (color: CalendarEventItem['color']) => {
    switch (color) {
      case 'blue':
        return {
          bg: 'bg-[#E1EFFF] border-l-4 border-l-[#3B82F6] text-[#1E3A8A]',
          title: 'text-[#1E3A8A]',
          subtitle: 'text-[#3B82F6]',
        }
      case 'purple':
        return {
          bg: 'bg-[#EDE8FC] border-l-4 border-l-[#8B5CF6] text-[#4C1D95]',
          title: 'text-[#4C1D95]',
          subtitle: 'text-[#7C3AED]',
        }
      case 'green':
        return {
          bg: 'bg-[#DCFCE7] border-l-4 border-l-[#22C55E] text-[#14532D]',
          title: 'text-[#14532D]',
          subtitle: 'text-[#16A34A]',
        }
      case 'yellow':
        return {
          bg: 'bg-[#FEF3C7] border-l-4 border-l-[#F59E0B] text-[#78350F]',
          title: 'text-[#78350F]',
          subtitle: 'text-[#B45309]',
        }
      default:
        return {
          bg: 'bg-gray-100 border-l-4 border-l-gray-400 text-gray-800',
          title: 'text-gray-900',
          subtitle: 'text-gray-600',
        }
    }
  }

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/70 font-sans overflow-hidden">
      <div className="overflow-x-auto">
        <div className="min-w-[640px]">
          {/* Days Header Row */}
          <div className="grid grid-cols-[60px_repeat(7,1fr)] items-center pb-3 border-b border-gray-100">
            <div className="text-[11px] font-medium text-gray-400 pl-1" />
            {DAYS.map((d) => {
              const isSelected = selectedDayIndex === d.index
              return (
                <div
                  key={d.day}
                  onClick={() => onSelectDay?.(d.index)}
                  className="flex flex-col items-center justify-center cursor-pointer transition-all"
                >
                  {isSelected ? (
                    <div className="bg-[#1E2433] text-white rounded-2xl px-3 py-1.5 shadow-xs flex flex-col items-center min-w-[58px]">
                      <span className="text-[11px] font-medium text-white/80">
                        {d.day}
                      </span>
                      <span className="text-xs font-bold text-white">
                        {d.date}
                      </span>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center py-1 hover:text-[#1E2433] text-[#64748B]">
                      <span className="text-[11px] font-semibold text-[#64748B]">
                        {d.day}
                      </span>
                      <span className="text-xs font-normal text-[#94A3B8] mt-0.5">
                        {d.date}
                      </span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Time Grid with Positioned Events */}
          <div className="relative grid grid-cols-[60px_repeat(7,1fr)]">
            {/* Time labels column */}
            <div className="relative">
              {TIME_SLOTS.map((slot) => (
                <div
                  key={slot}
                  style={{ height: `${ROW_HEIGHT_PX}px` }}
                  className="text-[11px] text-[#94A3B8] font-medium flex items-start pt-0"
                >
                  {slot}
                </div>
              ))}
            </div>

            {/* 7 Day Columns with Grid Lines */}
            {DAYS.map((d) => (
              <div
                key={d.day}
                className="relative border-l border-gray-100/90"
                style={{ height: `${TIME_SLOTS.length * ROW_HEIGHT_PX}px` }}
              >
                {/* Horizontal row divider lines */}
                {TIME_SLOTS.map((slot) => (
                  <div
                    key={slot}
                    style={{ height: `${ROW_HEIGHT_PX}px` }}
                    className="border-b border-gray-100/70"
                  />
                ))}

                {/* Events for this day */}
                {events
                  .filter((e) => e.dayIndex === d.index)
                  .map((evt) => {
                    const topOffset = (evt.startHour - START_HOUR) * ROW_HEIGHT_PX
                    const height = Math.max(evt.durationHours * ROW_HEIGHT_PX - 2, 38)
                    const styles = getColorStyles(evt.color)

                    return (
                      <div
                        key={evt.id}
                        onClick={() => onEventClick?.(evt)}
                        style={{
                          top: `${topOffset}px`,
                          height: `${height}px`,
                        }}
                        className={`absolute left-1 right-1 rounded-xl p-2 shadow-2xs cursor-pointer transition-all hover:scale-[1.02] hover:shadow-xs z-10 overflow-hidden flex flex-col justify-center ${styles.bg}`}
                      >
                        <p className={`text-[11px] font-bold leading-tight truncate ${styles.title}`}>
                          {evt.title}
                        </p>
                        {evt.student && (
                          <p className="text-[10px] text-gray-600 font-medium truncate mt-0.5">
                            {evt.student}
                          </p>
                        )}
                        <p className={`text-[9px] font-medium leading-none mt-0.5 ${styles.subtitle}`}>
                          {evt.time}
                        </p>
                      </div>
                    )
                  })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

