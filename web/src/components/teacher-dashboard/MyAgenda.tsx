import React, { useState } from 'react'
import { Users, User, ChevronRight } from 'lucide-react'

export interface AgendaItem {
  id: string
  title: string
  time: string
  type: 'group' | 'individual'
  avatars: string[]
  extraCount?: number
}

const DEFAULT_AGENDA: AgendaItem[] = [
  {
    id: 'ag-1',
    title: 'Case Review Meeting',
    time: '12:30 – 13:30',
    type: 'group',
    avatars: [
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
      'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=100&q=80',
    ],
    extraCount: 2,
  },
  {
    id: 'ag-2',
    title: '1-on-1 with Asha V.',
    time: '14:30 – 15:15',
    type: 'individual',
    avatars: [
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
    ],
  },
  {
    id: 'ag-3',
    title: '1-on-1 with Rohan M.',
    time: '16:30 – 17:00',
    type: 'individual',
    avatars: [
      'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=100&q=80',
    ],
  },
  {
    id: 'ag-4',
    title: 'Mentor Sync',
    time: '18:00 – 19:00',
    type: 'group',
    avatars: [
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80',
    ],
  },
]

const DAYS_OF_WEEK = [
  { day: 'Mo', date: 12 },
  { day: 'Tu', date: 13, isSelected: true },
  { day: 'We', date: 14 },
  { day: 'Th', date: 15 },
  { day: 'Fr', date: 16 },
  { day: 'Sa', date: 17 },
  { day: 'Su', date: 18 },
]

interface MyAgendaProps {
  agendaItems?: AgendaItem[]
  onViewAll?: () => void
  onAllUpcoming?: () => void
}

export function MyAgenda({
  agendaItems = DEFAULT_AGENDA,
  onViewAll,
  onAllUpcoming,
}: MyAgendaProps) {
  const [selectedDate, setSelectedDate] = useState(13)

  return (
    <div className="font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3">
        <h2 className="text-sm font-bold text-[#1E2433]">My Agenda</h2>
        <button
          onClick={onViewAll}
          className="text-xs font-medium text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      {/* Weekly Date Selector */}
      <div className="flex items-center justify-between gap-1 text-center py-1">
        {DAYS_OF_WEEK.map((d) => {
          const isSelected = d.date === selectedDate
          return (
            <button
              key={d.date}
              onClick={() => setSelectedDate(d.date)}
              className={`flex flex-col items-center justify-center py-1.5 px-2 rounded-2xl transition-all ${
                isSelected
                  ? 'bg-[#1E2433] text-white shadow-xs'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-white/60'
              }`}
            >
              <span className={`text-[10px] ${isSelected ? 'text-white/80' : 'text-[#94A3B8]'}`}>
                {d.day}
              </span>
              <span className="text-xs font-bold mt-0.5">
                {d.date}
              </span>
            </button>
          )
        })}
      </div>

      {/* Agenda Items */}
      <div className="mt-3.5 space-y-2">
        {agendaItems.map((item) => {
          const isGroup = item.type === 'group'
          const Icon = isGroup ? Users : User

          return (
            <div
              key={item.id}
              className="bg-white rounded-2xl p-2.5 px-3 flex items-center justify-between shadow-2xs border border-gray-100/50 hover:shadow-xs transition"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="flex items-center justify-center w-7 h-7 rounded-xl bg-gray-50 text-[#1E2433] shrink-0">
                  <Icon className="w-3.5 h-3.5 text-[#1E2433]" />
                </span>
                <div className="min-w-0">
                  <h3 className="text-xs font-bold text-[#1E2433] truncate leading-tight">
                    {item.title}
                  </h3>
                  <p className="text-[10px] text-[#717E95] font-medium mt-0.5">
                    {item.time}
                  </p>
                </div>
              </div>

              {/* Avatars on right */}
              <div className="flex items-center -space-x-1.5 shrink-0 ml-2">
                {item.avatars.map((url, i) => (
                  <img
                    key={i}
                    src={url}
                    alt="Attendee"
                    className="w-5 h-5 rounded-full object-cover border border-white"
                  />
                ))}
                {item.extraCount ? (
                  <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#1E2433] text-white text-[8px] font-bold border border-white">
                    +{item.extraCount}
                  </span>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom Action Button */}
      <button
        onClick={onAllUpcoming}
        className="w-full mt-4 py-2 px-3 rounded-2xl border border-gray-200/80 bg-white/70 hover:bg-white text-xs font-semibold text-[#1E2433] flex items-center justify-center gap-1.5 shadow-2xs transition hover:shadow-xs"
      >
        <span>All upcoming events</span>
        <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
      </button>
    </div>
  )
}

