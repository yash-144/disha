import React, { useState } from 'react'
import {
  Users,
  AlertTriangle,
  Award,
  Search,
  Filter,
  CircleHelp,
  Bell,
  Mail,
  Calendar,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  CheckCircle,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

interface StudentDirectoryItem {
  id: string
  name: string
  dishaId: string
  email: string
  avatar: string
  cohort: string
  attendanceRate: number
  quizScoreAvg: number
  riskStatus: 'Attention Suggested' | 'Good Standing' | 'Under Review'
  activeInterventionsCount: number
}

const INITIAL_DIRECTORY_STUDENTS: StudentDirectoryItem[] = [
  {
    id: 'stud-1',
    name: 'Asha Verma',
    dishaId: 'DISHA-STU-8821',
    email: 'asha.verma@example.com',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-CS',
    attendanceRate: 72.0,
    quizScoreAvg: 78.5,
    riskStatus: 'Attention Suggested',
    activeInterventionsCount: 1,
  },
  {
    id: 'stud-2',
    name: 'Rohan Mehta',
    dishaId: 'DISHA-STU-4412',
    email: 'rohan.mehta@example.com',
    avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-CS',
    attendanceRate: 68.0,
    quizScoreAvg: 64.0,
    riskStatus: 'Attention Suggested',
    activeInterventionsCount: 1,
  },
  {
    id: 'stud-3',
    name: 'Neha Kapoor',
    dishaId: 'DISHA-STU-9923',
    email: 'neha.kapoor@example.com',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-CS',
    attendanceRate: 88.0,
    quizScoreAvg: 71.0,
    riskStatus: 'Under Review',
    activeInterventionsCount: 1,
  },
  {
    id: 'stud-4',
    name: 'Tanvi Verma',
    dishaId: 'DISHA-STU-3301',
    email: 'tanvi.verma@example.com',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-CS',
    attendanceRate: 98.0,
    quizScoreAvg: 94.5,
    riskStatus: 'Good Standing',
    activeInterventionsCount: 0,
  },
  {
    id: 'stud-5',
    name: 'Kabir Patel',
    dishaId: 'DISHA-STU-7719',
    email: 'kabir.patel@example.com',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-IT',
    attendanceRate: 94.0,
    quizScoreAvg: 89.0,
    riskStatus: 'Good Standing',
    activeInterventionsCount: 0,
  },
  {
    id: 'stud-6',
    name: 'Meera Iyer',
    dishaId: 'DISHA-STU-5542',
    email: 'meera.iyer@example.com',
    avatar: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=150&q=80',
    cohort: '2025-IT',
    attendanceRate: 96.0,
    quizScoreAvg: 92.0,
    riskStatus: 'Good Standing',
    activeInterventionsCount: 0,
  },
]

export function StudentDirectoryPage() {
  const { addToast } = useApp()
  const [students, setStudents] = useState<StudentDirectoryItem[]>(INITIAL_DIRECTORY_STUDENTS)
  const [selectedStudentId, setSelectedStudentId] = useState<string>('stud-1')
  const [selectedCohort, setSelectedCohort] = useState<string>('All')
  const [riskFilter, setRiskFilter] = useState<string>('All')
  const [searchQuery, setSearchQuery] = useState('')

  const activeStudent = students.find((s) => s.id === selectedStudentId) || students[0]

  const filteredStudents = students.filter((s) => {
    const matchesCohort = selectedCohort === 'All' || s.cohort === selectedCohort
    const matchesRisk =
      riskFilter === 'All' ||
      (riskFilter === 'Attention' && s.riskStatus === 'Attention Suggested') ||
      (riskFilter === 'Good' && s.riskStatus === 'Good Standing')

    const matchesSearch =
      !searchQuery ||
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.dishaId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.email.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesCohort && matchesRisk && matchesSearch
  })

  return (
    <>
      <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-1">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
              Student Directory
            </h1>
            <p className="text-xs text-[#717E95] font-medium mt-1">
              Roster overview, attendance trajectory, learning outcomes and risk signals
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              className="flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] transition"
            >
              <CircleHelp className="w-4 h-4" />
            </button>
            <button
              type="button"
              className="relative flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] transition"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
            </button>
            <img
              src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80"
              alt="Prof. Sharma"
              className="w-8 h-8 rounded-full object-cover ring-2 ring-white shadow-2xs ml-1"
            />
          </div>
        </header>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          <div className="bg-[#FDF2D5] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#614F23]">
              Total Students Monitored
            </span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">128</span>
              <span className="text-[11px] font-medium text-gray-500 ml-2">Across 2 Sections</span>
            </div>
          </div>

          <div className="bg-[#ECE8FB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#524077]">
              Attention Suggested
            </span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">14</span>
              <span className="text-[11px] font-bold text-[#7C3AED] ml-2">Needs intervention</span>
            </div>
          </div>

          <div className="bg-[#E5EEFB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#284873]">
              Cohort Attendance Rate
            </span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">92.4%</span>
              <span className="text-[11px] font-bold text-[#16A34A] ml-2">↑ +1.2% this month</span>
            </div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white rounded-2xl p-2.5 px-3.5 shadow-2xs border border-gray-100/70">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Cohort:</span>
            {['All', '2025-CS', '2025-IT'].map((cohort) => (
              <button
                key={cohort}
                onClick={() => setSelectedCohort(cohort)}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  selectedCohort === cohort
                    ? 'bg-[#1E2433] text-white font-semibold shadow-xs'
                    : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100'
                }`}
              >
                {cohort}
              </button>
            ))}

            <span className="text-gray-300 ml-1">|</span>

            {['All', 'Attention', 'Good'].map((rf) => (
              <button
                key={rf}
                onClick={() => setRiskFilter(rf)}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  riskFilter === rf
                    ? 'bg-[#1E2433] text-white font-semibold shadow-xs'
                    : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100'
                }`}
              >
                {rf}
              </button>
            ))}
          </div>

          <div className="relative min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search name, DISHA-ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
            />
          </div>
        </div>

        {/* Directory Table */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/70 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] font-semibold text-[#94A3B8]">
                  <th className="pb-2.5 font-medium">Student</th>
                  <th className="pb-2.5 font-medium">DISHA ID</th>
                  <th className="pb-2.5 font-medium">Cohort</th>
                  <th className="pb-2.5 font-medium">Attendance</th>
                  <th className="pb-2.5 font-medium">Quiz Avg</th>
                  <th className="pb-2.5 font-medium">Status Signal</th>
                  <th className="pb-2.5 font-medium text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredStudents.map((row) => {
                  const isSelected = row.id === activeStudent.id
                  const isLowAtt = row.attendanceRate < 75
                  const isMedAtt = row.attendanceRate >= 75 && row.attendanceRate < 85

                  return (
                    <tr
                      key={row.id}
                      onClick={() => setSelectedStudentId(row.id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-[#F4F6FD]' : 'hover:bg-gray-50/60'
                      }`}
                    >
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-2">
                          <img
                            src={row.avatar}
                            alt={row.name}
                            className="w-7 h-7 rounded-full object-cover shrink-0"
                          />
                          <div>
                            <p className="text-xs font-bold text-[#1E2433] leading-tight">
                              {row.name}
                            </p>
                            <span className="text-[10px] text-gray-400">
                              {row.email}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 text-xs font-mono text-[#505D75]">
                        {row.dishaId}
                      </td>
                      <td className="py-2.5 pr-3 text-xs text-[#505D75]">
                        {row.cohort}
                      </td>
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              style={{ width: `${row.attendanceRate}%` }}
                              className={`h-full rounded-full ${
                                isLowAtt ? 'bg-[#EF4444]' : isMedAtt ? 'bg-[#F59E0B]' : 'bg-[#22C55E]'
                              }`}
                            />
                          </div>
                          <span className={`text-xs font-bold ${
                            isLowAtt ? 'text-[#DC2626]' : isMedAtt ? 'text-[#D97706]' : 'text-[#16A34A]'
                          }`}>
                            {row.attendanceRate}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 text-xs font-bold text-[#1E2433]">
                        {row.quizScoreAvg}%
                      </td>
                      <td className="py-2.5 pr-3">
                        {row.riskStatus === 'Attention Suggested' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEE2E2] text-[#DC2626]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626] animate-pulse" />
                            Attention
                          </span>
                        ) : row.riskStatus === 'Under Review' ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#FEF3C7] text-[#D97706]">
                            Under Review
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#EAF7EE] text-[#16A34A]">
                            Good Standing
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 text-right">
                        <span className="inline-flex items-center text-xs font-semibold text-[#2563EB]">
                          View
                          <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Right-Side Student Spotlight Dossier Panel */}
      <aside className="w-76 xl:w-84 shrink-0 flex flex-col gap-3.5 font-sans">
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-xs font-mono font-bold text-gray-500">
                {activeStudent.dishaId}
              </span>
              <span className="text-[10px] font-semibold text-[#16A34A] bg-[#EAF7EE] px-2 py-0.5 rounded-full">
                Active Scholar
              </span>
            </div>

            {/* Profile Avatar Center */}
            <div className="flex flex-col items-center mt-3">
              <img
                src={activeStudent.avatar}
                alt={activeStudent.name}
                className="w-16 h-16 rounded-full object-cover ring-4 ring-gray-50 shadow-xs"
              />
              <h2 className="text-base font-bold text-[#1E2433] mt-2">
                {activeStudent.name}
              </h2>
              <p className="text-xs text-[#717E95] mt-0.5">
                Cohort: <span className="font-semibold text-[#1E2433]">{activeStudent.cohort}</span>
              </p>
            </div>

            {/* Attendance & Academics Snapshot */}
            <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-gray-100">
              <div className="bg-[#F8F9FD] p-2.5 rounded-2xl border border-gray-100">
                <span className="text-[10px] font-bold text-[#717E95] uppercase">Attendance</span>
                <p className={`text-lg font-bold mt-0.5 ${
                  activeStudent.attendanceRate < 75 ? 'text-red-600' : 'text-emerald-600'
                }`}>
                  {activeStudent.attendanceRate}%
                </p>
                <span className="text-[9px] text-gray-400">Benchmark: 75%</span>
              </div>

              <div className="bg-[#F8F9FD] p-2.5 rounded-2xl border border-gray-100">
                <span className="text-[10px] font-bold text-[#717E95] uppercase">Quiz Average</span>
                <p className="text-lg font-bold text-[#1E2433] mt-0.5">
                  {activeStudent.quizScoreAvg}%
                </p>
                <span className="text-[9px] text-gray-400">Class Rank: Top 25%</span>
              </div>
            </div>

            {/* Active Interventions Status */}
            <div className="mt-3.5 p-3 rounded-2xl bg-[#ECE8FB]/50 border border-[#ECE8FB]">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#524077]">
                <ShieldCheck className="w-4 h-4 text-[#7C3AED]" />
                <span>Intervention Status</span>
              </div>
              <p className="text-xs text-gray-700 mt-1">
                {activeStudent.activeInterventionsCount > 0
                  ? 'Currently assigned to Mentor Check-In & Lab Attendance Tracking.'
                  : 'No active risk cases. Student in good academic trajectory.'}
              </p>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2 mt-4 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => addToast('Session Invited', `Sent 1-on-1 calendar invite to ${activeStudent.name}.`, 'success')}
                className="w-full py-2.5 px-3 rounded-2xl bg-[#1E2433] text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs hover:bg-[#2B3347] transition"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Schedule 1-on-1 Consultation</span>
              </button>

              <button
                type="button"
                onClick={() => addToast('Signal Flagged', `Deterministic signal evaluation requested for ${activeStudent.name}.`, 'info')}
                className="w-full py-2.5 px-3 rounded-2xl bg-white border border-gray-200 text-[#1E2433] text-xs font-semibold flex items-center justify-center gap-2 shadow-2xs hover:bg-gray-50 transition"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-[#D97706]" />
                <span>Evaluate Academic Risk Signal</span>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

