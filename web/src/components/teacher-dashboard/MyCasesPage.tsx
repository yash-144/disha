import React, { useState } from 'react'
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  Search,
  Filter,
  ArrowUpRight,
  Clock,
  User,
  ShieldAlert,
  ChevronRight,
  Plus,
  Send,
  CircleHelp,
  Bell,
  Check,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

interface CaseItem {
  id: string
  caseNumber: string
  student: {
    id: string
    name: string
    avatar: string
    cohort: string
  }
  intervention: string
  priority: 'High' | 'Medium' | 'Low'
  state: 'Open' | 'In Progress' | 'Escalated' | 'Closed'
  dueDate: string
  dueDays: number
  lastNote: string
  tasks: { id: string; label: string; done: boolean }[]
}

const INITIAL_CASES: CaseItem[] = [
  {
    id: 'case-1',
    caseNumber: 'CASE-2025-081',
    student: {
      id: 'stud-1',
      name: 'Asha Verma',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
      cohort: '2025-CS',
    },
    intervention: 'Mentor Check-in',
    priority: 'High',
    state: 'In Progress',
    dueDate: '14 Oct, 17:30',
    dueDays: 1,
    lastNote: 'Met student in office; agreed on makeup lab attendance schedule.',
    tasks: [
      { id: 't1', label: 'Conduct 1-on-1 Attendance & Syllabus Review', done: true },
      { id: 't2', label: 'Monitor week 44 lab submissions', done: false },
      { id: 't3', label: 'Sign off on restored 80% attendance benchmark', done: false },
    ],
  },
  {
    id: 'case-2',
    caseNumber: 'CASE-2025-082',
    student: {
      id: 'stud-2',
      name: 'Rohan Mehta',
      avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
      cohort: '2025-CS',
    },
    intervention: 'CBT & Stress Reduction',
    priority: 'High',
    state: 'Escalated',
    dueDate: '15 Oct, 14:00',
    dueDays: 2,
    lastNote: 'Escalated to student counselling cell for specialized exam anxiety coping plan.',
    tasks: [
      { id: 't4', label: 'Referral to university psychological counsellor', done: true },
      { id: 't5', label: 'Weekly pulse sentiment monitor review', done: false },
    ],
  },
  {
    id: 'case-3',
    caseNumber: 'CASE-2025-083',
    student: {
      id: 'stud-3',
      name: 'Neha Kapoor',
      avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
      cohort: '2025-CS',
    },
    intervention: 'Academic Tutoring Support',
    priority: 'Medium',
    state: 'Open',
    dueDate: '16 Oct, 11:00',
    dueDays: 3,
    lastNote: 'Pending diagnostic review of unit 2 data structures quiz score.',
    tasks: [
      { id: 't6', label: 'Pair with student peer tutor for recursion practice', done: false },
      { id: 't7', label: 'Re-attempt quiz 2 formative questions', done: false },
    ],
  },
  {
    id: 'case-4',
    caseNumber: 'CASE-2025-078',
    student: {
      id: 'stud-4',
      name: 'Tanvi Verma',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
      cohort: '2025-CS',
    },
    intervention: 'Attendance Remediation',
    priority: 'Low',
    state: 'Closed',
    dueDate: '10 Oct, 12:00',
    dueDays: 0,
    lastNote: 'Completed all makeup sessions. Attendance restored to 84%. Case concluded.',
    tasks: [
      { id: 't8', label: 'Complete 3 makeup lab exercises', done: true },
      { id: 't9', label: 'Faculty sign-off and outcome filing', done: true },
    ],
  },
]

