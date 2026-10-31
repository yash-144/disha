import React, { useState } from 'react'
import { CounsellorWelcome } from './CounsellorWelcome'
import { CounsellorStats } from './CounsellorStats'
import { CaseLoadTrend } from './CaseLoadTrend'
import { CasesByFocusArea } from './CasesByFocusArea'
import { StudentsNeedingAttention } from './StudentsNeedingAttention'
import { TodaysSchedule } from './TodaysSchedule'
import { QuickActions } from './QuickActions'
import { WellbeingInsights } from './WellbeingInsights'
import { WeeklyFocusChecklist } from './WeeklyFocusChecklist'
import { CounsellorScenarioData, CounsellorStudentItem, CounsellorAppointment } from './counsellorDemoData'
import { X, Calendar, Video, ShieldCheck, User } from 'lucide-react'

interface CounsellorOverviewProps {
  scenario: CounsellorScenarioData
  onNavigateToSchedule?: () => void
  onNavigateToStudentsInNeed?: () => void
  onNavigateToSupportCases?: () => void
}

export function CounsellorOverview({
  scenario,
  onNavigateToSchedule,
  onNavigateToStudentsInNeed,
  onNavigateToSupportCases,
}: CounsellorOverviewProps) {
  // Modal states for interactive Quick Actions & Item clicks
  const [activeModal, setActiveModal] = useState<
    | { type: 'student'; student: CounsellorStudentItem }
    | { type: 'appointment'; appointment: CounsellorAppointment }
    | { type: 'quickAction'; title: string; desc: string }
    | null
  >(null)

  return (
    <div className="flex flex-col gap-4.5 font-sans select-none pb-8 animate-in fade-in duration-200">
      {/* 1. Welcome Section & Motivational Banner */}
      <CounsellorWelcome name={scenario.greetingName} />

      {/* 2. Four Statistics Cards */}
      <CounsellorStats stats={scenario.stats} />

      {/* 3. Main Operational Content: Left 2x2 Grid + Right Vertical Column */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4.5 items-start">
        {/* LEFT COLUMN: 2x2 Operational Workspaces (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4.5">
          {/* Middle Row: Case Load Trend + Cases by Focus Area */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4.5">
            <CaseLoadTrend
              dataPoints={scenario.caseLoadTrend.dataPoints}
              weekLabels={scenario.caseLoadTrend.weekLabels}
              maxY={scenario.caseLoadTrend.maxY}
            />

            <CasesByFocusArea
              totalCases={scenario.casesByFocusArea.totalCases}
              segments={scenario.casesByFocusArea.segments}
            />
          </div>

          {/* Bottom Row: Students Needing Attention + Today's Schedule */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4.5">
            <StudentsNeedingAttention
              students={scenario.studentsNeedingAttention}
              onViewAll={onNavigateToStudentsInNeed}
              onSelectStudent={(student) => setActiveModal({ type: 'student', student })}
            />

            <TodaysSchedule
              schedule={scenario.todaysSchedule}
              onViewCalendar={onNavigateToSchedule}
              onSelectAppointment={(appointment) =>
                setActiveModal({ type: 'appointment', appointment })
              }
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Quick Actions, Wellbeing Insights & Focus (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4.5">
          <QuickActions
            onCreateSupportCase={() =>
              setActiveModal({
                type: 'quickAction',
                title: 'Create Support Case',
                desc: 'Open a structured student assistance case with initial signal observations and assigned intervention tier.',
              })
            }
            onScheduleSession={() =>
              setActiveModal({
                type: 'quickAction',
                title: 'Schedule a Session',
                desc: 'Book a 1-on-1 confidential counselling consultation slot with calendar invites and automatic reminders.',
              })
            }
            onAddToWatchlist={() =>
              setActiveModal({
                type: 'quickAction',
                title: 'Add Student to Watchlist',
                desc: 'Add a student to the priority wellbeing watchlist for closer automated check-in and attendance signal tracking.',
              })
            }
            onLogFollowUp={() =>
              setActiveModal({
                type: 'quickAction',
                title: 'Log a Follow-up',
                desc: 'Record outcomes from post-counselling check-ins and update intervention progress in the student ledger.',
              })
            }
          />

          <WellbeingInsights
            headline={scenario.wellbeingInsights.headline}
            delta={scenario.wellbeingInsights.delta}
            trendData={scenario.wellbeingInsights.trendData}
          />

          <WeeklyFocusChecklist initialItems={scenario.focusItems} />
        </div>
      </div>

      {/* Interactive Modal for Quick Actions and Student/Appointment details */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl p-6 sm:p-7 max-w-md w-full border border-purple-100 shadow-2xl flex flex-col relative text-left">
            <button
              type="button"
              onClick={() => setActiveModal(null)}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-gray-800 flex items-center justify-center transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            {activeModal.type === 'student' && (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm ${activeModal.student.avatarBg} ${activeModal.student.avatarText}`}
                  >
                    {activeModal.student.initials}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#1E2433]">
                      {activeModal.student.name}
                    </h3>
                    <p className="text-xs text-[#717E95]">{activeModal.student.subtitle}</p>
                  </div>
                </div>

                <div className="p-3.5 bg-purple-50/50 rounded-2xl border border-purple-100 text-xs text-[#334155] leading-relaxed mb-4">
                  <p>
                    <strong>Priority Status:</strong> {activeModal.student.priority}
                  </p>
                  <p className="mt-1">
                    <strong>Authorized Case:</strong> #{activeModal.student.caseId}
                  </p>
                  <p className="mt-1 text-gray-500">
                    Accessible under scoped counselor permissions (NFR-SEC-01). Case notes and
                    attestations are cryptographically signed.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveModal(null)
                      onNavigateToSupportCases?.()
                    }}
                    className="flex-1 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition text-center shadow-xs"
                  >
                    Open Support Case
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveModal(null)}
                    className="px-5 py-2.5 rounded-full border border-gray-200 text-gray-700 text-xs font-bold hover:bg-gray-50 transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}

            {activeModal.type === 'appointment' && (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center">
                    <Video className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#1E2433]">
                      {activeModal.appointment.title}
                    </h3>
                    <p className="text-xs text-[#717E95]">
                      Student: {activeModal.appointment.studentName}
                    </p>
                  </div>
                </div>

                <div className="p-3.5 bg-gray-50 rounded-2xl border border-gray-100 text-xs text-[#334155] leading-relaxed mb-4">
                  <p>
                    <strong>Scheduled Time:</strong> Today at {activeModal.appointment.time}
                  </p>
                  <p className="mt-1">
                    <strong>Format:</strong> 1-on-1 Secure Counselling Video Call
                  </p>
                  <p className="mt-1 text-gray-500">
                    A private end-to-end encrypted session link has been dispatched to the student
                    portal.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveModal(null)}
                    className="flex-1 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition text-center shadow-xs"
                  >
                    Ready for Session
                  </button>
                </div>
              </div>
            )}

            {activeModal.type === 'quickAction' && (
              <div>
                <div className="flex items-center gap-2.5 mb-3">
                  <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <h3 className="text-base font-bold text-[#1E2433]">
                    {activeModal.title}
                  </h3>
                </div>

                <p className="text-xs text-[#475569] leading-relaxed mb-5">
                  {activeModal.desc}
                </p>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveModal(null)}
                    className="flex-1 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition text-center shadow-xs"
                  >
                    Proceed with Action
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveModal(null)}
                    className="px-5 py-2.5 rounded-full border border-gray-200 text-gray-700 text-xs font-bold hover:bg-gray-50 transition"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

