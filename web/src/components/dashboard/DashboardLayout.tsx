import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  GraduationCap,
  BookOpen,
  Menu,
  Search,
  Bell,
  LogOut,
  ChevronUp,
  ChevronDown,
  ArrowLeft,
  X,
  Radio,
  Calendar,
  Users,
  Award,
  Sparkles,
  Maximize2,
  Minimize2,
  PanelLeftClose,
  PanelLeft,
  Settings,
  HelpCircle,
  FileSpreadsheet,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { DashboardTab } from '../../types'
import { OverviewTab } from './OverviewTab'
import { CoursesTab } from './CoursesTab'
import { ClassesTab } from './ClassesTab'
import { RosterTab } from './RosterTab'
import { QuizzesTab } from './QuizzesTab'
import { GradebookTab } from './GradebookTab'
import { ScheduleTab } from './ScheduleTab'
import { ResourcesTab } from './ResourcesTab'
import { SettingsTab } from './SettingsTab'

export function DashboardLayout() {
  const {
    currentUser,
    dashboardTab,
    setDashboardTab,
    navigateTo,
    addToast,
    userRole,
    switchRole,
    activeClasses,
  } = useApp()

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [fitScreen, setFitScreen] = useState(true)
  const [showNotifications, setShowNotifications] = useState(false)
  const [currentTime, setCurrentTime] = useState('')
  const [globalSearch, setGlobalSearch] = useState('')

  const [notifications, setNotifications] = useState([
    { id: '1', title: 'A student submitted a capstone PR', time: '2m ago', unread: true },
    { id: '2', title: 'Weekly Assessment Report ready for review', time: '45m ago', unread: true },
    { id: '3', title: 'A student scored 98% in React Canvas Lab', time: '2h ago', unread: false },
  ])

  // Live dynamic clock for top cockpit bar
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const firstName = currentUser.name.split(' ')[0]

  const handleLogout = () => {
    addToast('Signed Out', 'You have exited the LMS instructor workstation.', 'info')
    navigateTo('landing')
  }

  const handleTabClick = (tabId: DashboardTab) => {
    setDashboardTab(tabId)
    setMobileMenuOpen(false)
  }

  return (
    <div
      className={`relative w-full ${
        fitScreen
          ? 'h-screen max-h-screen overflow-hidden'
          : 'min-h-screen'
      } bg-[#090f20] p-1 sm:p-2.5 md:p-3.5 font-mono text-ink transition-all duration-300 flex flex-col`}
    >
      {/* Outer Dynamic Royal Blue Frame wrapping screen */}
      <div
        className={`relative flex flex-1 flex-col lg:flex-row overflow-hidden rounded-[20px] sm:rounded-[28px] md:rounded-[34px] border-[3px] sm:border-4 border-ink bg-gradient-to-br from-accent via-[#164db6] to-accent-dark p-1.5 sm:p-2.5 shadow-[0_0_35px_rgba(29,95,209,0.35),6px_6px_0_#0d1b3e] dynamic-blue-frame transition-all duration-300`}
      >
        {/* Subtle Blueprint grid texture overlay on the blue frame */}
        <div className="pointer-events-none absolute inset-0 opacity-15 bg-grid-blueprint-dark rounded-[inherit]" />

        {/* Dynamic Frame Status Bar (Top Mini Strip) */}
        <div className="relative z-10 flex items-center justify-between px-3 py-1 text-xs text-white/80 lg:hidden border-b border-white/10 mb-1">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            <span className="font-bold tracking-wider">DISHA COCKPIT</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-white/70">{currentTime}</span>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded border border-white/20 bg-white/10 p-1 text-white hover:bg-white/20"
              aria-label="Toggle Navigation"
            >
              <Menu className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* SIDEBAR */}
        <aside
          className={`${
            mobileMenuOpen ? 'flex fixed inset-y-0 left-0 z-50 w-72 bg-[#123e94] p-4 shadow-2xl' : 'hidden'
          } lg:flex shrink-0 flex-col py-2 sm:py-3 text-white transition-all duration-300 ease-in-out relative z-20 ${
            sidebarCollapsed ? 'lg:w-[72px] lg:px-2' : 'lg:w-[230px] lg:px-3'
          }`}
        >
          {/* Top Brand & Profile Capsule */}
          <div className="flex flex-col items-center">
            {/* Header branding / Logo */}
            <div className="flex w-full items-center justify-between pb-2 border-b border-white/15">
              {!sidebarCollapsed ? (
                <button
                  onClick={() => navigateTo('landing')}
                  className="flex items-center gap-1.5 text-left group"
                  title="Return to Public Site"
                >
                  <span className="rounded bg-accent px-1.5 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                    v2.0
                  </span>
                  <span className="text-sm font-bold tracking-tight text-white group-hover:text-emerald-300 transition-colors">
                    Skills<span className="text-emerald-400">Up</span>
                  </span>
                </button>
              ) : (
                <div className="mx-auto">
                  <span className="rounded bg-accent px-1.5 py-0.5 text-xs font-bold text-white">
                    SU
                  </span>
                </div>
              )}

              {/* Sidebar Collapse Toggle (Desktop only) */}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="hidden lg:flex h-6 w-6 items-center justify-center rounded border border-white/30 bg-white/10 text-white hover:bg-white/20 transition"
                title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              >
                {sidebarCollapsed ? <PanelLeft className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
              </button>

              {/* Mobile Close Button */}
              {mobileMenuOpen && (
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="lg:hidden rounded border border-white/20 p-1 text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* User Profile Card */}
            <div className={`mt-3 flex w-full items-center ${sidebarCollapsed ? 'justify-center' : 'gap-2.5'} rounded-xl border border-white/20 bg-white/10 p-2 backdrop-blur-xs`}>
              <div className="relative shrink-0">
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  className="h-10 w-10 rounded-lg border-2 border-white object-cover shadow-sm"
                />
                <span className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-brand bg-accent animate-pulse" />
              </div>

              {!sidebarCollapsed && (
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-bold leading-snug">{currentUser.name}</p>
                  <div className="mt-0.5 flex items-center gap-1.5">
                    <span className="inline-block rounded bg-accent px-1.5 py-0.2 text-xs font-bold uppercase text-white shadow-xs">
                      {userRole}
                    </span>
                    <span className="text-xs text-white/70">· Online</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Navigation Pill List */}
          <nav className="mt-4 flex-1 space-y-1.5 overflow-y-auto pr-1 text-xs">
            {/* Overview / Dashboard */}
            <button
              onClick={() => handleTabClick('overview')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'overview'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Overview & Canvas"
            >
              <LayoutDashboard className={`h-4 w-4 shrink-0 ${dashboardTab === 'overview' ? 'text-brand' : ''}`} />
              {!sidebarCollapsed && <span>Dashboard</span>}
            </button>

            {/* Courses Tab */}
            <button
              onClick={() => handleTabClick('courses-list')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'courses-list' || dashboardTab === 'all-courses' || dashboardTab === 'add-course'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Courses & Curriculums"
            >
              <GraduationCap className={`h-4 w-4 shrink-0 ${dashboardTab === 'courses-list' ? 'text-brand' : ''}`} />
              {!sidebarCollapsed && <span>Courses</span>}
            </button>

            {/* Classes Tab */}
            <button
              onClick={() => handleTabClick('all-classes')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'all-classes' || dashboardTab === 'add-class'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Live Cohort Classes"
            >
              <BookOpen className={`h-4 w-4 shrink-0 ${dashboardTab === 'all-classes' ? 'text-brand' : ''}`} />
              {!sidebarCollapsed && <span>Live Cohorts</span>}
            </button>

            {/* Schedule */}
            <button
              onClick={() => handleTabClick('schedule')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'schedule'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Cohort Schedule"
            >
              <Calendar className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>Schedule</span>}
            </button>

            {/* Roster & Attendance */}
            <button
              onClick={() => handleTabClick('roster')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'roster'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Students Roster"
            >
              <Users className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>Learner Roster</span>}
            </button>

            {/* Quizzes & Assessments */}
            <button
              onClick={() => handleTabClick('quizzes')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'quizzes'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Quizzes & Tests"
            >
              <Award className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>Quizzes</span>}
            </button>

            {/* Gradebook */}
            <button
              onClick={() => handleTabClick('gradebook')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'gradebook'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Gradebook & Analytics"
            >
              <FileSpreadsheet className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>Gradebook</span>}
            </button>

            {/* Settings */}
            <button
              onClick={() => handleTabClick('settings')}
              className={`flex w-full items-center gap-2.5 rounded-lg border-2 px-3 py-2 text-left font-bold transition-all ${
                dashboardTab === 'settings'
                  ? 'border-ink bg-white text-ink shadow-[3px_3px_0_#0d1b3e] -translate-y-0.5'
                  : 'border-transparent text-white/90 hover:bg-white/10 hover:border-white/20'
              }`}
              title="Workstation Settings"
            >
              <Settings className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>Settings</span>}
            </button>
          </nav>

          {/* Quick Return to Public Site CTA & Session Indicator */}
          <div className="mt-auto space-y-2 pt-3 border-t border-white/15">
            {!sidebarCollapsed ? (
              <div className="rounded-lg border border-white/20 bg-white/10 p-2.5 text-xs text-white">
                <div className="flex items-center justify-between font-bold">
                  <span className="flex items-center gap-1.5 text-emerald-300">
                    <Radio className="h-3 w-3 animate-pulse" /> Live Node
                  </span>
                  <span className="text-xs text-white/70 font-mono">100% Synced</span>
                </div>
                <p className="mt-1 text-xs text-white/80 leading-tight">
                  Active Room: <span className="font-bold text-white">CS402-React</span>
                </p>
              </div>
            ) : (
              <div className="flex justify-center" title="Live Node Active">
                <span className="h-3 w-3 rounded-full bg-accent animate-pulse" />
              </div>
            )}

            <button
              onClick={() => navigateTo('landing')}
              className={`flex w-full items-center ${
                sidebarCollapsed ? 'justify-center' : 'justify-center gap-2'
              } rounded-lg border-2 border-ink bg-white px-3 py-2 text-xs font-bold text-ink shadow-[2.5px_2.5px_0_#0d1b3e] transition hover:bg-gray-100 hover:translate-x-0.5`}
              title="Return to Public Landing Page"
            >
              <ArrowLeft className="h-3.5 w-3.5 text-brand" />
              {!sidebarCollapsed && <span>Public Site</span>}
            </button>
          </div>
        </aside>

        {/* MAIN WORKSPACE SURFACE (Neo-Brutal Canvas inside Royal Blue Frame) */}
        <main className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden rounded-[16px] sm:rounded-[24px] md:rounded-[28px] border-2 sm:border-3 border-ink bg-paper shadow-sm">
          {/* TOP COCKPIT CONTROLS HEADER */}
          <header className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-ink bg-white px-4 py-3 sm:px-6 shadow-xs">
            {/* Title / Greeting with Live Breadcrumb */}
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-accent px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                  LMS COCKPIT
                </span>
                <span className="hidden text-xs text-muted sm:inline font-mono">
                  / {dashboardTab.replace('-', ' ').toUpperCase()}
                </span>
              </div>
              <h1 className="mt-1 text-lg font-bold leading-none tracking-tight text-ink sm:text-2xl">
                Welcome back, <span className="text-brand">{firstName}</span>!
              </h1>
            </div>

            {/* Quick Actions & Dynamic Controls */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              {/* Quick Search */}
              <div className="hidden md:flex items-center rounded-lg border-2 border-ink bg-paper px-2.5 py-1.5 text-xs shadow-[2px_2px_0_#0d1b3e]">
                <Search className="mr-1.5 h-3.5 w-3.5 text-gray-500" />
                <input
                  value={globalSearch}
                  onChange={(e) => setGlobalSearch(e.target.value)}
                  placeholder="Quick search cohorts..."
                  className="w-32 bg-transparent text-xs font-medium text-ink outline-none placeholder:text-gray-400 lg:w-44"
                />
                <span className="ml-1 rounded border border-gray-300 bg-white px-1 text-xs font-mono font-bold text-gray-500">
                  ⌘K
                </span>
              </div>

              {/* Dynamic Interactive Role Switcher */}
              <div className="flex items-center rounded-lg border-2 border-ink bg-white p-0.5 shadow-[2px_2px_0_#0d1b3e]">
                <button
                  onClick={() => switchRole('instructor')}
                  title="Switch to Instructor Tools"
                  className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-bold transition ${
                    userRole === 'instructor'
                      ? 'bg-brand text-white shadow-xs'
                      : 'text-gray-600 hover:text-black'
                  }`}
                >
                  <span>👨‍🏫 Instructor</span>
                </button>
                <button
                  onClick={() => switchRole('student')}
                  title="Switch to Student Dashboard"
                  className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-bold transition ${
                    userRole === 'student'
                      ? 'bg-accent text-white shadow-xs'
                      : 'text-gray-600 hover:text-black'
                  }`}
                >
                  <span>🎓 Student</span>
                </button>
              </div>

              {/* Dynamic Fit-Screen Viewport Wrap Toggle */}
              <button
                onClick={() => {
                  setFitScreen(!fitScreen)
                  addToast(
                    fitScreen ? 'Expanded Natural Height' : 'Viewport Wrap Locked',
                    fitScreen ? 'Dashboard will expand naturally with page.' : 'Screen wrapped tightly to viewport.',
                    'info'
                  )
                }}
                className="hidden sm:flex h-8 w-8 items-center justify-center rounded-lg border-2 border-ink bg-white text-ink shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100"
                title={fitScreen ? 'Expand page height naturally' : 'Lock screen wrap viewport'}
              >
                {fitScreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </button>

              {/* Notifications Popover */}
              <div className="relative">
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  aria-label="Notifications"
                  className="relative flex h-8 w-8 items-center justify-center rounded-lg border-2 border-ink bg-white text-ink shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100"
                >
                  <Bell className="h-4 w-4" />
                  <span className="absolute -right-1 -top-1 flex h-3 w-3 items-center justify-center rounded-full bg-accent text-[8px] font-bold text-white animate-pulse" />
                </button>

                {showNotifications && (
                  <div className="absolute right-0 top-full z-40 mt-2 w-80 rounded-xl border-2 border-ink bg-white p-3 shadow-[6px_6px_0_#0d1b3e] animate-in fade-in">
                    <div className="flex items-center justify-between border-b-2 border-ink/20 pb-2">
                      <div className="flex items-center gap-1.5 font-bold text-xs">
                        <Sparkles className="h-3.5 w-3.5 text-brand" />
                        <span>System Notifications</span>
                      </div>
                      <button
                        onClick={() => setShowNotifications(false)}
                        className="rounded p-0.5 text-gray-400 hover:text-black"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    <div className="mt-2 space-y-2">
                      {notifications.map((n) => (
                        <div
                          key={n.id}
                          className="rounded-lg border border-gray-100 bg-gray-50/70 p-2 text-xs transition hover:bg-blue-50/50"
                        >
                          <p className="font-bold text-ink">{n.title}</p>
                          <span className="text-xs text-gray-500 font-mono">{n.time}</span>
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={() => {
                        setShowNotifications(false)
                        addToast('All Caught Up', 'All notifications marked as read.', 'info')
                      }}
                      className="mt-3 w-full rounded border-2 border-ink bg-accent py-1 text-center text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark"
                    >
                      Clear All Notifications
                    </button>
                  </div>
                )}
              </div>

              {/* Logout Button */}
              <button
                onClick={handleLogout}
                aria-label="Log out"
                title="Log out of LMS"
                className="flex h-8 w-8 items-center justify-center rounded-lg border-2 border-ink bg-white text-red-600 shadow-[2px_2px_0_#0d1b3e] transition hover:bg-red-50 hover:translate-x-0.5"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          </header>

          {/* DYNAMIC SCROLLABLE CONTENT BODY */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-7 bg-paper bg-grid-pattern">
            {dashboardTab === 'overview' && <OverviewTab />}
            {(dashboardTab === 'courses-list' ||
              dashboardTab === 'all-courses' ||
              dashboardTab === 'add-course') && <CoursesTab />}
            {(dashboardTab === 'all-classes' ||
              dashboardTab === 'add-class' ||
              dashboardTab === 'management') && <ClassesTab />}
            {dashboardTab === 'roster' && <RosterTab />}
            {dashboardTab === 'quizzes' && <QuizzesTab />}
            {dashboardTab === 'gradebook' && <GradebookTab />}
            {dashboardTab === 'schedule' && <ScheduleTab />}
            {dashboardTab === 'resources' && <ResourcesTab />}
            {dashboardTab === 'settings' && <SettingsTab />}
          </div>
        </main>
      </div>
    </div>
  )
}
