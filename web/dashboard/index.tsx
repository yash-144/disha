import React, { useState } from 'react'
import {
  CalendarDays,
  GraduationCap,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Briefcase,
  BookOpen,
  Menu,
  Search,
  Mail,
  Bell,
  LogOut,
  FileText,
  Settings,
  Monitor,
  Lock,
  Pencil,
  Highlighter,
  Circle,
  Square,
  Type,
  AlignJustify,
  Save,
  Eraser,
  Maximize2,
  Check,
  User,
  MoreVertical,
  KeyRound,
  Users,
  LayoutDashboard,
} from 'lucide-react'

export const args = {
  firstName: 'Joseph',
  fullName: 'Joseph jackbon',
  activeStudents: 20,
  board: 'White Board',
}

export const argTypes = {
  firstName: { control: 'text' },
  fullName: { control: 'text' },
  activeStudents: { control: 'number' },
  board: { control: 'radio', options: ['White Board', 'Literacy'] },
}

type Props = Partial<typeof args> & { onLogout?: () => void }

const AVATAR = 'https://cdn.magicpatterns.com/patterns/generated-images/9019b6fb-e381-4430-9866-47a59a2c7012.jpg'

export default function Dashboard(props: Props) {
  const { firstName, fullName, activeStudents, board, onLogout } = { ...args, ...props }
  const [tab, setTab] = useState(board)
  const [color, setColor] = useState(0)

  return (
    <div className="flex min-h-full w-full items-start justify-center bg-[#f5f7fc] p-3 font-sans text-ink sm:p-8 lg:p-12">
      <div className="flex w-full max-w-[1180px] rounded-[40px] bg-royal p-2.5 sm:p-3">
        {/* Sidebar */}
        <aside className="hidden w-[220px] shrink-0 flex-col pb-6 pt-6 text-white lg:flex">
          <div className="flex flex-col items-center">
            <img src={AVATAR} alt={fullName} className="h-[76px] w-[76px] rounded-xl border-[3px] border-white/80 object-cover" />
            <p className="mt-3 text-sm font-semibold">{fullName}</p>
          </div>

          <div className="relative mt-8">
            <div className="flex items-center gap-3 rounded-l-xl bg-white py-3.5 pl-9 text-sm font-medium text-royal -mr-3">
              <LayoutDashboard className="h-4 w-4" /> Dashboard
            </div>
          </div>

          <nav className="mt-6 space-y-4 pl-4 pr-3 text-[13px]">
            {NAV.map((g) => {
              const Icon = g.icon
              return (
                <div key={g.label}>
                  <div className="flex items-center gap-3 font-medium">
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="flex-1">{g.label}</span>
                    {g.items.length > 0 && <ChevronUp className="h-3.5 w-3.5" />}
                  </div>
                  {g.items.length > 0 && (
                    <ul className="mt-1.5 space-y-1.5 pl-7 text-[11px] text-white/90">
                      {g.items.map((it) => (
                        <li key={it}>{it}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })}
          </nav>

          <div className="mt-auto pl-9 pt-10 text-[9px] leading-relaxed text-white/80">
            <p>© 2020 All rights reserved</p>
            <p>
              <span className="underline">Privacy Policy</span> &amp; <span className="underline">Terms of Use</span>
            </p>
          </div>
        </aside>

        {/* Main */}
        <main className="min-w-0 flex-1 rounded-[32px] bg-white px-5 pb-6 pt-7 sm:px-8 sm:pt-9">
          <header className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="whitespace-nowrap text-2xl font-light sm:text-[28px]">
              Welcome, <span className="font-medium">{firstName}</span>
            </h1>
            <div className="flex flex-wrap items-center gap-3">
              <button className="whitespace-nowrap rounded-sm bg-royal px-6 py-2 text-[10px] font-medium text-white transition-colors duration-150 hover:bg-blue-700">
                Live Instructor
              </button>
              <div className="flex w-40 items-center rounded-md bg-[#f1f4fb] px-3 py-2 text-[10px] text-gray-400 sm:w-44">
                <input placeholder="Search..." className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-gray-400" />
                <Search className="h-3.5 w-3.5 text-gray-600" />
              </div>
              <IconBadge icon={<Mail className="h-3.5 w-3.5" />} />
              <IconBadge icon={<Bell className="h-3.5 w-3.5" />} />
              <button onClick={onLogout} aria-label="Log out" className="p-1 text-gray-700">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </header>

          {/* Quick tiles */}
          <div className="mt-6 grid grid-cols-2 gap-4 xl:grid-cols-4 xl:gap-5">
            {TILES.map((t) => {
              const Icon = t.icon
              return (
                <button
                  key={t.label}
                  className="flex items-center gap-3 rounded-[14px] rounded-br-[36px] bg-white px-4 py-6 text-left shadow-[0_4px_18px_rgba(30,50,110,0.10)] transition-shadow duration-200 hover:shadow-[0_6px_24px_rgba(30,50,110,0.16)] sm:px-6"
                >
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${t.bg}`}>
                    <Icon className={`h-4 w-4 ${t.color}`} />
                  </span>
                  <span className="whitespace-nowrap text-sm font-medium sm:text-base">{t.label}</span>
                </button>
              )
            })}
          </div>

          {/* Whiteboard + side */}
          <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_240px]">
            <section className="rounded-md bg-white p-3 shadow-[0_2px_14px_rgba(30,50,110,0.10)]">
              <div className="flex flex-wrap items-center justify-between gap-2 px-2">
                <h2 className="text-sm font-medium">Live Instrutor</h2>
                <div className="flex text-[9px]">
                  {(['White Board', 'Literacy'] as const).map((b) => (
                    <button
                      key={b}
                      onClick={() => setTab(b)}
                      className={`flex items-center gap-1.5 whitespace-nowrap px-4 py-2 transition-colors duration-150 ${
                        tab === b ? 'bg-royal text-white' : 'border border-gray-200 text-gray-400'
                      }`}
                    >
                      {b === 'White Board' ? <Monitor className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
                      {b}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-3 rounded-md border border-gray-200 px-4 py-2">
                {['#111111', '#6c4ce0', '#ef4444', '#34c38f'].map((c, i) => (
                  <button
                    key={c}
                    onClick={() => setColor(i)}
                    aria-label={`Color ${i + 1}`}
                    className={`h-3 w-3 rounded-full ${color === i ? 'ring-2 ring-offset-1 ring-gray-300' : ''}`}
                    style={{ backgroundColor: c }}
                  />
                ))}
                <div className="relative ml-6 hidden h-0.5 w-20 rounded bg-gray-200 sm:block">
                  <span className="absolute -top-[5px] left-1/4 h-3 w-3 rounded-full bg-royal" />
                  <span className="absolute left-0 top-0 h-0.5 w-1/4 bg-royal" />
                </div>
                <div className="ml-auto flex items-center gap-3 text-gray-500">
                  <Pencil className="h-3.5 w-3.5" />
                  <Highlighter className="h-3.5 w-3.5 text-violet-600" />
                  <Circle className="h-3.5 w-3.5" />
                  <Square className="h-3.5 w-3.5" />
                  <Type className="h-3.5 w-3.5" />
                  <AlignJustify className="h-3.5 w-3.5" />
                  <Save className="h-3.5 w-3.5" />
                  <Eraser className="h-3.5 w-3.5" />
                </div>
              </div>
              <div className="relative mt-2 h-44 rounded-md border border-gray-200 sm:h-[150px]">
                <Maximize2 className="absolute bottom-2 right-2 h-3 w-3 text-gray-400" />
              </div>
            </section>

            <div className="flex flex-col gap-3">
              <section className="rounded-md bg-white shadow-[0_2px_14px_rgba(30,50,110,0.10)]">
                <h3 className="border-b border-gray-100 px-3 py-2.5 text-[11px] font-medium">Search Classes</h3>
                <div className="space-y-2.5 p-3">
                  <input
                    placeholder="What your Looking for?"
                    className="w-full rounded-sm border border-gray-200 px-2.5 py-2 text-[10px] outline-none placeholder:text-gray-500 focus:border-royal"
                  />
                  <div className="flex items-center justify-between rounded-sm border border-gray-200 px-2.5 py-2 text-[10px] text-gray-600">
                    Business &amp; Management <ChevronDown className="h-3 w-3 text-gray-400" />
                  </div>
                  <button className="rounded-sm bg-royal px-6 py-2 text-[10px] font-medium text-white transition-colors duration-150 hover:bg-blue-700">
                    Search
                  </button>
                </div>
              </section>
              <section className="rounded-md bg-white shadow-[0_2px_14px_rgba(30,50,110,0.10)]">
                <h3 className="border-b border-gray-100 px-3 py-2.5 text-[11px] font-medium">Grecon Safety Tips</h3>
                <ul className="space-y-1.5 p-3 text-[9px] text-gray-700">
                  {TIPS.map((t) => (
                    <li key={t} className="flex items-center gap-1.5">
                      <Check className="h-3 w-3 text-green-600" strokeWidth={3} /> {t}
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>

          {/* Classes */}
          <h2 className="mt-5 text-sm font-medium">Classes</h2>
          <div className="mt-2 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <article key={i} className="flex flex-col rounded-md bg-white p-4 shadow-[0_2px_14px_rgba(30,50,110,0.10)]">
                <div className="flex items-start gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#eef1fb] text-royal">
                    <User className="h-4 w-4" />
                  </span>
                  <div className="flex-1">
                    <p className="text-base leading-tight">Test</p>
                    <p className="text-[10px] text-gray-500">122</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <MoreVertical className="h-4 w-4 text-gray-700" />
                    <span className="text-[8px] text-gray-400">D. Peterson</span>
                  </div>
                </div>
                <p className="mt-6 flex items-center gap-1 text-[10px] text-gray-700">
                  <KeyRound className="h-3 w-3 text-amber-500" /> Access Code:{' '}
                  <span className="text-royal">3mia24z9x0</span>
                </p>
                <p className="mt-0.5 text-[9px] text-gray-500">Term: Jun 1, 2020 - Jun 30, 2020</p>
                <p className="mb-5 mt-2 flex items-center gap-1 text-[10px] text-green-600">
                  <Users className="h-3 w-3" /> {activeStudents} active students.
                </p>
                <p className="mt-auto border-t border-gray-100 pt-3 text-[8px] text-gray-500">
                  Created: May 30, 2020 9:33 PM
                </p>
              </article>
            ))}
          </div>
          <div className="mt-3 flex justify-end">
            <button className="flex items-center gap-1 text-[10px] text-royal">
              See all <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </main>
      </div>
    </div>
  )
}

function IconBadge({ icon }: { icon: React.ReactNode }) {
  return (
    <button className="relative flex h-8 w-8 items-center justify-center rounded-md bg-[#f1f4fb] text-gray-700">
      {icon}
      <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-royal" />
    </button>
  )
}

const NAV = [
  { label: 'Courses List', icon: GraduationCap, items: ['Marco economics', 'Literature', 'Physhology', 'Global study'] },
  { label: 'Courses', icon: GraduationCap, items: ['All Courses', 'Add Course'] },
  { label: 'Management', icon: Briefcase, items: [] as string[] },
  { label: 'Classes', icon: BookOpen, items: ['All Classes', 'Add New Class'] },
  {
    label: 'Menu',
    icon: Menu,
    items: ['Shedule', 'Roster/Attendence', 'Syllabus', 'Lesson Plan', 'Quizes/Tests', 'Gradebook', 'Resources', 'Support Request'],
  },
]

const TILES = [
  { label: 'Courses', icon: GraduationCap, bg: 'bg-teal-50', color: 'text-teal-500' },
  { label: 'Reporting', icon: FileText, bg: 'bg-violet-50', color: 'text-violet-500' },
  { label: 'Calender', icon: CalendarDays, bg: 'bg-red-50', color: 'text-red-500' },
  { label: 'Settings', icon: Settings, bg: 'bg-sky-50', color: 'text-sky-500' },
]

const TIPS = ['Keep Personal Info Private', 'Always Check Reviews', 'Have an adult present', 'Always check updates']
