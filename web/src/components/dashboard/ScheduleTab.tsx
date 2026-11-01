import React, { useState } from 'react'
import { Calendar as CalendarIcon, Clock, Plus, Users, Video } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const SESSIONS = [
  {
    id: 1,
    day: 'Mon',
    time: '10:00 AM - 11:30 AM',
    title: 'React 19 Server Components & Hooks',
    course: 'Full-Stack Web Dev',
    color: 'border-l-4 border-l-brand bg-white',
    badge: 'bg-brand text-white',
    students: 28,
  },
  {
    id: 2,
    day: 'Tue',
    time: '2:00 PM - 3:30 PM',
    title: 'PostgreSQL Query Execution Planning',
    course: 'Database Engineering',
    color: 'border-l-4 border-l-accent bg-white',
    badge: 'bg-accent text-white',
    students: 24,
  },
  {
    id: 3,
    day: 'Wed',
    time: '11:00 AM - 12:30 PM',
    title: 'Figma Auto-Layout & Design Tokens Handoff',
    course: 'UI/UX Design',
    color: 'border-l-4 border-l-purple-600 bg-white',
    badge: 'bg-purple-600 text-white',
    students: 31,
  },
  {
    id: 4,
    day: 'Thu',
    time: '4:00 PM - 5:30 PM',
    title: 'AWS VPC Architecture & Security Groups',
    course: 'Cloud Solutions',
    color: 'border-l-4 border-l-amber-500 bg-white',
    badge: 'bg-amber-500 text-white',
    students: 22,
  },
  {
    id: 5,
    day: 'Fri',
    time: '12:30 PM - 2:00 PM',
    title: 'Collaborative Live Whiteboard Demo',
    course: 'Interactive Workshop',
    color: 'border-l-4 border-l-brand bg-white',
    badge: 'bg-brand text-white',
    students: 35,
  },
  {
    id: 6,
    day: 'Sat',
    time: '11:00 AM - 1:00 PM',
    title: 'Capstone Project Code Review & Q&A',
    course: 'Weekend Cohort',
    color: 'border-l-4 border-l-accent bg-white',
    badge: 'bg-accent text-white',
    students: 40,
  },
]

export function ScheduleTab() {
  const { addToast } = useApp()
  const [selectedDay, setSelectedDay] = useState<string>('All')

  const filtered =
    selectedDay === 'All' ? SESSIONS : SESSIONS.filter((s) => s.day === selectedDay)

  return (
    <div className="space-y-6 font-mono">
      <div className="flex flex-wrap items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              COHORT TIMETABLE
            </span>
            <span className="text-xs text-muted">(UTC+05:30 IST)</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Weekly Live Schedule</h2>
        </div>

        <button
          onClick={() => addToast('Schedule Event', 'Interactive calendar slot picker opened.', 'info')}
          className="flex items-center gap-1.5 border-2 border-ink bg-accent px-4 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
        >
          <Plus className="h-4 w-4" /> Add Schedule Slot
        </button>
      </div>

      {/* Days Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        {['All', ...WEEK_DAYS].map((day) => (
          <button
            key={day}
            onClick={() => setSelectedDay(day)}
            className={`border-2 border-ink px-4 py-1.5 text-xs font-bold transition shadow-[2px_2px_0_#0d1b3e] ${
              selectedDay === day
                ? 'bg-brand text-white -translate-y-0.5'
                : 'bg-white text-ink hover:bg-gray-100'
            }`}
          >
            {day}
          </button>
        ))}
      </div>

      {/* Sessions Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((s) => (
          <div
            key={s.id}
            className={`flex flex-col justify-between border-2 border-ink p-4 shadow-[3px_3px_0_#0d1b3e] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_#0d1b3e] ${s.color}`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className={`border border-ink px-2 py-0.5 text-xs font-bold shadow-[1px_1px_0_#0d1b3e] ${s.badge}`}>
                  {s.day} DAY
                </span>
                <span className="flex items-center gap-1 text-xs font-bold text-gray-600">
                  <Clock className="h-3 w-3 text-brand" /> {s.time}
                </span>
              </div>

              <h3 className="mt-3 text-sm font-bold leading-snug text-ink">{s.title}</h3>
              <p className="mt-1 text-xs text-muted">{s.course}</p>
            </div>

            <div className="mt-4 border-t border-ink/10 pt-3 flex items-center justify-between">
              <span className="flex items-center gap-1 text-xs font-bold text-accent">
                <Users className="h-3.5 w-3.5" /> {s.students} Enrolled
              </span>
              <button
                onClick={() => addToast('Connecting Stream', `Joining live session room: "${s.title}".`, 'info')}
                className="flex items-center gap-1 border border-ink bg-accent px-2.5 py-1 text-xs font-bold text-white shadow-[1px_1px_0_#0d1b3e] hover:bg-accent-dark"
              >
                <Video className="h-3 w-3" /> Join Room
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
