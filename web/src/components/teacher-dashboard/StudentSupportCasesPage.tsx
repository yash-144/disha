import React, { useState, useMemo } from 'react'
import {
  Users,
  Flag,
  Clock,
  CheckCircle2,
  CircleHelp,
  Bell,
  Search,
  ChevronDown,
  ChevronRight,
  Filter,
  SlidersHorizontal,
  FileText,
  Target,
  Calendar,
  MoreVertical,
  Check,
  X,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  User,
  Sparkles,
  RefreshCw,
  Plus,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export interface CaseMilestone {
  id: number
  title: string
  status: 'completed' | 'current' | 'upcoming'
}

export interface StudentCase {
  id: string
  name: string
  program: string
  concern: string
  priority: 'High' | 'Medium' | 'Low'
  status: 'In Progress' | 'Under Review' | 'Scheduled' | 'Resolved'
  avatar: string
  summary: string
  openedDate: string
  lastUpdate: string
  assignedTo: string
  progressPercent: number
  completedMilestones: number
  totalMilestones: number
  milestones: CaseMilestone[]
  nextAction: string
  nextActionDate: string
  isAssignedToMe: boolean
  needsAction: boolean
  tasks: { id: string; text: string; done: boolean; dueDate: string }[]
  notes: { id: string; author: string; date: string; text: string }[]
  timeline: { id: string; event: string; date: string; icon: string }[]
}

const INITIAL_CASES: StudentCase[] = [
  {
    id: 'CASE-1027',
    name: 'Asha Verma',
    program: 'B.Tech (CSE) • 3rd Year',
    concern: 'Academic Stress',
    priority: 'High',
    status: 'In Progress',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
    summary: 'Showing signs of elevated academic stress with possible impact on sleep and mood.',
    openedDate: '08 Oct, 2025',
    lastUpdate: '12 Oct, 2025',
    assignedTo: 'Prof. Sharma (You)',
    progressPercent: 50,
    completedMilestones: 2,
    totalMilestones: 4,
    milestones: [
      { id: 1, title: 'Initial\nCheck-in', status: 'completed' },
      { id: 2, title: 'Plan\nCreated', status: 'completed' },
      { id: 3, title: 'Intervention\n(ongoing)', status: 'current' },
      { id: 4, title: 'Review\n& Close', status: 'upcoming' },
    ],
    nextAction: 'Follow-up session',
    nextActionDate: '14 Oct, 17:30',
    isAssignedToMe: true,
    needsAction: true,
    tasks: [
      { id: 't1', text: 'Conduct 1-on-1 Attendance & Syllabus Review Session', done: true, dueDate: '10 Oct' },
      { id: 't2', text: 'Coordinate with CSE course coordinator for assignment extension', done: true, dueDate: '12 Oct' },
      { id: 't3', text: 'Evaluate mid-term stress reflection report', done: false, dueDate: '14 Oct' },
      { id: 't4', text: 'Schedule peer study mentor introduction call', done: false, dueDate: '16 Oct' },
    ],
    notes: [
      { id: 'n1', author: 'Prof. Sharma', date: '12 Oct, 14:15', text: 'Student reported feeling significantly more grounded after revising the weekly milestone targets. Agreed on lighter load for upcoming week.' },
      { id: 'n2', author: 'Academic Counselor', date: '08 Oct, 11:30', text: 'Initial check-in completed. Suggested sleep hygiene adjustments and academic workload balancing.' },
    ],
    timeline: [
      { id: 'tl1', event: 'Follow-up scheduled with Prof. Sharma', date: '12 Oct, 2025', icon: 'calendar' },
      { id: 'tl2', event: 'Workload rebalancing plan finalized', date: '10 Oct, 2025', icon: 'file' },
      { id: 'tl3', event: 'Case initiated from early warning signal', date: '08 Oct, 2025', icon: 'flag' },
    ],
  },
  {
    id: 'CASE-0984',
    name: 'Rohan Mehta',
    program: 'B.Tech (ECE) • 2nd Year',
    concern: 'Anxiety Concerns',
    priority: 'Medium',
    status: 'Under Review',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
    summary: 'Expressed feeling overwhelmed prior to mid-term assessments. Needs study scheduling support and testing accommodations.',
    openedDate: '05 Oct, 2025',
    lastUpdate: '11 Oct, 2025',
    assignedTo: 'Prof. Sharma (You)',
    progressPercent: 25,
    completedMilestones: 1,
    totalMilestones: 4,
    milestones: [
      { id: 1, title: 'Initial\nCheck-in', status: 'completed' },
      { id: 2, title: 'Plan\nCreated', status: 'current' },
      { id: 3, title: 'Intervention\n(ongoing)', status: 'upcoming' },
      { id: 4, title: 'Review\n& Close', status: 'upcoming' },
    ],
    nextAction: 'Counselor Call Sync',
    nextActionDate: '15 Oct, 11:00',
    isAssignedToMe: true,
    needsAction: true,
    tasks: [
      { id: 't2-1', text: 'Review initial wellbeing survey responses', done: true, dueDate: '07 Oct' },
      { id: 't2-2', text: 'Draft individualized test schedule adjustment', done: false, dueDate: '15 Oct' },
    ],
    notes: [
      { id: 'n2-1', author: 'Prof. Sharma', date: '11 Oct, 16:00', text: 'Student is attentive in class but exhibits test performance paralysis. Coordinating with student wellbeing desk.' },
    ],
    timeline: [
      { id: 'tl2-1', event: 'Test accommodation draft shared', date: '11 Oct, 2025', icon: 'file' },
      { id: 'tl2-2', event: 'Case opened upon faculty review', date: '05 Oct, 2025', icon: 'flag' },
    ],
  },
  {
    id: 'CASE-0971',
    name: 'Neha Kapoor',
    program: 'B.Sc (Data Science) • 1st Year',
    concern: 'Adjustment Challenges',
    priority: 'Medium',
    status: 'In Progress',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    summary: 'First-generation university student navigating campus transition, hostel acclimation, and attendance routines.',
    openedDate: '02 Oct, 2025',
    lastUpdate: '10 Oct, 2025',
    assignedTo: 'Prof. Sharma (You)',
    progressPercent: 50,
    completedMilestones: 2,
    totalMilestones: 4,
    milestones: [
      { id: 1, title: 'Initial\nCheck-in', status: 'completed' },
      { id: 2, title: 'Plan\nCreated', status: 'completed' },
      { id: 3, title: 'Intervention\n(ongoing)', status: 'current' },
      { id: 4, title: 'Review\n& Close', status: 'upcoming' },
    ],
    nextAction: 'Peer Mentor Connect',
    nextActionDate: '16 Oct, 14:00',
    isAssignedToMe: true,
    needsAction: false,
    tasks: [
      { id: 't3-1', text: 'Assign 3rd year peer mentor buddy', done: true, dueDate: '05 Oct' },
      { id: 't3-2', text: 'Connect with academic tutoring lab', done: true, dueDate: '09 Oct' },
      { id: 't3-3', text: 'Check mid-month lab presence', done: false, dueDate: '16 Oct' },
    ],
    notes: [
      { id: 'n3-1', author: 'Prof. Sharma', date: '10 Oct, 13:00', text: 'Attendance has improved from 68% to 78% over the past two weeks. Student feels more comfortable in team coding assignments.' },
    ],
    timeline: [
      { id: 'tl3-1', event: 'Peer buddy connection confirmed', date: '10 Oct, 2025', icon: 'user' },
      { id: 'tl3-2', event: 'First intake conversation', date: '02 Oct, 2025', icon: 'flag' },
    ],
  },
  {
    id: 'CASE-0956',
    name: 'Arjun Singh',
    program: 'B.Tech (ME) • 4th Year',
    concern: 'Wellbeing Check-in',
    priority: 'Low',
    status: 'Scheduled',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80',
    summary: 'Routine semester check-in on final year capstone project deadlines and placement preparation balance.',
    openedDate: '29 Sep, 2025',
    lastUpdate: '08 Oct, 2025',
    assignedTo: 'Prof. Sharma (You)',
    progressPercent: 25,
    completedMilestones: 1,
    totalMilestones: 4,
    milestones: [
      { id: 1, title: 'Initial\nCheck-in', status: 'completed' },
      { id: 2, title: 'Plan\nCreated', status: 'current' },
      { id: 3, title: 'Intervention\n(ongoing)', status: 'upcoming' },
      { id: 4, title: 'Review\n& Close', status: 'upcoming' },
    ],
    nextAction: 'Introductory Mentorship Call',
    nextActionDate: '18 Oct, 16:30',
    isAssignedToMe: false,
    needsAction: false,
    tasks: [
      { id: 't4-1', text: 'Review capstone project milestone document', done: true, dueDate: '04 Oct' },
      { id: 't4-2', text: 'Conduct preliminary check-in', done: false, dueDate: '18 Oct' },
    ],
    notes: [
      { id: 'n4-1', author: 'Mentor Lead', date: '08 Oct, 15:45', text: 'Requested guidance on time management between lab submissions and technical interview practice.' },
    ],
    timeline: [
      { id: 'tl4-1', event: 'Session scheduled on faculty calendar', date: '08 Oct, 2025', icon: 'calendar' },
      { id: 'tl4-2', event: 'Request submitted via student portal', date: '29 Sep, 2025', icon: 'flag' },
    ],
  },
  {
    id: 'CASE-0948',
    name: 'Kavya Iyer',
    program: 'B.Tech (CSE) • 2nd Year',
    concern: 'Peer Concerns',
    priority: 'Low',
    status: 'In Progress',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
    summary: 'Requested faculty advice regarding collaborative lab group dynamics, role division, and group project participation.',
    openedDate: '25 Sep, 2025',
    lastUpdate: '07 Oct, 2025',
    assignedTo: 'Prof. Sharma (You)',
    progressPercent: 75,
    completedMilestones: 3,
    totalMilestones: 4,
    milestones: [
      { id: 1, title: 'Initial\nCheck-in', status: 'completed' },
      { id: 2, title: 'Plan\nCreated', status: 'completed' },
      { id: 3, title: 'Intervention\n(ongoing)', status: 'completed' },
      { id: 4, title: 'Review\n& Close', status: 'current' },
    ],
    nextAction: 'Final Lab Evaluation Review',
    nextActionDate: '20 Oct, 10:00',
    isAssignedToMe: true,
    needsAction: false,
    tasks: [
      { id: 't5-1', text: 'Meet with lab team leads', done: true, dueDate: '28 Sep' },
      { id: 't5-2', text: 'Re-align project milestone responsibilities', done: true, dueDate: '02 Oct' },
      { id: 't5-3', text: 'Review mid-sprint commit contributions', done: true, dueDate: '06 Oct' },
      { id: 't5-4', text: 'Final case resolution sign-off', done: false, dueDate: '20 Oct' },
    ],
    notes: [
      { id: 'n5-1', author: 'Prof. Sharma', date: '07 Oct, 10:30', text: 'Lab group reported smooth coordination in the latest sprint. Project git repo shows balanced commit history.' },
    ],
    timeline: [
      { id: 'tl5-1', event: 'Milestone 3 marked as accomplished', date: '07 Oct, 2025', icon: 'check' },
      { id: 'tl5-2', event: 'Lab group mediation session held', date: '01 Oct, 2025', icon: 'calendar' },
    ],
  },
]

export function StudentSupportCasesPage() {
  const { addToast } = useApp()
  const [cases, setCases] = useState<StudentCase[]>(INITIAL_CASES)
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-1027')
  const [filterScope, setFilterScope] = useState<'all' | 'my' | 'needsAction'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [detailTab, setDetailTab] = useState<'Overview' | 'Interventions' | 'Tasks' | 'Notes' | 'Timeline'>('Overview')
  const [isFullModalOpen, setIsFullModalOpen] = useState(false)
  const [newNoteText, setNewNoteText] = useState('')

  // Selected Case Object
  const selectedCase = useMemo(() => {
    return cases.find((c) => c.id === selectedCaseId) || cases[0]
  }, [cases, selectedCaseId])

  // Filtered Cases List
  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      // Tab scope filter
      if (filterScope === 'my' && !c.isAssignedToMe) return false
      if (filterScope === 'needsAction' && !c.needsAction) return false

      // Status filter
      if (statusFilter !== 'all' && c.status.toLowerCase() !== statusFilter.toLowerCase()) return false

      // Priority filter
      if (priorityFilter !== 'all' && c.priority.toLowerCase() !== priorityFilter.toLowerCase()) return false

      // Search query (student name, case reference, concern)
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim()
        const matchesName = c.name.toLowerCase().includes(query)
        const matchesRef = c.id.toLowerCase().includes(query)
        const matchesConcern = c.concern.toLowerCase().includes(query)
        const matchesProgram = c.program.toLowerCase().includes(query)
        return matchesName || matchesRef || matchesConcern || matchesProgram
      }

      return true
    })
  }, [cases, filterScope, statusFilter, priorityFilter, searchQuery])

  // Quick Status Updater
  const handleUpdateStatus = (newStatus: StudentCase['status']) => {
    setCases((prev) =>
      prev.map((c) => (c.id === selectedCase.id ? { ...c, status: newStatus } : c))
    )
    addToast('Status Updated', `Case ${selectedCase.id} is now ${newStatus}.`, 'success')
  }

  // Toggle Task in Selected Case
  const handleToggleTask = (taskId: string) => {
    setCases((prev) =>
      prev.map((c) => {
        if (c.id !== selectedCase.id) return c
        return {
          ...c,
          tasks: c.tasks.map((t) => (t.id === taskId ? { ...t, done: !t.done } : t)),
        }
      })
    )
  }

  // Add Note to Selected Case
  const handleAddNote = () => {
    if (!newNoteText.trim()) return
    const newNote = {
      id: `n-${Date.now()}`,
      author: 'Prof. Sharma (You)',
      date: 'Just now',
      text: newNoteText.trim(),
    }
    setCases((prev) =>
      prev.map((c) => (c.id === selectedCase.id ? { ...c, notes: [newNote, ...c.notes] } : c))
    )
    setNewNoteText('')
    addToast('Note Saved', 'Observation note added to case record.', 'success')
  }

  return (
    <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
      {/* ------------------------------------------------------------- */}
      {/* 1. Page Header */}
      {/* ------------------------------------------------------------- */}
      <header className="flex items-center justify-between pb-1">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#1E2433]">
            Student Support Cases
          </h1>
          <p className="text-xs text-[#717E95] font-medium mt-1">
            Review active student cases, task assignments, and intervention milestones.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Help Button */}
          <button
            type="button"
            aria-label="Help and documentation"
            className="flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-2xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition cursor-pointer"
            onClick={() => addToast('Case Guidance', 'Cases are initiated from risk signals or faculty escalations.', 'info')}
          >
            <CircleHelp className="w-4 h-4" />
          </button>

          {/* Notifications Button */}
          <button
            type="button"
            aria-label="Case notifications"
            className="relative flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-2xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-xs transition cursor-pointer"
            onClick={() => addToast('Notifications', 'You have 3 case milestones approaching deadline.', 'info')}
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
          </button>

          {/* Teacher Profile Avatar */}
          <img
            src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80"
            alt="Prof. Sharma"
            className="w-8 h-8 rounded-full object-cover ring-2 ring-white shadow-2xs ml-1"
          />
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* 2. Top Stats & Case Trend Row */}
      {/* ------------------------------------------------------------- */}
      <section aria-label="Case statistics summary" className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Card 1: Active Cases */}
        <div className="bg-[#FFF9EE] rounded-2xl p-4 border border-[#FEEFCA] flex flex-col justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-[#FEF08A]/60 text-[#B45309] flex items-center justify-center shrink-0">
              <Users className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-[#6E5D38]">Active Cases</span>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-black text-[#1E2433] tracking-tight">18</span>
            <span className="text-[11px] font-semibold text-[#16A34A] flex items-center gap-0.5">
              ↑ +3 this week
            </span>
          </div>
        </div>

        {/* Card 2: High Priority */}
        <div className="bg-[#FFF1F2] rounded-2xl p-4 border border-[#FFE4E6] flex flex-col justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-[#FECDD3]/70 text-[#E11D48] flex items-center justify-center shrink-0">
              <Flag className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-[#9F1239]">High Priority</span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-black text-[#1E2433] tracking-tight">6</span>
          </div>
        </div>

        {/* Card 3: Under Intervention */}
        <div className="bg-[#F0F7FF] rounded-2xl p-4 border border-[#E0F2FE] flex flex-col justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-[#BAE6FD]/60 text-[#0284C7] flex items-center justify-center shrink-0">
              <Clock className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-[#0369A1]">Under Intervention</span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-black text-[#1E2433] tracking-tight">9</span>
          </div>
        </div>

        {/* Card 4: Resolved (This Month) */}
        <div className="bg-[#F0FDF4] rounded-2xl p-4 border border-[#DCFCE7] flex flex-col justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-[#BBF7D0]/60 text-[#16A34A] flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-[#166534]">Resolved (This Month)</span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-black text-[#1E2433] tracking-tight">12</span>
          </div>
        </div>

        {/* Card 5: Case Trend (Right Column) */}
        <div className="col-span-2 md:col-span-1 bg-white rounded-2xl p-4 border border-gray-100/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#1E2433]">Case Trend</span>
            <span className="text-[11px] font-semibold text-[#16A34A] flex items-center gap-0.5">
              ↑ +25% vs last month
            </span>
          </div>

          {/* Elegant 9-bar upward trend chart matching reference */}
          <div className="mt-2.5 flex items-end justify-between gap-1 h-8 px-1">
            {[18, 28, 38, 50, 62, 75, 86, 94, 100].map((heightPercent, idx) => (
              <div
                key={idx}
                className="flex-1 bg-gradient-to-t from-[#8B5CF6] to-[#C4B5FD] rounded-full transition-all duration-300 hover:brightness-110"
                style={{ height: `${heightPercent}%` }}
                title={`Week ${idx + 1}: ${heightPercent}% activity`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 3. Search and Filter Toolbar */}
      {/* ------------------------------------------------------------- */}
      <section aria-label="Search and filters" className="bg-white rounded-2xl p-2.5 sm:p-3 border border-gray-100/90 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="flex items-center gap-2.5 flex-1 w-full pl-2">
          <Search className="w-4 h-4 text-[#94A3B8] shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by student name, case reference or concern..."
            className="w-full text-xs text-[#1E2433] placeholder-[#94A3B8] bg-transparent outline-none font-medium"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-gray-400 hover:text-gray-600 p-0.5 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Right Dropdown Filters */}
        <div className="flex items-center gap-2.5 w-full sm:w-auto shrink-0 justify-end">
          {/* Status Dropdown */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="appearance-none bg-[#F8FAFC] hover:bg-gray-100/80 border border-gray-200/70 text-xs font-semibold text-[#1E2433] py-1.5 pl-3 pr-7 rounded-xl outline-none cursor-pointer transition"
            >
              <option value="all">Status: All Statuses</option>
              <option value="in progress">Status: In Progress</option>
              <option value="under review">Status: Under Review</option>
              <option value="scheduled">Status: Scheduled</option>
              <option value="resolved">Status: Resolved</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#64748B] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Priority Dropdown */}
          <div className="relative">
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="appearance-none bg-[#F8FAFC] hover:bg-gray-100/80 border border-gray-200/70 text-xs font-semibold text-[#1E2433] py-1.5 pl-3 pr-7 rounded-xl outline-none cursor-pointer transition"
            >
              <option value="all">Priority: All</option>
              <option value="high">Priority: High</option>
              <option value="medium">Priority: Medium</option>
              <option value="low">Priority: Low</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#64748B] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Filter Action Button */}
          <button
            type="button"
            onClick={() => {
              setStatusFilter('all')
              setPriorityFilter('all')
              setSearchQuery('')
              setFilterScope('all')
              addToast('Filters Reset', 'Showing all available support cases.', 'info')
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-gray-200/70 bg-[#F8FAFC] hover:bg-gray-100/80 text-xs font-semibold text-[#1E2433] transition cursor-pointer"
            title="Reset active filters"
          >
            <Filter className="w-3.5 h-3.5 text-[#64748B]" />
            Filters
          </button>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 4. Main Case Management Workspace (Split View) */}
      {/* ------------------------------------------------------------- */}
      <section aria-label="Cases workspace" className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 flex-1 min-h-[560px]">
        {/* Left Column: Cases Master List (Span 5 of 12) */}
        <div className="lg:col-span-5 bg-white rounded-3xl p-4 border border-gray-100/80 shadow-2xs flex flex-col justify-between">
          <div>
            {/* Sub-Tabs Row */}
            <div className="flex items-center justify-between pb-3 border-b border-gray-100/60">
              <div className="flex items-center gap-1 bg-gray-50/70 p-1 rounded-full border border-gray-100">
                <button
                  type="button"
                  onClick={() => setFilterScope('all')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition cursor-pointer ${
                    filterScope === 'all'
                      ? 'bg-[#1E2433] text-white shadow-2xs'
                      : 'text-[#64748B] hover:text-[#1E2433]'
                  }`}
                >
                  All Cases ({cases.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterScope('my')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition cursor-pointer ${
                    filterScope === 'my'
                      ? 'bg-[#1E2433] text-white shadow-2xs'
                      : 'text-[#64748B] hover:text-[#1E2433]'
                  }`}
                >
                  My Cases (12)
                </button>
                <button
                  type="button"
                  onClick={() => setFilterScope('needsAction')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition cursor-pointer ${
                    filterScope === 'needsAction'
                      ? 'bg-[#1E2433] text-white shadow-2xs'
                      : 'text-[#64748B] hover:text-[#1E2433]'
                  }`}
                >
                  Needs Action (4)
                </button>
              </div>

              {/* Sort / Reorder Icon */}
              <button
                type="button"
                aria-label="Sort list"
                className="text-[#64748B] hover:text-[#1E2433] p-1.5 rounded-lg hover:bg-gray-100 transition cursor-pointer"
                onClick={() => addToast('Sorted by Recent', 'Sorted cases by latest intervention date.', 'info')}
              >
                <SlidersHorizontal className="w-4 h-4" />
              </button>
            </div>

            {/* List of Case Cards */}
            <div className="mt-2.5 space-y-1.5 overflow-y-auto max-h-[500px] pr-0.5">
              {filteredCases.length === 0 ? (
                <div className="text-center py-12 px-4 text-[#717E95]">
                  <p className="text-sm font-semibold">No cases match your filter criteria.</p>
                  <p className="text-xs mt-1">Try resetting the search keywords or status filters.</p>
                </div>
              ) : (
                filteredCases.map((item) => {
                  const isSelected = item.id === selectedCase.id

                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedCaseId(item.id)}
                      className={`relative flex items-center justify-between p-3 rounded-2xl cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-[#F3F4FD] border border-[#E0E2F9] shadow-2xs'
                          : 'bg-white hover:bg-gray-50/80 border border-transparent'
                      }`}
                    >
                      {/* Left: Avatar & Info */}
                      <div className="flex items-center gap-3 min-w-0">
                        <img
                          src={item.avatar}
                          alt={item.name}
                          className="w-10 h-10 rounded-full object-cover ring-2 ring-white shadow-2xs shrink-0"
                        />
                        <div className="min-w-0">
                          <p className="text-[13px] font-bold text-[#1E2433] truncate leading-snug">
                            {item.name}
                          </p>
                          <p className="text-[11px] text-[#717E95] truncate font-medium leading-snug">
                            {item.id} • {item.concern}
                          </p>
                        </div>
                      </div>

                      {/* Right: Badges & Chevron */}
                      <div className="flex items-center gap-2 shrink-0">
                        {/* Priority Badge */}
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            item.priority === 'High'
                              ? 'bg-[#FEE2E2] text-[#DC2626]'
                              : item.priority === 'Medium'
                              ? 'bg-[#FEF3C7] text-[#D97706]'
                              : 'bg-[#DCFCE7] text-[#16A34A]'
                          }`}
                        >
                          {item.priority}
                        </span>

                        {/* Status Badge */}
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            item.status === 'In Progress'
                              ? 'bg-[#EDE9FE] text-[#6D28D9]'
                              : item.status === 'Under Review'
                              ? 'bg-[#E0F2FE] text-[#0284C7]'
                              : item.status === 'Scheduled'
                              ? 'bg-[#F1F5F9] text-[#475569]'
                              : 'bg-[#DCFCE7] text-[#16A34A]'
                          }`}
                        >
                          {item.status}
                        </span>

                        <ChevronRight className={`w-3.5 h-3.5 transition ${isSelected ? 'text-[#6D28D9]' : 'text-[#CBD5E1]'}`} />
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Case Detailed Inspection (Span 7 of 12) */}
        <div className="lg:col-span-7 bg-white rounded-3xl p-5 border border-gray-100/80 shadow-2xs flex flex-col justify-between">
          <div className="flex flex-col gap-4">
            {/* Header: Student Info + Priority + Status Dropdown */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-100/60">
              {/* Student Identity */}
              <div className="flex items-center gap-3">
                <img
                  src={selectedCase.avatar}
                  alt={selectedCase.name}
                  className="w-12 h-12 rounded-full object-cover ring-2 ring-gray-100 shadow-2xs shrink-0"
                />
                <div>
                  <h2 className="text-lg font-black text-[#1E2433] leading-snug">
                    {selectedCase.name}
                  </h2>
                  <p className="text-xs text-[#717E95] font-medium leading-snug">
                    {selectedCase.id} • {selectedCase.program}
                  </p>
                </div>
              </div>

              {/* Actions & Status Pill */}
              <div className="flex items-center gap-2 self-start sm:self-center">
                {/* Priority Pill */}
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full ${
                    selectedCase.priority === 'High'
                      ? 'bg-[#FEE2E2] text-[#DC2626]'
                      : selectedCase.priority === 'Medium'
                      ? 'bg-[#FEF3C7] text-[#D97706]'
                      : 'bg-[#DCFCE7] text-[#16A34A]'
                  }`}
                >
                  {selectedCase.priority} Priority
                </span>

                {/* Status Selector Pill */}
                <div className="relative">
                  <select
                    value={selectedCase.status}
                    onChange={(e) => handleUpdateStatus(e.target.value as any)}
                    className="appearance-none bg-[#EEF2FF] hover:bg-[#E0E7FF] text-[#4F46E5] text-xs font-bold py-1 pl-3 pr-6 rounded-full cursor-pointer transition outline-none"
                  >
                    <option value="In Progress">In Progress</option>
                    <option value="Under Review">Under Review</option>
                    <option value="Scheduled">Scheduled</option>
                    <option value="Resolved">Resolved</option>
                  </select>
                  <ChevronDown className="w-3 h-3 text-[#4F46E5] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>

                {/* More Options */}
                <button
                  type="button"
                  aria-label="More case actions"
                  onClick={() => setIsFullModalOpen(true)}
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100 transition cursor-pointer"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Sub-Navigation Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {(['Overview', 'Interventions', 'Tasks', 'Notes', 'Timeline'] as const).map((tab) => {
                const isActive = detailTab === tab
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setDetailTab(tab)}
                    className={`px-3.5 py-1 rounded-full text-xs font-bold transition cursor-pointer ${
                      isActive
                        ? 'bg-[#EDE9FE] text-[#6D28D9] shadow-2xs'
                        : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-50'
                    }`}
                  >
                    {tab}
                    {tab === 'Tasks' && (
                      <span className="ml-1 px-1.5 py-0.2 rounded-full bg-gray-200/70 text-[#1E2433] text-[10px]">
                        {selectedCase.tasks.filter((t) => !t.done).length}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Tab 1: Overview (Main Visual Reference) */}
            {detailTab === 'Overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {/* Left Card: Case Summary */}
                <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 flex flex-col justify-between shadow-2xs">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-bold text-[#1E2433]">
                      <FileText className="w-4 h-4 text-[#6D28D9]" />
                      <h3>Case Summary</h3>
                    </div>
                    <p className="text-xs text-[#475569] leading-relaxed mt-2.5 font-normal">
                      {selectedCase.summary}
                    </p>
                  </div>

                  {/* Metadata key-values */}
                  <div className="mt-4 pt-3 border-t border-gray-200/60 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[#717E95] font-medium flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-[#94A3B8]" />
                        Opened
                      </span>
                      <span className="font-bold text-[#1E2433]">{selectedCase.openedDate}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[#717E95] font-medium flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#94A3B8]" />
                        Last Update
                      </span>
                      <span className="font-bold text-[#1E2433]">{selectedCase.lastUpdate}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[#717E95] font-medium flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-[#94A3B8]" />
                        Assigned To
                      </span>
                      <span className="font-bold text-[#1E2433]">{selectedCase.assignedTo}</span>
                    </div>
                  </div>
                </div>

                {/* Right Card: Intervention Progress */}
                <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 flex flex-col justify-between shadow-2xs">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-bold text-[#1E2433]">
                      <Target className="w-4 h-4 text-[#6D28D9]" />
                      <h3>Intervention Progress</h3>
                    </div>

                    {/* Progress text and percentage */}
                    <div className="flex items-center justify-between text-xs mt-3">
                      <span className="text-[#717E95] font-medium">
                        {selectedCase.completedMilestones} of {selectedCase.totalMilestones} milestones completed
                      </span>
                      <span className="font-black text-[#1E2433]">{selectedCase.progressPercent}%</span>
                    </div>

                    {/* Gradient Progress Bar */}
                    <div className="w-full bg-[#E2E8F0] h-2 rounded-full overflow-hidden mt-1.5">
                      <div
                        className="bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] h-full rounded-full transition-all duration-500"
                        style={{ width: `${selectedCase.progressPercent}%` }}
                      />
                    </div>
                  </div>

                  {/* 4-Milestone Pipeline Stepper matching reference */}
                  <div className="mt-4 pt-3 border-t border-gray-200/60">
                    <div className="relative flex items-center justify-between">
                      {/* Connecting Lines Behind Circles */}
                      <div className="absolute left-4 right-4 top-3.5 h-0.5 bg-[#E2E8F0] -z-0">
                        <div
                          className="h-full bg-[#16A34A] transition-all duration-500"
                          style={{
                            width:
                              selectedCase.completedMilestones === 1
                                ? '33%'
                                : selectedCase.completedMilestones === 2
                                ? '66%'
                                : selectedCase.completedMilestones >= 3
                                ? '100%'
                                : '0%',
                          }}
                        />
                      </div>

                      {/* Milestone Nodes */}
                      {selectedCase.milestones.map((m, idx) => {
                        const isDone = m.status === 'completed'
                        const isCurrent = m.status === 'current'

                        return (
                          <div key={m.id} className="relative z-10 flex flex-col items-center text-center">
                            {/* Circle Node */}
                            <div
                              className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                                isDone
                                  ? 'bg-[#DCFCE7] text-[#16A34A] ring-2 ring-white'
                                  : isCurrent
                                  ? 'bg-white text-[#6D28D9] border-2 border-[#6D28D9] ring-2 ring-white shadow-2xs'
                                  : 'bg-white text-gray-300 border-2 border-gray-200 ring-2 ring-white'
                              }`}
                            >
                              {isDone ? (
                                <Check className="w-3.5 h-3.5 stroke-[3]" />
                              ) : isCurrent ? (
                                <span className="w-2 h-2 rounded-full bg-[#6D28D9]" />
                              ) : (
                                <span className="text-[10px] font-bold text-gray-400">{idx + 1}</span>
                              )}
                            </div>

                            {/* Node Label */}
                            <span
                              className={`text-[10px] mt-1.5 leading-tight whitespace-pre-line ${
                                isCurrent
                                  ? 'font-bold text-[#1E2433]'
                                  : isDone
                                  ? 'font-medium text-[#475569]'
                                  : 'text-[#94A3B8]'
                              }`}
                            >
                              {m.title}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Interventions Detailed List */}
            {detailTab === 'Interventions' && (
              <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-[#1E2433]">Active Protocol: UG Attendance &amp; Stress V1</h3>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#EDE9FE] text-[#6D28D9]">
                    Standard Protocol
                  </span>
                </div>
                <div className="space-y-2">
                  <div className="p-3 rounded-xl bg-white border border-gray-100 flex items-start gap-3">
                    <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <p className="font-bold text-[#1E2433]">Milestone 1: 1-on-1 Academic Review</p>
                      <p className="text-[#64748B] mt-0.5">Completed by Prof. Sharma on 08 Oct, 2025.</p>
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-gray-100 flex items-start gap-3">
                    <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <p className="font-bold text-[#1E2433]">Milestone 2: Academic Goal Setting &amp; Plan Freezing</p>
                      <p className="text-[#64748B] mt-0.5">Plan created with adjusted lab deadlines.</p>
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-[#E0E2F9] flex items-start gap-3 shadow-2xs">
                    <Clock className="w-4 h-4 text-[#6D28D9] shrink-0 mt-0.5 animate-pulse" />
                    <div className="text-xs">
                      <p className="font-bold text-[#6D28D9]">Milestone 3: Active Intervention (Ongoing)</p>
                      <p className="text-[#64748B] mt-0.5">Weekly check-in on test preparation schedule.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Actionable Tasks */}
            {detailTab === 'Tasks' && (
              <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 space-y-2.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-[#1E2433]">Case Action Items</h3>
                  <span className="text-xs text-[#717E95]">Click checkbox to update</span>
                </div>
                <div className="space-y-2">
                  {selectedCase.tasks.map((task) => (
                    <label
                      key={task.id}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-gray-100 hover:bg-gray-50/80 cursor-pointer transition"
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={task.done}
                          onChange={() => handleToggleTask(task.id)}
                          className="w-4 h-4 accent-[#6D28D9] rounded cursor-pointer"
                        />
                        <span className={`text-xs font-medium ${task.done ? 'line-through text-gray-400' : 'text-[#1E2433]'}`}>
                          {task.text}
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-[#94A3B8]">Due: {task.dueDate}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 4: Faculty Notes */}
            {detailTab === 'Notes' && (
              <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={newNoteText}
                    onChange={(e) => setNewNoteText(e.target.value)}
                    placeholder="Add confidential teacher note..."
                    className="flex-1 text-xs bg-white border border-gray-200 rounded-xl px-3 py-2 outline-none text-[#1E2433] placeholder-[#94A3B8]"
                  />
                  <button
                    type="button"
                    onClick={handleAddNote}
                    className="px-3 py-2 rounded-xl bg-[#1E2433] text-white text-xs font-bold hover:bg-[#2D3748] transition cursor-pointer"
                  >
                    Add Note
                  </button>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {selectedCase.notes.map((note) => (
                    <div key={note.id} className="p-3 rounded-xl bg-white border border-gray-100 text-xs">
                      <div className="flex items-center justify-between text-[#717E95] text-[11px] mb-1">
                        <span className="font-bold text-[#1E2433]">{note.author}</span>
                        <span>{note.date}</span>
                      </div>
                      <p className="text-[#475569] leading-relaxed">{note.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 5: Timeline & Audit Chain */}
            {detailTab === 'Timeline' && (
              <div className="bg-[#FAFBFD] rounded-2xl p-4 border border-gray-100 space-y-2.5">
                <h3 className="text-sm font-bold text-[#1E2433]">Audit &amp; Case Activity Log</h3>
                <div className="space-y-2">
                  {selectedCase.timeline.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-gray-100 text-xs">
                      <div className="w-7 h-7 rounded-full bg-[#EDE9FE] text-[#6D28D9] flex items-center justify-center shrink-0">
                        <Calendar className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-[#1E2433]">{item.event}</p>
                        <p className="text-[10px] text-[#717E95]">{item.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Bottom Action Bar: Next Action */}
          <div className="mt-4 pt-3 border-t border-gray-100/70 flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#FAFBFD] p-3.5 rounded-2xl border border-gray-100 shadow-2xs">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div className="w-9 h-9 rounded-xl bg-[#EDE9FE] text-[#6D28D9] flex items-center justify-center shrink-0">
                <Calendar className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-[#1E2433] leading-tight">
                  Next Action: <span className="font-normal text-[#475569]">{selectedCase.nextAction}</span>
                </p>
                <p className="text-[11px] text-[#717E95] font-semibold flex items-center gap-1 mt-0.5">
                  <span>📅</span> {selectedCase.nextActionDate}
                </p>
              </div>
            </div>

            {/* View Full Case Button */}
            <button
              type="button"
              onClick={() => setIsFullModalOpen(true)}
              className="w-full sm:w-auto px-4 py-2 rounded-full bg-[#1E2433] text-white text-xs font-bold hover:bg-[#2D3748] transition flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer shrink-0"
            >
              <span>View Full Case</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 5. Full Case Modal Dialog */}
      {/* ------------------------------------------------------------- */}
      {isFullModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-xl border border-gray-100 flex flex-col gap-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <img
                  src={selectedCase.avatar}
                  alt={selectedCase.name}
                  className="w-10 h-10 rounded-full object-cover ring-2 ring-gray-100"
                />
                <div>
                  <h3 className="text-base font-black text-[#1E2433]">{selectedCase.name} — Full Dossier</h3>
                  <p className="text-xs text-[#717E95]">{selectedCase.id} • {selectedCase.program}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsFullModalOpen(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs max-h-[60vh] overflow-y-auto pr-1">
              <div className="p-3.5 rounded-2xl bg-[#FAFBFD] border border-gray-100">
                <h4 className="font-bold text-[#1E2433] mb-1">Academic Diagnostic Assessment</h4>
                <p className="text-[#475569] leading-relaxed">
                  Student triggered early attention threshold on 08 Oct due to consecutive missed lab sessions.
                  Diagnostic shows no foundational concept gap; primary bottleneck is scheduling anxiety around multiple end-of-term project deadlines.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#FAFBFD] border border-gray-100">
                <h4 className="font-bold text-[#1E2433] mb-1">Action Protocol</h4>
                <ul className="list-disc list-inside text-[#475569] space-y-1">
                  <li>Weekly asynchronous check-in via DISHA student portal.</li>
                  <li>Faculty advisory note shared with CSE Department Chair.</li>
                  <li>Peer study group mentor introduced.</li>
                </ul>
              </div>

              <div className="flex items-center justify-between p-3 rounded-2xl bg-[#F0FDF4] border border-[#DCFCE7] text-[#166534]">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
                  <span className="font-semibold">Cryptographic Evidence Packet verified</span>
                </div>
                <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded-md border border-gray-200">
                  SHA-256 Digest
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setIsFullModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-[#64748B] hover:text-[#1E2433] cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsFullModalOpen(false)
                  addToast('Export Complete', 'Exported student support dossier as verified PDF packet.', 'success')
                }}
                className="px-4 py-2 rounded-xl bg-[#1E2433] text-white text-xs font-bold hover:bg-[#2D3748] transition cursor-pointer"
              >
                Export Dossier PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

