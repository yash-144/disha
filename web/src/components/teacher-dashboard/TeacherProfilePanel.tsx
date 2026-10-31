import React, { useState } from 'react'
import { MoreHorizontal, ChevronDown } from 'lucide-react'
import { MyAgenda } from './MyAgenda'

interface TeacherProfilePanelProps {
  name?: string
  title?: string
  avatar?: string
  status?: string
}

export function TeacherProfilePanel({
  name = 'Prof. Sharma',
  title = 'Course Instructor',
  avatar = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
  status = 'Available',
}: TeacherProfilePanelProps) {
  const [currentStatus, setCurrentStatus] = useState(status)
  const [statusMenuOpen, setStatusMenuOpen] = useState(false)

  return (
    <aside className="w-72 shrink-0 bg-[#F1F3FA] rounded-3xl p-5 flex flex-col justify-between font-sans border border-gray-100/40">
      <div>
        {/* Top options dots */}
        <div className="flex justify-end">
          <button
            type="button"
            aria-label="Profile actions"
            className="text-gray-400 hover:text-[#1E2433] p-1 transition"
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>

        {/* Profile Card Center */}
        <div className="flex flex-col items-center -mt-2">
          <div className="relative">
            <img
              src={avatar}
              alt={name}
              className="w-18 h-18 rounded-full object-cover ring-4 ring-white shadow-xs"
            />
          </div>

          <h2 className="text-base font-bold text-[#1E2433] mt-2.5">
            {name}
          </h2>
          <p className="text-xs text-[#717E95] font-medium mt-0.5">
            {title}
          </p>

          {/* Availability Status Selector */}
          <div className="relative mt-2.5">
            <button
              onClick={() => setStatusMenuOpen(!statusMenuOpen)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-gray-200/60 shadow-2xs text-xs font-semibold text-[#1E2433] hover:bg-gray-50 transition"
            >
              <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
              <span>{currentStatus}</span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 ml-0.5" />
            </button>

            {statusMenuOpen && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-32 bg-white rounded-xl shadow-md border border-gray-100 py-1 z-20">
                {['Available', 'In Session', 'Offline'].map((st) => (
                  <button
                    key={st}
                    onClick={() => {
                      setCurrentStatus(st)
                      setStatusMenuOpen(false)
                    }}
                    className="w-full px-3 py-1 text-left text-xs font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {st}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* My Agenda Section */}
        <div className="mt-6 pt-5 border-t border-gray-200/50">
          <MyAgenda />
        </div>
      </div>
    </aside>
  )
}

