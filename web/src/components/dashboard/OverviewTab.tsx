import React, { useState } from 'react'
import {
  GraduationCap,
  FileText,
  CalendarDays,
  Settings,
  Monitor,
  Lock,
  Search,
  Check,
  User,
  MoreVertical,
  KeyRound,
  Users,
  ChevronDown,
  Copy,
  Plus,
  Radio,
  Sparkles,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { InteractiveWhiteboard } from './InteractiveWhiteboard'
import { LiteracyNotes } from './LiteracyNotes'

const TILES = [
  { id: 'courses-list', label: 'Courses & Syllabus', subtitle: 'Manage 8 Tracks', icon: GraduationCap, bg: 'bg-accent', badge: '8 ACTIVE' },
  { id: 'gradebook', label: 'Gradebook & Analytics', subtitle: 'Reports & GPA', icon: FileText, bg: 'bg-brand', badge: 'UPDATED' },
  { id: 'schedule', label: 'Live Schedule', subtitle: 'Sync Calendar', icon: CalendarDays, bg: 'bg-accent', badge: 'TODAY' },
  { id: 'settings', label: 'Workstation Setup', subtitle: 'Audio & Canvas', icon: Settings, bg: 'bg-brand', badge: 'CONFIG' },
]

const TIPS = [
  'Verify audio & screen share bitrate before live cohort starts',
  'Save whiteboard state as snapshot after completing architectural diagrams',
  'Export weekly attendance records to CSV for credential verification',
  'Keep student credentials & room codes secure and cohort-specific',
]

export function OverviewTab() {
  const { activeClasses, setDashboardTab, addToast, userRole } = useApp()
  const [boardTab, setBoardTab] = useState<'whiteboard' | 'literacy'>('whiteboard')
  const [searchClassQuery, setSearchClassQuery] = useState('')
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('Computer Science & IT')

  const copyAccessCode = (code: string) => {
    navigator.clipboard?.writeText?.(code)
    addToast('Access Code Copied!', `Code ${code} copied to clipboard.`, 'success')
  }

  const filteredClasses = activeClasses.filter(
    (c) =>
      !searchClassQuery ||
      c.name.toLowerCase().includes(searchClassQuery.toLowerCase()) ||
      c.code.toLowerCase().includes(searchClassQuery.toLowerCase())
  )

  return (
    <div className="space-y-6 font-mono">
      {/* Quick Action Neo-Brutalist Tiles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {TILES.map((t) => {
          const Icon = t.icon
          return (
            <button
              key={t.label}
              onClick={() => setDashboardTab(t.id as any)}
              className="group relative flex items-center gap-3.5 border-2 border-ink bg-white p-4 text-left shadow-[3px_3px_0_#0d1b3e] transition-all duration-150 hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0_#0d1b3e]"
            >
              <span
                className={`flex h-12 w-12 shrink-0 items-center justify-center border-2 border-ink ${t.bg} text-white shadow-[2px_2px_0_#0d1b3e]`}
              >
                <Icon className="h-6 w-6" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="rounded bg-gray-100 px-1.5 py-0.2 text-xs font-bold text-gray-700">
                    {t.badge}
                  </span>
                </div>
                <span className="mt-1 block truncate text-xs font-bold text-ink sm:text-sm">
                  {t.label}
                </span>
                <span className="text-xs text-muted">{t.subtitle}</span>
              </div>
            </button>
          )
        })}
      </div>

      {/* Main Whiteboard / Literacy + Side Panel */}
      <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
        {/* Left: Interactive Live Whiteboard Section */}
        <section className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-ink/20 pb-3">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 items-center justify-center rounded-full bg-accent animate-pulse" />
              <h2 className="text-sm font-bold text-ink">
                Live Interactive Canvas &amp; Whiteboard
              </h2>
              <span className="rounded bg-brand/10 px-1.5 py-0.5 text-xs font-bold text-brand">
                HTML5 Vector
              </span>
            </div>

            {/* Toggle White Board vs Literacy */}
            <div className="flex rounded border-2 border-ink bg-gray-100 p-0.5 text-xs shadow-[2px_2px_0_#0d1b3e]">
              <button
                onClick={() => setBoardTab('whiteboard')}
                className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-bold transition ${
                  boardTab === 'whiteboard'
                    ? 'border border-ink bg-brand text-white shadow-xs'
                    : 'text-gray-600 hover:text-black'
                }`}
              >
                <Monitor className="h-3 w-3" />
                Drawing Board
              </button>
              <button
                onClick={() => setBoardTab('literacy')}
                className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-bold transition ${
                  boardTab === 'literacy'
                    ? 'border border-ink bg-accent text-white shadow-xs'
                    : 'text-gray-600 hover:text-black'
                }`}
              >
                <Lock className="h-3 w-3" />
                Literacy Notes
              </button>
            </div>
          </div>

          <div className="mt-3">
            {boardTab === 'whiteboard' ? <InteractiveWhiteboard /> : <LiteracyNotes />}
          </div>
        </section>

        {/* Right: Search Classes & Tips */}
        <div className="flex flex-col gap-4">
          {/* Search Cohorts Widget */}
          <section className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
            <div className="flex items-center justify-between border-b-2 border-ink/20 pb-2">
              <h3 className="text-xs font-bold text-ink">Search Cohorts</h3>
              <span className="rounded bg-accent px-1.5 py-0.5 text-xs font-bold text-white">
                LIVE
              </span>
            </div>
            <div className="mt-3 space-y-2.5">
              <div className="relative">
                <input
                  value={searchClassQuery}
                  onChange={(e) => setSearchClassQuery(e.target.value)}
                  placeholder="Filter by code or title..."
                  className="w-full border-2 border-ink bg-paper px-3 py-1.5 text-xs text-ink outline-none placeholder:text-gray-400 focus:bg-white"
                />
              </div>

              <div className="relative">
                <select
                  value={selectedCategoryFilter}
                  onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                  className="w-full appearance-none border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-gray-700 outline-none"
                >
                  <option>Computer Science &amp; IT</option>
                  <option>Data &amp; SQL Engineering</option>
                  <option>Design &amp; Multimedia</option>
                  <option>Cloud Infrastructure</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3.5 w-3.5 text-gray-400" />
              </div>

              <button
                onClick={() =>
                  addToast(
                    'Filter Applied',
                    `Displaying active cohorts in "${selectedCategoryFilter}".`,
                    'info'
                  )
                }
                className="w-full border-2 border-ink bg-accent py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark"
              >
                Apply Track Filter
              </button>
            </div>
          </section>

          {/* Safety & Protocol Tips */}
          <section className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
            <h3 className="border-b-2 border-ink/20 pb-2 text-xs font-bold text-brand">
              Instructor Guidelines &amp; Protocol
            </h3>
            <ul className="mt-3 space-y-2 text-xs text-gray-700">
              {TIPS.map((t, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" strokeWidth={3} />
                  <span className="leading-tight">{t}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      {/* Active Classes Grid Section */}
      <div className="border-2 border-ink bg-white p-4 sm:p-5 shadow-[4px_4px_0_#0d1b3e]">
        <div className="flex items-center justify-between border-b-2 border-ink/20 pb-3">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-accent animate-pulse" />
            <h2 className="text-sm font-bold text-ink sm:text-base">
              Active Cohort Rooms ({filteredClasses.length})
            </h2>
          </div>
          <button
            onClick={() => setDashboardTab('all-classes')}
            className="border-2 border-ink bg-white px-3 py-1 text-xs font-bold text-brand shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100"
          >
            Manage All Classes →
          </button>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredClasses.map((cls) => (
            <article
              key={cls.id}
              className="flex flex-col justify-between border-2 border-ink bg-paper p-4 shadow-[3px_3px_0_#0d1b3e] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_#0d1b3e]"
            >
              <div>
                <div className="flex items-start justify-between">
                  <span className="border border-ink bg-accent px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                    {cls.code}
                  </span>
                  <span className="text-xs font-bold text-gray-500">{cls.instructor}</span>
                </div>

                <h3 className="mt-2 text-sm font-bold text-ink leading-snug">{cls.name}</h3>
                <p className="text-xs text-muted">{cls.subject}</p>
              </div>

              <div className="mt-4 space-y-2 border-t-2 border-ink/10 pt-3">
                <div className="flex items-center justify-between border border-ink/30 bg-white px-2 py-1 text-xs">
                  <span className="flex items-center gap-1 text-gray-700 text-xs">
                    <KeyRound className="h-3 w-3 text-amber-500" />
                    Code: <span className="font-bold text-brand">{cls.accessCode}</span>
                  </span>
                  <button
                    onClick={() => copyAccessCode(cls.accessCode)}
                    title="Copy Access Code"
                    className="border border-ink bg-gray-100 px-1.5 py-0.5 text-xs font-bold text-ink hover:bg-gray-200"
                  >
                    Copy
                  </button>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span className="flex items-center gap-1 font-bold text-accent">
                    <Users className="h-3 w-3" /> {cls.activeStudents} Learners
                  </span>
                  <span className="rounded bg-emerald-100 px-1.5 py-0.2 font-bold text-emerald-800">
                    Live Session
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
