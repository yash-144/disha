import React, { useState } from 'react'
import {
  Users,
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  Download,
  Mail,
  UserPlus,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function RosterTab() {
  const { students, toggleStudentAttendance, addToast } = useApp()
  const [search, setSearch] = useState('')

  const filtered = students.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase())
  )

  const presentCount = students.filter((s) => s.status === 'Present').length
  const lateCount = students.filter((s) => s.status === 'Late').length
  const absentCount = students.filter((s) => s.status === 'Absent').length
  const attendancePercent = Math.round(((presentCount + lateCount * 0.5) / students.length) * 100)

  const handleExportCSV = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,Name,Email,Status,AttendanceRate,QuizScore\n' +
      students
        .map((s) => `${s.name},${s.email},${s.status},${s.attendanceRate}%,${s.quizScore}%`)
        .join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `skillsup-attendance-roster-${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    addToast('Roster Exported', 'Attendance CSV downloaded successfully.', 'success')
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Header and Summary Metrics */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0f9d58] px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              COHORT ROSTER
            </span>
            <span className="text-xs text-muted">({students.length} Learners)</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Roster &amp; Live Attendance Log</h2>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 border-2 border-ink bg-white px-3.5 py-2 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] hover:bg-gray-100"
          >
            <Download className="h-3.5 w-3.5 text-brand" /> Export CSV
          </button>
          <button
            onClick={() => addToast('Invite Generated', 'Cohort invitation link copied to clipboard.', 'info')}
            className="flex items-center gap-1.5 border-2 border-ink bg-[#0f9d58] px-4 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
          >
            <UserPlus className="h-4 w-4" /> Enroll Student
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-muted">Total Enrolled</p>
          <p className="mt-1 text-2xl font-bold text-ink">{students.length}</p>
        </div>
        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-[#0f9d58]">Present Today</p>
          <p className="mt-1 text-2xl font-bold text-[#0f9d58]">{presentCount}</p>
        </div>
        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-amber-600">Late Arrivals</p>
          <p className="mt-1 text-2xl font-bold text-amber-600">{lateCount}</p>
        </div>
        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-brand">Cohort Rate</p>
          <p className="mt-1 text-2xl font-bold text-brand">{attendancePercent}%</p>
        </div>
      </div>

      {/* Roster Table */}
      <div className="border-2 border-ink bg-white shadow-[4px_4px_0_#0d1b3e]">
        <div className="border-b-2 border-ink/20 p-4 flex items-center justify-between gap-4">
          <div className="flex items-center border-2 border-ink bg-[#f5f7fc] px-3 py-1.5 text-xs w-full max-w-xs shadow-[2px_2px_0_#0d1b3e]">
            <Search className="mr-2 h-3.5 w-3.5 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by student or email..."
              className="w-full bg-transparent outline-none text-xs font-bold text-ink"
            />
          </div>
          <span className="text-xs text-muted font-bold">{filtered.length} students</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#f5f7fc] border-b-2 border-ink text-[11px] font-bold text-ink uppercase">
              <tr>
                <th className="px-5 py-3">Student Name</th>
                <th className="px-5 py-3">Today's Attendance</th>
                <th className="px-5 py-3">Term Attendance</th>
                <th className="px-5 py-3">Quiz Score</th>
                <th className="px-5 py-3">Last Active</th>
                <th className="px-5 py-3 text-right">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink/10 font-bold text-ink">
              {filtered.map((s) => {
                const isPresent = s.status === 'Present'
                const isLate = s.status === 'Late'
                const isAbsent = s.status === 'Absent'

                return (
                  <tr key={s.id} className="hover:bg-blue-50/40 transition">
                    <td className="px-5 py-3.5 flex items-center gap-3">
                      <img
                        src={s.avatar}
                        alt={s.name}
                        className="h-8 w-8 border border-ink object-cover"
                      />
                      <div>
                        <p className="font-bold text-ink">{s.name}</p>
                        <p className="text-[10px] text-gray-500 font-normal">{s.email}</p>
                      </div>
                    </td>

                    <td className="px-5 py-3.5">
                      <button
                        onClick={() => toggleStudentAttendance(s.id)}
                        title="Click to toggle status"
                        className={`inline-flex items-center gap-1 border border-ink px-2.5 py-1 text-[10px] font-bold transition hover:scale-105 shadow-[1px_1px_0_#0d1b3e] ${
                          isPresent
                            ? 'bg-emerald-100 text-emerald-900'
                            : isLate
                            ? 'bg-amber-100 text-amber-900'
                            : 'bg-red-100 text-red-900'
                        }`}
                      >
                        {isPresent && <CheckCircle2 className="h-3 w-3 text-emerald-700" />}
                        {isLate && <Clock className="h-3 w-3 text-amber-700" />}
                        {isAbsent && <XCircle className="h-3 w-3 text-red-700" />}
                        <span>{s.status}</span>
                      </button>
                    </td>

                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-brand">{s.attendanceRate}%</span>
                        <div className="h-2 w-16 border border-ink bg-gray-100 overflow-hidden">
                          <div
                            className="h-full bg-brand"
                            style={{ width: `${s.attendanceRate}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-3.5">
                      <span className="font-bold text-[#0f9d58]">{s.quizScore}/100</span>
                    </td>

                    <td className="px-5 py-3.5 text-gray-500 text-[11px] font-mono">{s.lastActive}</td>

                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => addToast('Email Student', `Drafting message to ${s.email}...`, 'info')}
                        className="border border-ink bg-white p-1 text-ink shadow-[1px_1px_0_#0d1b3e] hover:bg-gray-100"
                        title="Send message"
                      >
                        <Mail className="h-3.5 w-3.5 text-brand" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
