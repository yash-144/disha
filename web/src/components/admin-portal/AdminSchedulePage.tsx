import React, { useState } from 'react'
import {
  Calendar as CalendarIcon,
  Clock,
  Video,
  MapPin,
  Users,
  Plus,
  Filter,
  CheckCircle2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
  Search,
} from 'lucide-react'
import { INITIAL_APPOINTMENTS, AppointmentRecord } from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminSchedulePage() {
  const { addToast } = useApp()
  const [appointments, setAppointments] = useState<AppointmentRecord[]>(INITIAL_APPOINTMENTS)
  const [viewMode, setViewMode] = useState<'week' | 'month' | 'agenda'>('agenda')
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [isModalOpen, setIsModalOpen] = useState(false)

  // New Appointment Form state
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState<AppointmentRecord['category']>('case_review')
  const [staffName, setStaffName] = useState('Prof. Sharma (Faculty)')
  const [participantName, setParticipantName] = useState('')
  const [dateTime, setDateTime] = useState('Tomorrow, 02:00 PM')
  const [mode, setMode] = useState<'virtual' | 'in_person'>('virtual')
  const [roomOrLink, setRoomOrLink] = useState('DISHA Secure Room #Alpha')

  const filteredAppointments = appointments.filter((app) => {
    if (filterCategory === 'all') return true
    return app.category === filterCategory
  })

  const handleCreateAppointment = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !participantName.trim()) {
      addToast('Missing Fields', 'Please specify the review session title and participants.', 'info')
      return
    }

    const newApp: AppointmentRecord = {
      id: `app-${Date.now()}`,
      title,
      category,
      staffName,
      staffRole: 'Institutional Lead',
      participantName,
      dateTime,
      durationMinutes: 45,
      status: 'confirmed',
      mode,
      roomOrLink,
    }

    setAppointments([newApp, ...appointments])
    setIsModalOpen(false)
    setTitle('')
    setParticipantName('')
    addToast('Review Scheduled', `Session "${title}" successfully placed on the campus calendar.`, 'success')
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. CALENDAR TOOLBAR & CONTROLS */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
            <CalendarIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Institutional Schedule &amp; Case Syncs
            </h2>
            <p className="text-xs text-[#717E95]">
              Coordinate welfare committee sessions, faculty briefings, and counsellor check-ins
            </p>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 p-1 rounded-full text-xs font-semibold">
            {(['agenda', 'week', 'month'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1 rounded-full transition capitalize cursor-pointer ${
                  viewMode === mode
                    ? 'bg-white text-[#1E2433] shadow-xs font-bold'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Schedule Session Button */}
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Schedule Review</span>
          </button>
        </div>
      </section>

      {/* 2. FILTER STRIP & TIMEFRAME */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: 'all', label: 'All Reviews' },
            { id: 'case_review', label: 'Case Conferences' },
            { id: 'emergency_escalation', label: 'Emergency Syncs' },
            { id: 'counselling', label: 'Counselling Consultations' },
          ].map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setFilterCategory(cat.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition cursor-pointer whitespace-nowrap ${
                filterCategory === cat.id
                  ? 'bg-purple-100 text-purple-900 font-bold'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-gray-600 self-end sm:self-auto">
          <span>Term: Autumn 2025 · Week 7</span>
        </div>
      </div>

      {/* 3. SESSIONS LIST & STAFF AVAILABILITY PANEL */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Scheduled Sessions (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-3">
          {filteredAppointments.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-3xl border border-gray-100 shadow-2xs">
              <CalendarIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-gray-500">No scheduled sessions matching filter.</p>
            </div>
          ) : (
            filteredAppointments.map((app) => (
              <div
                key={app.id}
                className="bg-white rounded-2xl border border-gray-100/90 shadow-2xs p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:shadow-xs transition"
              >
                <div className="flex items-start gap-3.5">
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 ${
                    app.category === 'emergency_escalation'
                      ? 'bg-rose-50 text-rose-600 border border-rose-100'
                      : app.category === 'counselling'
                      ? 'bg-blue-50 text-blue-600 border border-blue-100'
                      : 'bg-purple-50 text-purple-600 border border-purple-100'
                  }`}>
                    {app.mode === 'virtual' ? <Video className="w-5 h-5" /> : <MapPin className="w-5 h-5" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-[#1E2433]">{app.title}</h4>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        app.category === 'emergency_escalation'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-gray-100 text-gray-700 border-gray-200'
                      }`}>
                        {app.category.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    <p className="text-xs text-[#64748B] mt-1">
                      Lead: <strong className="text-gray-800">{app.staffName}</strong> • Participants: {app.participantName}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-gray-500 mt-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        <span>{app.dateTime} ({app.durationMinutes} min)</span>
                      </span>
                      <span className="flex items-center gap-1 font-mono text-purple-700">
                        {app.roomOrLink}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    type="button"
                    onClick={() => addToast('Joining Room', `Connecting to ${app.roomOrLink}...`, 'info')}
                    className="px-4 py-2 rounded-full text-xs font-bold bg-[#1E2433] hover:bg-[#2C3549] text-white transition shadow-xs cursor-pointer"
                  >
                    Enter Room
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Staff Availability Roster (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5">
            <h3 className="text-sm font-bold text-[#1E2433] tracking-tight mb-3 flex items-center justify-between">
              <span>Staff Availability Monitor</span>
              <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100 font-semibold">
                Live Roster
              </span>
            </h3>

            <div className="divide-y divide-gray-100 text-xs">
              {[
                { name: 'Prof. Sharma', role: 'Faculty Mentor (CS)', status: 'available', statusColor: 'bg-emerald-500' },
                { name: 'Dr. Rao', role: 'Senior Counsellor', status: 'in_session', statusColor: 'bg-amber-500' },
                { name: 'Meera K.', role: 'Wellbeing Specialist', status: 'available', statusColor: 'bg-emerald-500' },
                { name: 'Dr. Mukherjee', role: 'HOD Mechanical', status: 'away', statusColor: 'bg-gray-400' },
              ].map((staff) => (
                <div key={staff.name} className="py-2.5 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-[#1E2433] block">{staff.name}</span>
                    <span className="text-[11px] text-[#717E95]">{staff.role}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${staff.statusColor}`} />
                    <span className="text-[11px] font-semibold capitalize text-gray-700">
                      {staff.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-gray-500 leading-relaxed">
              Counseling availability schedules are synchronized in accordance with institutional on-call duty requirements.
            </div>
          </div>
        </div>
      </div>

      {/* SCHEDULE REVIEW MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <CalendarIcon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Schedule Review / Sync Session</h3>
                  <p className="text-[11px] text-[#717E95]">Institutional case coordination</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateAppointment} className="p-5 flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Session Title *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Midterm Persistence Review - Mechanical Dept"
                  className="p-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="p-2.5 rounded-xl border border-gray-200 bg-white"
                  >
                    <option value="case_review">Case Conference</option>
                    <option value="emergency_escalation">Emergency Escalation</option>
                    <option value="counselling">Counselling Session</option>
                    <option value="mentor_sync">Mentor Briefing</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Staff Lead</label>
                  <select
                    value={staffName}
                    onChange={(e) => setStaffName(e.target.value)}
                    className="p-2.5 rounded-xl border border-gray-200 bg-white"
                  >
                    <option value="Prof. Sharma (Faculty)">Prof. Sharma (Faculty)</option>
                    <option value="Dr. Rao (Counsellor)">Dr. Rao (Counsellor)</option>
                    <option value="Dr. V. Raman (Admin)">Dr. V. Raman (Admin)</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Attendees / Participants *</label>
                <input
                  type="text"
                  value={participantName}
                  onChange={(e) => setParticipantName(e.target.value)}
                  placeholder="e.g. Student Welfare Committee, Asha Verma"
                  className="p-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Date & Time</label>
                  <input
                    type="text"
                    value={dateTime}
                    onChange={(e) => setDateTime(e.target.value)}
                    className="p-2.5 rounded-xl border border-gray-200"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Room / Link</label>
                  <input
                    type="text"
                    value={roomOrLink}
                    onChange={(e) => setRoomOrLink(e.target.value)}
                    className="p-2.5 rounded-xl border border-gray-200"
                  />
                </div>
              </div>

              <div className="p-4 bg-gray-50 border-t border-gray-100 -mx-5 -mb-5 mt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-full font-bold text-white bg-[#1E2433] hover:bg-[#2C3549] transition"
                >
                  Confirm Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

