import React, { useState } from 'react'
import {
  Folder,
  CheckCircle2,
  Calendar,
  Sparkles,
  Filter,
  Sprout,
  Users,
  Heart,
  ChevronRight,
  MoreVertical,
  FileText,
  Target,
  Video,
  Play,
  Headphones,
  BookOpen,
  ArrowUpRight,
  Clock,
  User,
  ShieldCheck,
  Check,
  X,
  Mic,
  Camera,
  ExternalLink,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { useApp } from '../../context/AppContext'

interface StudentMyCasesPageProps {
  demoMode: DemoMode
}

type FilterTab = 'all' | 'active' | 'completed'
type DetailTab = 'overview' | 'plan' | 'notes' | 'timeline'

interface CaseData {
  id: string
  caseNumber: string
  title: string
  status: 'In Progress' | 'Completed'
  openedDate: string
  completedDate?: string
  iconType: 'leaf' | 'users' | 'heart'
  summary: string
  assignedMentor: string
  supportTeam: string
  progress: {
    completedSteps: number
    totalSteps: number
    percentage: number
    steps: {
      name: string
      status: 'completed' | 'active' | 'pending'
    }[]
  }
  nextStep?: {
    title: string
    time: string
    actionLabel: string
    canJoin: boolean
  }
  resources: {
    id: string
    title: string
    type: 'Video' | 'Audio' | 'Quick Guide'
    duration?: string
    iconType: 'play' | 'headphones' | 'document'
    bg: string
    iconBg: string
    iconColor: string
    content: string
  }[]
  planItems: {
    id: string
    title: string
    description: string
    targetDate: string
    status: 'completed' | 'in_progress' | 'upcoming'
  }[]
  notes: {
    id: string
    author: string
    role: string
    date: string
    content: string
  }[]
  timelineEvents: {
    id: string
    title: string
    date: string
    description: string
    status: 'completed' | 'active' | 'scheduled'
  }[]
}

const CASES_DATA: CaseData[] = [
  {
    id: 'case-1027',
    caseNumber: 'CASE-1027',
    title: 'Academic Stress',
    status: 'In Progress',
    openedDate: '08 Oct, 2025',
    iconType: 'leaf',
    summary: 'Support for elevated academic stress and difficulty in managing workload.',
    assignedMentor: 'Prof. Sharma',
    supportTeam: 'Counselling Unit',
    progress: {
      completedSteps: 2,
      totalSteps: 4,
      percentage: 50,
      steps: [
        { name: 'Initial Check-in', status: 'completed' },
        { name: 'Plan Created', status: 'completed' },
        { name: 'Ongoing Support', status: 'active' },
        { name: 'Review & Close', status: 'pending' },
      ],
    },
    nextStep: {
      title: 'Follow-up session with Prof. Sharma',
      time: '14 Oct, 17:30',
      actionLabel: 'Join Session',
      canJoin: true,
    },
    resources: [
      {
        id: 'r1',
        title: 'Managing Academic Stress',
        type: 'Video',
        duration: '5 min',
        iconType: 'play',
        bg: 'bg-[#F0F7FF]',
        iconBg: 'bg-[#DBEAFE]',
        iconColor: 'text-[#1D4ED8]',
        content: 'Learn cognitive reframing and structured time-chunking techniques for high-workload semesters.',
      },
      {
        id: 'r2',
        title: 'Focus & Calm Meditation',
        type: 'Audio',
        duration: '7 min',
        iconType: 'headphones',
        bg: 'bg-[#FEF6EE]',
        iconBg: 'bg-[#FFEDD5]',
        iconColor: 'text-[#C2410C]',
        content: 'A guided breathwork sequence designed to lower cortisol and regain focus during exam preparation.',
      },
      {
        id: 'r3',
        title: 'Study-Wellbeing Balance',
        type: 'Quick Guide',
        iconType: 'document',
        bg: 'bg-[#FAF5FF]',
        iconBg: 'bg-[#F3E8FF]',
        iconColor: 'text-[#7E22CE]',
        content: 'Checklist and weekly planner template balancing course submissions with restorative sleep.',
      },
    ],
    planItems: [
      {
        id: 'pi-1',
        title: '1-on-1 Academic Needs Assessment',
        description: 'Discuss current coursework pain points and identify high-friction assignment deadlines.',
        targetDate: '10 Oct, 2025',
        status: 'completed',
      },
      {
        id: 'pi-2',
        title: 'Workload Pacing & Pomodoro Schedule',
        description: 'Set up 25-minute study intervals with dedicated 5-minute movement breaks.',
        targetDate: '12 Oct, 2025',
        status: 'completed',
      },
      {
        id: 'pi-3',
        title: 'Mid-term Check-in Consultation',
        description: 'Review assignment submission progress and evaluate stress levels ahead of midterm week.',
        targetDate: '14 Oct, 2025',
        status: 'in_progress',
      },
      {
        id: 'pi-4',
        title: 'Final Progress Review & Graduation from Plan',
        description: 'Confirm sustained wellbeing score and close active intervention case.',
        targetDate: '24 Oct, 2025',
        status: 'upcoming',
      },
    ],
    notes: [
      {
        id: 'n-1',
        author: 'Prof. Sharma',
        role: 'Faculty Mentor',
        date: '12 Oct, 2025',
        content: 'Asha is responding very well to the pacing template. Recommended taking a 15-minute screen-free walk after each 2-hour study block.',
      },
      {
        id: 'n-2',
        author: 'Wellbeing Support Unit',
        role: 'Counselling Advisor',
        date: '08 Oct, 2025',
        content: 'Support case opened upon student request. Allocated 4-week structured academic mentorship plan.',
      },
    ],
    timelineEvents: [
      {
        id: 'te-1',
        title: 'Case Opened',
        date: '08 Oct, 2025 · 10:15 AM',
        description: 'Student initiated confidential academic support inquiry.',
        status: 'completed',
      },
      {
        id: 'te-2',
        title: 'Initial Check-in Conducted',
        date: '10 Oct, 2025 · 04:30 PM',
        description: 'Introductory video consultation with Prof. Sharma.',
        status: 'completed',
      },
      {
        id: 'te-3',
        title: 'Pacing Plan Approved',
        date: '12 Oct, 2025 · 02:00 PM',
        description: 'Mutual agreement on 4-week study milestone benchmarks.',
        status: 'completed',
      },
      {
        id: 'te-4',
        title: 'Upcoming Video Follow-up',
        date: '14 Oct, 2025 · 05:30 PM',
        description: 'Virtual check-in scheduled via DISHA Secure Room.',
        status: 'scheduled',
      },
    ],
  },
  {
    id: 'case-0984',
    caseNumber: 'CASE-0984',
    title: 'Adjustment Support',
    status: 'Completed',
    openedDate: '01 Sep, 2025',
    completedDate: '21 Sep',
    iconType: 'users',
    summary: 'Guidance and peer-mentoring support for campus transition and group project integration.',
    assignedMentor: 'Dr. Rao',
    supportTeam: 'Student Mentorship Cell',
    progress: {
      completedSteps: 4,
      totalSteps: 4,
      percentage: 100,
      steps: [
        { name: 'Initial Check-in', status: 'completed' },
        { name: 'Plan Created', status: 'completed' },
        { name: 'Ongoing Support', status: 'completed' },
        { name: 'Review & Close', status: 'completed' },
      ],
    },
    nextStep: {
      title: 'Support journey completed successfully',
      time: 'Reach out anytime if further guidance is needed',
      actionLabel: 'Case Archived',
      canJoin: false,
    },
    resources: [
      {
        id: 'r4',
        title: 'Campus Transition Guide',
        type: 'Quick Guide',
        iconType: 'document',
        bg: 'bg-[#F0FDF4]',
        iconBg: 'bg-[#DCFCE7]',
        iconColor: 'text-[#16A34A]',
        content: 'Directory of academic help centers, student clubs, and quiet campus study zones.',
      },
      {
        id: 'r5',
        title: 'Active Peer Collaboration',
        type: 'Video',
        duration: '6 min',
        iconType: 'play',
        bg: 'bg-[#F0F7FF]',
        iconBg: 'bg-[#DBEAFE]',
        iconColor: 'text-[#1D4ED8]',
        content: 'Effective communication practices for engineering cohort group projects.',
      },
      {
        id: 'r6',
        title: 'Confidence Building Audio',
        type: 'Audio',
        duration: '8 min',
        iconType: 'headphones',
        bg: 'bg-[#FEF6EE]',
        iconBg: 'bg-[#FFEDD5]',
        iconColor: 'text-[#C2410C]',
        content: 'Guided audio on imposter syndrome management and celebrating small wins.',
      },
    ],
    planItems: [
      {
        id: 'pi-5',
        title: 'Orientation Peer Pairing',
        description: 'Connect with a senior mentor in the Computer Science department.',
        targetDate: '05 Sep, 2025',
        status: 'completed',
      },
      {
        id: 'pi-6',
        title: 'Group Study Workshop',
        description: 'Participate in the collaborative coding lab session.',
        targetDate: '12 Sep, 2025',
        status: 'completed',
      },
      {
        id: 'pi-7',
        title: 'Final Adjustment Reflection',
        description: 'Review social adaptation and campus resources comfort.',
        targetDate: '21 Sep, 2025',
        status: 'completed',
      },
    ],
    notes: [
      {
        id: 'n-3',
        author: 'Dr. Rao',
        role: 'Faculty Advisor',
        date: '21 Sep, 2025',
        content: 'Asha has settled in remarkably well and demonstrated high collaboration in team lab submissions.',
      },
    ],
    timelineEvents: [
      {
        id: 'te-5',
        title: 'Case Opened',
        date: '01 Sep, 2025 · 09:00 AM',
        description: 'Transition onboarding check-in initiated.',
        status: 'completed',
      },
      {
        id: 'te-6',
        title: 'Mentorship Session Completed',
        date: '10 Sep, 2025 · 03:00 PM',
        description: 'Met with Dr. Rao and senior peer mentor.',
        status: 'completed',
      },
      {
        id: 'te-7',
        title: 'Case Concluded with Resolution',
        date: '21 Sep, 2025 · 04:30 PM',
        description: 'All milestones satisfied with positive feedback.',
        status: 'completed',
      },
    ],
  },
  {
    id: 'case-0948',
    caseNumber: 'CASE-0948',
    title: 'Wellbeing Check-in',
    status: 'Completed',
    openedDate: '20 Aug, 2025',
    completedDate: '05 Sep',
    iconType: 'heart',
    summary: 'Semester start wellbeing pulse review and sleep schedule optimization guidance.',
    assignedMentor: 'Prof. Sharma',
    supportTeam: 'Guidance Team',
    progress: {
      completedSteps: 4,
      totalSteps: 4,
      percentage: 100,
      steps: [
        { name: 'Initial Check-in', status: 'completed' },
        { name: 'Plan Created', status: 'completed' },
        { name: 'Ongoing Support', status: 'completed' },
        { name: 'Review & Close', status: 'completed' },
      ],
    },
    nextStep: {
      title: 'Routine check-in closed',
      time: 'Continue logging weekly emotional pulses',
      actionLabel: 'Log Pulse',
      canJoin: false,
    },
    resources: [
      {
        id: 'r7',
        title: 'Healthy Sleep Fundamentals',
        type: 'Quick Guide',
        iconType: 'document',
        bg: 'bg-[#FAF5FF]',
        iconBg: 'bg-[#F3E8FF]',
        iconColor: 'text-[#7E22CE]',
        content: 'Scientific protocols for screen-dimming and evening circadian rhythm reset.',
      },
      {
        id: 'r8',
        title: 'Morning Energy Routine',
        type: 'Audio',
        duration: '5 min',
        iconType: 'headphones',
        bg: 'bg-[#FEF6EE]',
        iconBg: 'bg-[#FFEDD5]',
        iconColor: 'text-[#C2410C]',
        content: 'Invigorating morning sequence to start your day with focus and intention.',
      },
      {
        id: 'r9',
        title: 'Semester Goal Setting',
        type: 'Video',
        duration: '4 min',
        iconType: 'play',
        bg: 'bg-[#F0F7FF]',
        iconBg: 'bg-[#DBEAFE]',
        iconColor: 'text-[#1D4ED8]',
        content: 'Setting realistic, sustainable academic objectives without burnout.',
      },
    ],
    planItems: [
      {
        id: 'pi-8',
        title: 'Sleep Hygiene Self-Check',
        description: 'Track evening screen time cutoff for 7 consecutive days.',
        targetDate: '27 Aug, 2025',
        status: 'completed',
      },
      {
        id: 'pi-9',
        title: 'Follow-up Pulse Survey',
        description: 'Verify improved morning energy and focus levels.',
        targetDate: '05 Sep, 2025',
        status: 'completed',
      },
    ],
    notes: [
      {
        id: 'n-4',
        author: 'Prof. Sharma',
        role: 'Faculty Mentor',
        date: '05 Sep, 2025',
        content: 'Sleep consistency improved by 40%. Student expressed readiness for upcoming midterm project phase.',
      },
    ],
    timelineEvents: [
      {
        id: 'te-8',
        title: 'Pulse Flagged Check-in',
        date: '20 Aug, 2025 · 11:00 AM',
        description: 'Kickoff survey follow-up on sleep balance.',
        status: 'completed',
      },
      {
        id: 'te-9',
        title: 'Advisory Review Concluded',
        date: '05 Sep, 2025 · 02:15 PM',
        description: 'Case closed with healthy baseline verified.',
        status: 'completed',
      },
    ],
  },
]

export function StudentMyCasesPage({ demoMode }: StudentMyCasesPageProps) {
  const { addToast } = useApp()
  const [filterTab, setFilterTab] = useState<FilterTab>('all')
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case-1027')
  const [detailTab, setDetailTab] = useState<DetailTab>('overview')
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false)
  const [selectedResource, setSelectedResource] = useState<CaseData['resources'][0] | null>(null)

  // Filter cases based on tab
  const filteredCases = CASES_DATA.filter((c) => {
    if (filterTab === 'active') return c.status === 'In Progress'
    if (filterTab === 'completed') return c.status === 'Completed'
    return true
  })

  // Selected case
  const currentCase = CASES_DATA.find((c) => c.id === selectedCaseId) || CASES_DATA[0]

  // Counts
  const activeCount = CASES_DATA.filter((c) => c.status === 'In Progress').length
  const completedCount = CASES_DATA.filter((c) => c.status === 'Completed').length
  const upcomingActionCount = currentCase.nextStep?.canJoin ? 1 : 0

  const handleJoinSession = () => {
    setIsVideoModalOpen(true)
  }

  const handleOpenResource = (res: CaseData['resources'][0]) => {
    setSelectedResource(res)
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. TOP STATISTICS & ENCOURAGEMENT BANNER ROW */}
      <section aria-label="Student case statistics and encouragement" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3.5">
        {/* Card 1: Active Case (Pastel yellow) */}
        <div className="lg:col-span-2 bg-[#FEFCE8] border border-[#FEF08A]/80 rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#FEF9C3] flex items-center justify-center text-[#A16207]">
              <Folder className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-[#854D0E]">Active Case</span>
          </div>
          <div className="mt-2.5">
            <span className="text-3xl font-bold tracking-tight text-[#1E2433]">{activeCount}</span>
          </div>
        </div>

        {/* Card 2: Completed (Pastel blue) */}
        <div className="lg:col-span-2 bg-[#F0F7FF] border border-[#BFDBFE]/80 rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#DBEAFE] flex items-center justify-center text-[#1D4ED8]">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-[#1E40AF]">Completed</span>
          </div>
          <div className="mt-2.5">
            <span className="text-3xl font-bold tracking-tight text-[#1E2433]">{completedCount}</span>
          </div>
        </div>

        {/* Card 3: Upcoming Action (Pastel purple) */}
        <div className="lg:col-span-2 bg-[#FAF5FF] border border-[#E9D5FF]/80 rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#F3E8FF] flex items-center justify-center text-[#7E22CE]">
              <Calendar className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-[#6B21A8]">Upcoming Action</span>
          </div>
          <div className="mt-2.5">
            <span className="text-3xl font-bold tracking-tight text-[#1E2433]">{upcomingActionCount}</span>
          </div>
        </div>

        {/* Encouragement Banner: Calming Wellbeing Illustration + Text */}
        <div className="sm:col-span-2 lg:col-span-6 bg-gradient-to-r from-[#FFF7ED] via-[#FDF4FF] to-[#F5F3FF] border border-[#E9D5FF]/60 rounded-2xl p-3.5 sm:px-5 sm:py-3.5 flex items-center justify-between gap-3 shadow-2xs overflow-hidden relative">
          {/* Calming student wellbeing illustration: young woman with headphones and gentle botanicals */}
          <div className="flex items-center gap-3.5 shrink-0">
            <div className="w-16 h-16 sm:w-18 sm:h-18 relative shrink-0">
              <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-xs" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Background soft pastel halo */}
                <circle cx="50" cy="50" r="46" fill="#F3E8FF" />
                <path d="M12 78 C25 65 35 70 45 68 C55 66 65 74 88 78 C80 92 65 96 50 96 C32 96 18 89 12 78 Z" fill="#E9D5FF" />
                
                {/* Botanical leaves behind */}
                <path d="M18 42 C14 30 24 22 34 26 C30 36 24 40 18 42 Z" fill="#86EFAC" opacity="0.85" />
                <path d="M82 40 C88 28 78 20 68 24 C72 34 78 38 82 40 Z" fill="#A7F3D0" opacity="0.85" />

                {/* Girl torso / purple knit sweater */}
                <path d="M26 88 C26 72 38 68 50 68 C62 68 74 72 74 88 C74 94 26 94 26 88 Z" fill="#A78BFA" />
                <path d="M42 68 L50 78 L58 68 Z" fill="#DDD6FE" />

                {/* Neck and face */}
                <rect x="45" y="58" width="10" height="12" rx="4" fill="#FCD34D" />
                <circle cx="50" cy="46" r="16" fill="#FDE68A" />

                {/* Dark flowing hair */}
                <path d="M36 44 C34 32 40 22 50 22 C60 22 66 32 64 44 C64 54 62 62 60 66 C57 66 54 48 50 48 C46 48 43 66 40 66 C38 62 36 54 36 44 Z" fill="#312E81" />

                {/* Calm eyes & gentle smile */}
                <path d="M44 46 Q47 48 48 46" stroke="#4338CA" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M52 46 Q53 48 56 46" stroke="#4338CA" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M47 52 Q50 55 53 52" stroke="#4338CA" strokeWidth="1.5" strokeLinecap="round" />

                {/* Purple over-ear headphones */}
                <path d="M34 46 C34 28 66 28 66 46" stroke="#6D28D9" strokeWidth="3.5" strokeLinecap="round" fill="none" />
                <rect x="31" y="42" width="6" height="12" rx="3" fill="#7C3AED" />
                <rect x="63" y="42" width="6" height="12" rx="3" fill="#7C3AED" />
              </svg>
            </div>
            
            {/* Encouragement Text */}
            <div className="flex flex-col">
              <h2 className="text-sm sm:text-base font-bold text-[#1E2433] flex items-center gap-1.5 leading-snug">
                <span>You&apos;re taking positive steps!</span>
                <span className="text-base">🌱</span>
              </h2>
              <p className="text-xs text-[#64748B] font-normal mt-0.5 leading-relaxed">
                Continue with your plan and stay consistent.
              </p>
            </div>
          </div>

          {/* Decorative Sparkle */}
          <div className="hidden xl:flex items-center justify-center w-8 h-8 rounded-full bg-white/70 text-purple-500 shadow-2xs">
            <Sparkles className="w-4 h-4 text-purple-500" />
          </div>
        </div>
      </section>

      {/* 2. MAIN WORKSPACE: TWO LARGE SIDE-BY-SIDE PANELS (STRICTLY IDENTICAL OUTER HEIGHTS & ALIGNMENT) */}
      <section aria-label="Support cases and details" className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        {/* LEFT PANEL: YOUR CASES */}
        <div className="lg:col-span-5 xl:col-span-4 flex flex-col bg-white rounded-3xl border border-gray-100 shadow-2xs p-4 sm:p-5 h-full">
          {/* Panel Header */}
          <div className="flex items-center justify-between pb-3">
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">Your Cases</h2>
            <button
              type="button"
              onClick={() => addToast('Filter Cases', 'Showing active and historical cases.', 'info')}
              className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-gray-100/80 transition"
              title="Filter case view"
            >
              <Filter className="w-4 h-4" />
            </button>
          </div>

          {/* Filter Pills / Tabs */}
          <div className="flex items-center gap-1.5 pb-4">
            <button
              type="button"
              onClick={() => setFilterTab('all')}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${
                filterTab === 'all'
                  ? 'bg-[#1E2433] text-white shadow-xs'
                  : 'bg-transparent text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100/60'
              }`}
            >
              All Cases ({CASES_DATA.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('active')}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${
                filterTab === 'active'
                  ? 'bg-[#1E2433] text-white shadow-xs'
                  : 'bg-transparent text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100/60'
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('completed')}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${
                filterTab === 'completed'
                  ? 'bg-[#1E2433] text-white shadow-xs'
                  : 'bg-transparent text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100/60'
              }`}
            >
              Completed ({completedCount})
            </button>
          </div>

          {/* Cases List */}
          <div className="flex flex-col gap-2.5">
            {filteredCases.map((item) => {
              const isSelected = item.id === currentCase.id

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedCaseId(item.id)}
                  className={`w-full flex items-center justify-between p-3.5 rounded-2xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-[#F2EFFE] border-[#DDD6FE] shadow-2xs'
                      : 'bg-white hover:bg-gray-50/80 border-transparent hover:border-gray-100'
                  }`}
                >
                  {/* Left: Icon + Title & Subtitle */}
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        item.iconType === 'leaf'
                          ? 'bg-[#ECFDF5] text-[#059669]'
                          : item.iconType === 'users'
                          ? 'bg-[#EFF6FF] text-[#2563EB]'
                          : 'bg-[#FAF5FF] text-[#7C3AED]'
                      }`}
                    >
                      {item.iconType === 'leaf' && <Sprout className="w-4 h-4" />}
                      {item.iconType === 'users' && <Users className="w-4 h-4" />}
                      {item.iconType === 'heart' && <Heart className="w-4 h-4" />}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className="text-xs sm:text-sm font-bold text-[#1E2433] truncate">
                        {item.title}
                      </span>
                      <span className="text-[11px] text-[#717E95] font-normal truncate mt-0.5">
                        {item.caseNumber} • {item.status === 'Completed' ? `Completed ${item.completedDate}` : `Opened ${item.openedDate.split(',')[0]}`}
                      </span>
                    </div>
                  </div>

                  {/* Right: Status Badge & Chevron */}
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                        item.status === 'In Progress'
                          ? 'bg-[#EEF2FF] text-[#4F46E5]'
                          : 'bg-[#ECFDF5] text-[#059669]'
                      }`}
                    >
                      {item.status}
                    </span>
                    <ChevronRight className={`w-3.5 h-3.5 ${isSelected ? 'text-[#6366F1]' : 'text-gray-300'}`} />
                  </div>
                </div>
              )
            })}
          </div>

          {/* Spacer to guarantee pixel-perfect height parity with right details panel */}
          <div className="flex-1 min-h-[30px]" />
        </div>

        {/* RIGHT PANEL: SELECTED CASE DETAILS */}
        <div className="lg:col-span-7 xl:col-span-8 flex flex-col bg-white rounded-3xl border border-gray-100 shadow-2xs p-5 md:p-6 h-full">
          {/* Header Row: Case Icon + Title + Case Ref + Status Pill + More Action */}
          <div className="flex items-center justify-between gap-3 pb-4 border-b border-gray-100/80">
            <div className="flex items-center gap-3">
              <div
                className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${
                  currentCase.iconType === 'leaf'
                    ? 'bg-[#ECFDF5] text-[#059669]'
                    : currentCase.iconType === 'users'
                    ? 'bg-[#EFF6FF] text-[#2563EB]'
                    : 'bg-[#FAF5FF] text-[#7C3AED]'
                }`}
              >
                {currentCase.iconType === 'leaf' && <Sprout className="w-5 h-5" />}
                {currentCase.iconType === 'users' && <Users className="w-5 h-5" />}
                {currentCase.iconType === 'heart' && <Heart className="w-5 h-5" />}
              </div>
              <div className="flex flex-col">
                <h3 className="text-base sm:text-lg font-bold text-[#1E2433] tracking-tight">
                  {currentCase.title}
                </h3>
                <span className="text-xs text-[#717E95] font-normal mt-0.5">
                  {currentCase.caseNumber} • Opened {currentCase.openedDate}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Status Pill */}
              <div
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                  currentCase.status === 'In Progress'
                    ? 'bg-[#EEF2FF] text-[#4F46E5] border border-[#C7D2FE]'
                    : 'bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]'
                }`}
              >
                <span>{currentCase.status}</span>
                <span className="text-[10px]">⌵</span>
              </div>

              {/* More options button */}
              <button
                type="button"
                onClick={() => addToast('Case Options', `Reference ${currentCase.caseNumber}`, 'info')}
                className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Sub-tabs Row: Overview | Intervention Plan | Notes | Timeline */}
          <div className="flex items-center gap-2 py-3.5 border-b border-gray-100/70 overflow-x-auto">
            <button
              type="button"
              onClick={() => setDetailTab('overview')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                detailTab === 'overview'
                  ? 'bg-[#EDE8FB] text-[#4338CA]'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-50'
              }`}
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => setDetailTab('plan')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                detailTab === 'plan'
                  ? 'bg-[#EDE8FB] text-[#4338CA]'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-50'
              }`}
            >
              Intervention Plan
            </button>
            <button
              type="button"
              onClick={() => setDetailTab('notes')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                detailTab === 'notes'
                  ? 'bg-[#EDE8FB] text-[#4338CA]'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-50'
              }`}
            >
              Notes
            </button>
            <button
              type="button"
              onClick={() => setDetailTab('timeline')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                detailTab === 'timeline'
                  ? 'bg-[#EDE8FB] text-[#4338CA]'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-50'
              }`}
            >
              Timeline
            </button>
          </div>

          {/* CONTENT AREA: BASED ON SUB-TAB */}
          <div className="flex-1 flex flex-col pt-4">
            {detailTab === 'overview' && (
              <div className="flex flex-col gap-4">
                {/* Row: Case Summary Card (Left) & Intervention Progress Card (Right) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {/* Left: Case Summary Card */}
                  <div className="bg-[#FAFBFD] border border-gray-100 rounded-2xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433] mb-2">
                        <FileText className="w-3.5 h-3.5 text-[#6366F1]" />
                        <span>Case Summary</span>
                      </div>
                      <p className="text-xs text-[#475569] leading-relaxed">
                        {currentCase.summary}
                      </p>
                    </div>

                    <div className="flex flex-col gap-2 mt-4 pt-3 border-t border-gray-100/90 text-xs">
                      <div className="flex items-center justify-between text-[#64748B]">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-gray-400" />
                          <span>Opened</span>
                        </span>
                        <span className="font-semibold text-[#1E2433]">{currentCase.openedDate}</span>
                      </div>
                      <div className="flex items-center justify-between text-[#64748B]">
                        <span className="flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-gray-400" />
                          <span>Assigned Mentor</span>
                        </span>
                        <span className="font-semibold text-[#1E2433]">{currentCase.assignedMentor}</span>
                      </div>
                      <div className="flex items-center justify-between text-[#64748B]">
                        <span className="flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5 text-gray-400" />
                          <span>Support Team</span>
                        </span>
                        <span className="font-semibold text-[#1E2433]">{currentCase.supportTeam}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Intervention Progress Card */}
                  <div className="bg-[#FAFBFD] border border-gray-100 rounded-2xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433]">
                          <Target className="w-3.5 h-3.5 text-[#6366F1]" />
                          <span>Intervention Progress</span>
                        </div>
                      </div>

                      {/* Counter & Percentage */}
                      <div className="flex items-center justify-between text-xs mt-3 mb-1.5">
                        <span className="text-[#64748B]">
                          {currentCase.progress.completedSteps} of {currentCase.progress.totalSteps} steps completed
                        </span>
                        <span className="font-bold text-[#1E2433]">{currentCase.progress.percentage}%</span>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mb-5">
                        <div
                          className="h-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-full transition-all duration-500"
                          style={{ width: `${currentCase.progress.percentage}%` }}
                        />
                      </div>

                      {/* 4-Step Stepper Component */}
                      <div className="relative flex items-center justify-between mt-2 px-1">
                        {/* Connecting background line */}
                        <div className="absolute top-3 left-4 right-4 h-0.5 bg-gray-200 z-0" />
                        <div
                          className="absolute top-3 left-4 h-0.5 bg-emerald-500 transition-all z-0"
                          style={{
                            width:
                              currentCase.progress.percentage === 100
                                ? 'calc(100% - 32px)'
                                : 'calc(50% - 16px)',
                          }}
                        />

                        {currentCase.progress.steps.map((st, idx) => {
                          const isDone = st.status === 'completed'
                          const isActive = st.status === 'active'

                          return (
                            <div key={idx} className="relative z-10 flex flex-col items-center">
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                                  isDone
                                    ? 'bg-emerald-500 text-white ring-2 ring-emerald-100'
                                    : isActive
                                    ? 'bg-white border-2 border-[#6366F1] text-[#6366F1] ring-2 ring-purple-100'
                                    : 'bg-white border-2 border-gray-300 text-transparent'
                                }`}
                              >
                                {isDone && <Check className="w-3 h-3 stroke-[3]" />}
                                {isActive && <span className="w-2 h-2 rounded-full bg-[#6366F1]" />}
                              </div>
                              <span
                                className={`text-[10px] mt-1.5 text-center font-medium max-w-[65px] ${
                                  isDone
                                    ? 'text-emerald-700 font-semibold'
                                    : isActive
                                    ? 'text-[#6366F1] font-bold'
                                    : 'text-gray-400'
                                }`}
                              >
                                {st.name}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Next Step Card / Bar */}
                {currentCase.nextStep && (
                  <div className="bg-[#FAFBFD] border border-gray-100 rounded-2xl p-3.5 sm:px-4 sm:py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-[#F3E8FF] text-[#7C3AED] flex items-center justify-center shrink-0">
                        <Calendar className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#7C3AED]">
                          Next Step
                        </span>
                        <span className="text-xs sm:text-sm font-semibold text-[#1E2433]">
                          {currentCase.nextStep.title}
                        </span>
                        <div className="flex items-center gap-1.5 text-[11px] text-[#64748B] mt-0.5">
                          <Clock className="w-3 h-3" />
                          <span>{currentCase.nextStep.time}</span>
                        </div>
                      </div>
                    </div>

                    {currentCase.nextStep.canJoin ? (
                      <button
                        type="button"
                        onClick={handleJoinSession}
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-semibold transition shadow-xs shrink-0"
                      >
                        <Video className="w-3.5 h-3.5" />
                        <span>Join Session</span>
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100 self-start sm:self-center">
                        ✓ Milestone Concluded
                      </span>
                    )}
                  </div>
                )}

                {/* Resources for You Section */}
                <div className="flex flex-col gap-2.5 mt-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433]">
                    <BookOpen className="w-3.5 h-3.5 text-[#6366F1]" />
                    <span>Resources for You</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {currentCase.resources.map((res) => (
                      <div
                        key={res.id}
                        onClick={() => handleOpenResource(res)}
                        className={`${res.bg} border border-gray-100/80 rounded-2xl p-3.5 flex flex-col justify-between cursor-pointer hover:shadow-xs transition group`}
                      >
                        <div className="flex items-start justify-between">
                          <div className={`w-8 h-8 rounded-xl ${res.iconBg} ${res.iconColor} flex items-center justify-center`}>
                            {res.iconType === 'play' && <Play className="w-3.5 h-3.5 fill-current" />}
                            {res.iconType === 'headphones' && <Headphones className="w-3.5 h-3.5" />}
                            {res.iconType === 'document' && <FileText className="w-3.5 h-3.5" />}
                          </div>
                          <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-700 transition" />
                        </div>

                        <div className="mt-3">
                          <h4 className="text-xs font-bold text-[#1E2433] line-clamp-1 group-hover:text-[#4338CA] transition">
                            {res.title}
                          </h4>
                          <span className="text-[11px] text-[#717E95] font-normal mt-0.5 block">
                            {res.duration ? `${res.duration} • ` : ''}{res.type}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB: INTERVENTION PLAN */}
            {detailTab === 'plan' && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <h4 className="text-xs font-bold text-[#1E2433]">Intervention Milestones</h4>
                    <p className="text-[11px] text-[#717E95]">Personalized steps established with your mentor.</p>
                  </div>
                  <span className="text-xs bg-purple-50 text-purple-700 font-semibold px-2.5 py-0.5 rounded-full border border-purple-100">
                    Confidential Academic Support
                  </span>
                </div>

                <div className="flex flex-col gap-2.5">
                  {currentCase.planItems.map((pi, idx) => (
                    <div
                      key={pi.id}
                      className="p-3.5 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex items-start gap-3"
                    >
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                          pi.status === 'completed'
                            ? 'bg-emerald-500 text-white'
                            : pi.status === 'in_progress'
                            ? 'bg-[#6366F1] text-white'
                            : 'bg-gray-100 text-gray-400'
                        }`}
                      >
                        {pi.status === 'completed' && <Check className="w-3.5 h-3.5" />}
                        {pi.status === 'in_progress' && <Clock className="w-3.5 h-3.5" />}
                        {pi.status === 'upcoming' && <span className="text-[10px]">{idx + 1}</span>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#1E2433]">{pi.title}</span>
                          <span className="text-[10px] text-[#717E95] font-medium">{pi.targetDate}</span>
                        </div>
                        <p className="text-xs text-[#64748B] mt-1 leading-relaxed">
                          {pi.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB: NOTES (STRICTLY STUDENT-AUTHORIZED GUIDANCE) */}
            {detailTab === 'notes' && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <h4 className="text-xs font-bold text-[#1E2433]">Mentor Guidance & Action Items</h4>
                    <p className="text-[11px] text-[#717E95]">Official notes shared with you by faculty advisors.</p>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                    <ShieldCheck className="w-3 h-3" />
                    <span>Verified Notes</span>
                  </div>
                </div>

                <div className="flex flex-col gap-2.5">
                  {currentCase.notes.map((note) => (
                    <div
                      key={note.id}
                      className="p-3.5 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-[10px] font-bold">
                            {note.author[0]}
                          </div>
                          <span className="text-xs font-bold text-[#1E2433]">{note.author}</span>
                          <span className="text-[10px] text-gray-400">• {note.role}</span>
                        </div>
                        <span className="text-[11px] text-gray-400">{note.date}</span>
                      </div>
                      <p className="text-xs text-[#475569] leading-relaxed pl-8">
                        {note.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB: TIMELINE */}
            {detailTab === 'timeline' && (
              <div className="flex flex-col gap-3">
                <div className="mb-1">
                  <h4 className="text-xs font-bold text-[#1E2433]">Activity Trail</h4>
                  <p className="text-[11px] text-[#717E95]">Chronological log of check-ins and support milestones.</p>
                </div>

                <div className="flex flex-col gap-3 pl-2">
                  {currentCase.timelineEvents.map((evt, idx) => (
                    <div key={evt.id} className="relative flex items-start gap-3">
                      {idx < currentCase.timelineEvents.length - 1 && (
                        <div className="absolute top-4 left-2 w-0.5 h-full -ml-[1px] bg-gray-200" />
                      )}
                      <div
                        className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 relative z-10 ${
                          evt.status === 'completed'
                            ? 'bg-emerald-500 ring-2 ring-emerald-100'
                            : evt.status === 'active'
                            ? 'bg-[#6366F1] ring-2 ring-purple-100'
                            : 'bg-gray-300 ring-2 ring-gray-100'
                        }`}
                      />
                      <div className="flex flex-col flex-1 pb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#1E2433]">{evt.title}</span>
                          <span className="text-[10px] text-gray-400">{evt.date}</span>
                        </div>
                        <p className="text-xs text-[#64748B] mt-0.5">{evt.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* MODAL 1: VIDEO CONSULTATION SESSION */}
      {isVideoModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Video className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Virtual 1-on-1 Consultation</h3>
                  <p className="text-[11px] text-[#717E95]">With Prof. Sharma (DISHA Secure Room)</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsVideoModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4">
              <div className="relative aspect-video rounded-2xl bg-gray-900 overflow-hidden flex items-center justify-center">
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
                  alt="Camera Preview"
                  className="w-full h-full object-cover opacity-80"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent flex items-end justify-between p-3">
                  <span className="text-xs font-semibold text-white">Asha Verma (You)</span>
                  <div className="flex items-center gap-1.5">
                    <span className="w-6 h-6 rounded-full bg-white/20 text-white flex items-center justify-center">
                      <Mic className="w-3.5 h-3.5" />
                    </span>
                    <span className="w-6 h-6 rounded-full bg-white/20 text-white flex items-center justify-center">
                      <Camera className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 rounded-2xl p-3 border border-purple-100 text-xs text-purple-900 flex items-start gap-2">
                <Sparkles className="w-4 h-4 shrink-0 text-purple-600 mt-0.5" />
                <span>
                  Prof. Sharma is ready in the virtual room. Your microphone and camera permissions are verified.
                </span>
              </div>
            </div>

            <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsVideoModalOpen(false)}
                className="px-4 py-2 rounded-full text-xs font-semibold text-gray-600 hover:bg-gray-200/60 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsVideoModalOpen(false)
                  addToast('Joining Session', 'Connecting to Prof. Sharma in DISHA Secure Room...', 'success')
                }}
                className="px-5 py-2 rounded-full text-xs font-bold text-white bg-[#1E2433] hover:bg-[#2C3549] transition shadow-xs flex items-center gap-1.5"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Enter Room</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: RESOURCE VIEWER */}
      {selectedResource && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`w-8 h-8 rounded-xl ${selectedResource.iconBg} ${selectedResource.iconColor} flex items-center justify-center`}>
                  {selectedResource.iconType === 'play' && <Play className="w-4 h-4 fill-current" />}
                  {selectedResource.iconType === 'headphones' && <Headphones className="w-4 h-4" />}
                  {selectedResource.iconType === 'document' && <FileText className="w-4 h-4" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">{selectedResource.title}</h3>
                  <span className="text-[11px] text-[#717E95]">
                    {selectedResource.duration ? `${selectedResource.duration} • ` : ''}{selectedResource.type}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedResource(null)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-3">
              <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs text-[#334155] leading-relaxed">
                {selectedResource.content}
              </div>

              <div className="flex items-center gap-2 text-xs text-[#64748B]">
                <Clock className="w-3.5 h-3.5 text-gray-400" />
                <span>Estimated reading/listening duration: {selectedResource.duration || '3 min'}</span>
              </div>
            </div>

            <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedResource(null)}
                className="px-4 py-2 rounded-full text-xs font-semibold text-gray-600 hover:bg-gray-200/60 transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedResource(null)
                  addToast('Resource Saved', `Added "${selectedResource.title}" to your offline self-care library.`, 'success')
                }}
                className="px-4 py-2 rounded-full text-xs font-bold text-white bg-[#6366F1] hover:bg-[#4F46E5] transition shadow-xs flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Save to Library</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

