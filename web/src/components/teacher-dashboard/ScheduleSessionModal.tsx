import React, { useState } from 'react'
import { X, Calendar, Clock, User, Bookmark } from 'lucide-react'

interface ScheduleSessionModalProps {
  isOpen: boolean
  onClose: () => void
  onSaveSession: (session: {
    title: string
    student: string
    date: string
    time: string
    type: 'mentor' | 'review' | '1-on-1' | 'intervention' | 'other'
  }) => void
}

export function ScheduleSessionModal({
  isOpen,
  onClose,
  onSaveSession,
}: ScheduleSessionModalProps) {
  const [title, setTitle] = useState('')
  const [student, setStudent] = useState('Asha Verma')
  const [date, setDate] = useState('2025-01-03')
  const [time, setTime] = useState('11:00 – 11:45')
  const [type, setType] = useState<'mentor' | 'review' | '1-on-1' | 'intervention' | 'other'>('mentor')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    onSaveSession({
      title,
      student,
      date,
      time,
      type,
    })
    setTitle('')
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs font-sans animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-white rounded-3xl p-6 shadow-xl border border-gray-100">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-[#1E2433]">Schedule a Session</h2>
            <p className="text-xs text-[#717E95] mt-0.5">
              Book a mentor meeting or intervention consultation
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-full text-gray-400 hover:text-black hover:bg-gray-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-[#1E2433] mb-1">
              Session Title
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Attendance & Labs Check-in"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
            />
          </div>

          {/* Student selection */}
          <div>
            <label className="block text-xs font-semibold text-[#1E2433] mb-1">
              Student / Attendee
            </label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
              <select
                value={student}
                onChange={(e) => setStudent(e.target.value)}
                className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-gray-200 text-xs text-[#1E2433] bg-white focus:outline-none focus:border-[#3B82F6]"
              >
                <option value="Asha Verma">Asha Verma (CS-2025)</option>
                <option value="Rohan Mehta">Rohan Mehta (CS-2025)</option>
                <option value="Neha Kapoor">Neha Kapoor (CS-2025)</option>
                <option value="Tanvi Verma">Tanvi Verma (CS-2025)</option>
                <option value="Faculty Advisory Group">Faculty Advisory Group</option>
              </select>
            </div>
          </div>

          {/* Session Type */}
          <div>
            <label className="block text-xs font-semibold text-[#1E2433] mb-1">
              Session Type
            </label>
            <div className="relative">
              <Bookmark className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
              <select
                value={type}
                onChange={(e) => setType(e.target.value as any)}
                className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-gray-200 text-xs text-[#1E2433] bg-white focus:outline-none focus:border-[#3B82F6]"
              >
                <option value="mentor">Mentor Check-in</option>
                <option value="review">Case Review</option>
                <option value="1-on-1">1-on-1 Consultation</option>
                <option value="intervention">Intervention Follow-up</option>
                <option value="other">Other Academic Session</option>
              </select>
            </div>
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#1E2433] mb-1">
                Date
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full pl-9 pr-2.5 py-2 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#1E2433] mb-1">
                Time Slot
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  placeholder="11:00 – 11:45"
                  className="w-full pl-9 pr-2.5 py-2 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-gray-600 hover:bg-gray-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-[#1E2433] text-white text-xs font-semibold hover:bg-[#2B3347] shadow-xs transition"
            >
              Confirm Session
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