export function MyCasesPage() {
  const { addToast } = useApp()
  const [cases, setCases] = useState<CaseItem[]>(INITIAL_CASES)
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case-1')
  const [filterPriority, setFilterPriority] = useState<string>('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [newFollowUpNote, setNewFollowUpNote] = useState('')

  const activeCase = cases.find((c) => c.id === selectedCaseId) || cases[0]

  const filteredCases = cases.filter((c) => {
    const matchesPriority =
      filterPriority === 'All' ||
      (filterPriority === 'High' && c.priority === 'High') ||
      (filterPriority === 'In Progress' && c.state === 'In Progress') ||
      (filterPriority === 'Escalated' && c.state === 'Escalated') ||
      (filterPriority === 'Closed' && c.state === 'Closed')

    const matchesSearch =
      !searchQuery ||
      c.student.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.caseNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.intervention.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesPriority && matchesSearch
  })

  const toggleTask = (taskId: string) => {
    if (!activeCase) return
    setCases((prev) =>
      prev.map((c) => {
        if (c.id !== activeCase.id) return c
        return {
          ...c,
          tasks: c.tasks.map((t) => (t.id === taskId ? { ...t, done: !t.done } : t)),
        }
      })
    )
  }

  const handleAddFollowUp = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newFollowUpNote.trim()) return

    setCases((prev) =>
      prev.map((c) => {
        if (c.id !== activeCase.id) return c
        return {
          ...c,
          lastNote: newFollowUpNote,
          state: c.state === 'Open' ? 'In Progress' : c.state,
        }
      })
    )
    addToast('Follow-Up Logged', 'Staff attestation added with cryptographic timestamp.', 'success')
    setNewFollowUpNote('')
  }

  const handleCloseCase = () => {
    setCases((prev) =>
      prev.map((c) => {
        if (c.id !== activeCase.id) return c
        return { ...c, state: 'Closed' }
      })
    )
    addToast('Case Concluded', `Marked ${activeCase.caseNumber} as resolved with academic evidence.`, 'success')
  }

  const getPriorityBadge = (p: CaseItem['priority']) => {
    switch (p) {
      case 'High':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEE2E2] text-[#DC2626]">High</span>
      case 'Medium':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF3C7] text-[#D97706]">Medium</span>
      case 'Low':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E0EDFD] text-[#2563EB]">Low</span>
    }
  }

  const getStatePill = (st: CaseItem['state']) => {
    switch (st) {
      case 'In Progress':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#EBF3FC] text-[#2563EB]">In Progress</span>
      case 'Escalated':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#FEE2E2] text-[#DC2626]">Escalated</span>
      case 'Closed':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#EAF7EE] text-[#16A34A]">Closed</span>
      case 'Open':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-700">Open</span>
    }
  }

  return (
    <>
      <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-1">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
              My Cases
            </h1>
            <p className="text-xs text-[#717E95] font-medium mt-1">
              Active student interventions, action checklists, and monitored outcomes
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

        {/* 3 Pastel Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          <div className="bg-[#FDF2D5] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#614F23]">Active Support Cases</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">18</span>
              <span className="text-[11px] font-bold text-[#16A34A] ml-2">↑ +3 this week</span>
            </div>
          </div>

          <div className="bg-[#FEE2E2]/70 rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#DC2626]">High Priority Attention</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">6</span>
              <span className="text-[11px] font-medium text-gray-500 ml-2">Need action &lt;48h</span>
            </div>
          </div>

          <div className="bg-[#E6F8EE] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#16A34A]">Successfully Resolved</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">12</span>
              <span className="text-[11px] font-medium text-gray-500 ml-2">This semester</span>
            </div>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white rounded-2xl p-2.5 px-3.5 shadow-2xs border border-gray-100/70">
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
            {['All', 'High', 'In Progress', 'Escalated', 'Closed'].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setFilterPriority(tab)}
                className={`px-3 py-1.5 rounded-full font-medium transition ${
                  filterPriority === tab
                    ? 'bg-[#1E2433] text-white font-semibold shadow-xs'
                    : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="relative min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search case, student..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
            />
          </div>
        </div>

        {/* Cases List Table */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/70 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] font-semibold text-[#94A3B8]">
                  <th className="pb-2.5 font-medium">Case Ref</th>
                  <th className="pb-2.5 font-medium">Student</th>
                  <th className="pb-2.5 font-medium">Intervention</th>
                  <th className="pb-2.5 font-medium">Priority</th>
                  <th className="pb-2.5 font-medium">Status</th>
                  <th className="pb-2.5 font-medium">Due Date</th>
                  <th className="pb-2.5 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredCases.map((row) => {
                  const isSelected = row.id === activeCase.id
                  return (
                    <tr
                      key={row.id}
                      onClick={() => setSelectedCaseId(row.id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-[#F4F6FD]' : 'hover:bg-gray-50/60'
                      }`}
                    >
                      <td className="py-3 pr-3 text-xs font-mono font-bold text-[#1E2433]">
                        {row.caseNumber}
                      </td>
                      <td className="py-3 pr-3">
                        <div className="flex items-center gap-2">
                          <img
                            src={row.student.avatar}
                            alt={row.student.name}
                            className="w-6 h-6 rounded-full object-cover shrink-0"
                          />
                          <div>
                            <p className="text-xs font-bold text-[#1E2433] leading-tight">
                              {row.student.name}
                            </p>
                            <span className="text-[10px] text-gray-400 font-mono">
                              {row.student.cohort}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 pr-3 text-xs text-[#505D75]">
                        {row.intervention}
                      </td>
                      <td className="py-3 pr-3">
                        {getPriorityBadge(row.priority)}
                      </td>
                      <td className="py-3 pr-3">
                        {getStatePill(row.state)}
                      </td>
                      <td className="py-3 pr-3 text-xs text-[#505D75]">
                        {row.dueDate}
                      </td>
                      <td className="py-3 text-right">
                        <span className="inline-flex items-center text-xs font-semibold text-[#2563EB]">
                          Inspect
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

      {/* Right-Side Case Inspector & Action Console */}
      <aside className="w-76 xl:w-84 shrink-0 flex flex-col gap-3.5 font-sans">
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-xs font-mono font-bold text-[#2563EB] bg-[#EBF3FC] px-2.5 py-0.5 rounded-full">
                {activeCase.caseNumber}
              </span>
              {getPriorityBadge(activeCase.priority)}
            </div>

            {/* Student Dossier Header */}
            <div className="flex items-center gap-3 mt-3.5">
              <img
                src={activeCase.student.avatar}
                alt={activeCase.student.name}
                className="w-11 h-11 rounded-full object-cover ring-2 ring-gray-100"
              />
              <div>
                <h3 className="text-sm font-bold text-[#1E2433]">
                  {activeCase.student.name}
                </h3>
                <p className="text-xs text-[#717E95]">
                  Plan: <span className="font-semibold text-[#1E2433]">{activeCase.intervention}</span>
                </p>
              </div>
            </div>

            {/* Action Tasks Checklist */}
            <div className="mt-4 pt-3 border-t border-gray-100">
              <h4 className="text-xs font-bold text-[#1E2433] mb-2">
                Intervention Task Checklist
              </h4>
              <div className="space-y-1.5">
                {activeCase.tasks.map((task) => (
                  <label
                    key={task.id}
                    onClick={() => toggleTask(task.id)}
                    className="flex items-start gap-2 p-2 rounded-xl bg-gray-50/70 hover:bg-gray-100 cursor-pointer transition text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={task.done}
                      readOnly
                      className="mt-0.5 rounded text-[#2563EB] focus:ring-0"
                    />
                    <span className={`leading-tight ${task.done ? 'line-through text-gray-400' : 'text-gray-700 font-medium'}`}>
                      {task.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Latest Attestation Note */}
            <div className="mt-3.5 p-3 rounded-2xl bg-[#F8F9FD] border border-gray-100">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#717E95] uppercase">
                <Clock className="w-3 h-3" />
                <span>Last Attestation Note</span>
              </div>
              <p className="text-xs text-gray-700 mt-1 italic">
                "{activeCase.lastNote}"
              </p>
            </div>

            {/* Quick Follow-up Logger Form */}
            <form onSubmit={handleAddFollowUp} className="mt-4">
              <label className="block text-[11px] font-bold text-[#1E2433] mb-1">
                Log New Follow-Up Note
              </label>
              <textarea
                rows={2}
                placeholder="Met student; reviewed quiz corrections..."
                value={newFollowUpNote}
                onChange={(e) => setNewFollowUpNote(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
              />
              <button
                type="submit"
                className="w-full mt-2 py-2 rounded-xl bg-[#1E2433] text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-2xs hover:bg-[#2B3347] transition"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Append Follow-Up</span>
              </button>
            </form>
          </div>

          {/* Close Case Outcome CTA */}
          <div className="mt-4 pt-3 border-t border-gray-100">
            {activeCase.state === 'Closed' ? (
              <div className="w-full py-2 px-3 rounded-xl bg-[#EAF7EE] text-[#16A34A] text-xs font-bold text-center">
                ✓ Case Resolved &amp; Concluded
              </div>
            ) : (
              <button
                type="button"
                onClick={handleCloseCase}
                className="w-full py-2 px-3 rounded-xl border border-[#16A34A] bg-[#EAF7EE] text-[#16A34A] hover:bg-[#DCFCE7] text-xs font-bold transition flex items-center justify-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5 stroke-[3]" />
                <span>Conclude Case with Outcome</span>
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

