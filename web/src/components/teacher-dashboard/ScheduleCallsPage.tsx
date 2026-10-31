import React, { useState } from 'react'
import { CircleHelp, Bell } from 'lucide-react'
import { ScheduleStats } from './ScheduleStats'
import { ScheduleToolbar, ScheduleViewTab, SessionCategory } from './ScheduleToolbar'
import { WeeklyCalendar, CalendarEventItem, INITIAL_CALENDAR_EVENTS } from './WeeklyCalendar'
import { ScheduleRightPanel, PendingRequest } from './ScheduleRightPanel'
import { ScheduleSessionModal } from './ScheduleSessionModal'
import { useApp } from '../../context/AppContext'

export function ScheduleCallsPage() {
  const { addToast } = useApp()
  const [viewTab, setViewTab] = useState<ScheduleViewTab>('my-schedule')
  const [selectedCategory, setSelectedCategory] = useState<SessionCategory>('all')
  const [calendarView, setCalendarView] = useState<'week' | 'month'>('week')
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedDayIndex, setSelectedDayIndex] = useState(1) // Tuesday 02 Jan
  const [events, setEvents] = useState<CalendarEventItem[]>(INITIAL_CALENDAR_EVENTS)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Filter events by selected category
  const filteredEvents = events.filter((e) => {
    if (selectedCategory === 'all') return true
    if (selectedCategory === 'mentor') return e.category === 'mentor' || e.category === '1-on-1'
    if (selectedCategory === 'review') return e.category === 'review'
    if (selectedCategory === 'intervention') return e.category === 'intervention'
    return true
  })

  // Date range label calculation
  const getDateRangeLabel = () => {
    if (weekOffset === 0) return '01 – 07 January 2025'
    if (weekOffset === 1) return '08 – 14 January 2025'
    if (weekOffset === -1) return '25 – 31 December 2024'
    return `Week ${weekOffset > 0 ? '+' : ''}${weekOffset}`
  }

  const handlePrevWeek = () => {
    setWeekOffset((prev) => prev - 1)
  }

  const handleNextWeek = () => {
    setWeekOffset((prev) => prev + 1)
  }

  const handleToday = () => {
    setWeekOffset(0)
    setSelectedDayIndex(1)
  }

  const handleSaveSession = (newSession: {
    title: string
    student: string
    date: string
    time: string
    type: 'mentor' | 'review' | '1-on-1' | 'intervention' | 'other'
  }) => {
    const colorMap: Record<string, CalendarEventItem['color']> = {
      mentor: 'blue',
      review: 'purple',
      '1-on-1': 'green',
      intervention: 'blue',
      other: 'yellow',
    }

    const newEvent: CalendarEventItem = {
      id: `evt-${Date.now()}`,
      title: newSession.title,
      student: newSession.student,
      time: newSession.time,
      dayIndex: selectedDayIndex,
      startHour: 11.0,
      durationHours: 0.8,
      category: newSession.type,
      color: colorMap[newSession.type] || 'blue',
    }

    setEvents((prev) => [...prev, newEvent])
    addToast(
      'Session Scheduled!',
      `Scheduled "${newSession.title}" with ${newSession.student}.`,
      'success'
    )
  }

  const handleStartInstantCall = () => {
    addToast(
      'Starting Instant Call Room',
      'Connecting to WebRTC live audio/video node...',
      'info'
    )
  }

  const handleAcceptRequest = (req: PendingRequest) => {
    addToast(
      'Request Accepted',
      `Confirmed appointment for "${req.title}".`,
      'success'
    )
  }

  const handleDeclineRequest = (req: PendingRequest) => {
    addToast(
      'Request Declined',
      `Removed pending request for "${req.title}".`,
      'info'
    )
  }

  return (
    <>
      {/* Center Main Schedule Section */}
      <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-1">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
              Schedule &amp; Calls
            </h1>
            <p className="text-xs text-[#717E95] font-medium mt-1">
              Manage your consultations, mentor sessions and faculty calls
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Help button */}
            <button
              type="button"
              aria-label="Help and resources"
              className="flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-sm transition"
            >
              <CircleHelp className="w-4 h-4" />
            </button>

            {/* Notification bell */}
            <button
              type="button"
              aria-label="Notifications"
              className="relative flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] hover:shadow-sm transition"
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

        {/* Statistics Cards Row */}
        <section aria-label="Schedule statistics">
          <ScheduleStats
            todaySessions={4}
            upcomingCalls={7}
            pendingRequests={2}
          />
        </section>

        {/* Schedule Toolbar (Week nav, views, filter pills) */}
        <section aria-label="Schedule controls">
          <ScheduleToolbar
            viewTab={viewTab}
            onViewTabChange={setViewTab}
            dateRangeLabel={getDateRangeLabel()}
            onPrevWeek={handlePrevWeek}
            onNextWeek={handleNextWeek}
            onToday={handleToday}
            calendarView={calendarView}
            onCalendarViewChange={setCalendarView}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />
        </section>

        {/* Main Weekly Calendar Grid */}
        <section aria-label="Weekly calendar" className="flex-1">
          <WeeklyCalendar
            events={filteredEvents}
            selectedDayIndex={selectedDayIndex}
            onSelectDay={setSelectedDayIndex}
            onEventClick={(evt) => {
              addToast(
                evt.title,
                `${evt.student ? `${evt.student} • ` : ''}${evt.time}`,
                'info'
              )
            }}
          />
        </section>
      </main>

      {/* Right-Side Dedicated Schedule Panel */}
      <ScheduleRightPanel
        onScheduleClick={() => setIsModalOpen(true)}
        onInstantCallClick={handleStartInstantCall}
        onAcceptRequest={handleAcceptRequest}
        onDeclineRequest={handleDeclineRequest}
      />

      {/* Interactive Schedule a Session Modal */}
      <ScheduleSessionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaveSession={handleSaveSession}
      />
    </>
  )
}

