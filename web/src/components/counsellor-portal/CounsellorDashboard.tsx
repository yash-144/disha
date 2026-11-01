import React, { useState, useEffect } from 'react'
import { CounsellorSidebar, CounsellorNavId, COUNSELLOR_NAV_ITEMS } from './CounsellorSidebar'
import { CounsellorHeader } from './CounsellorHeader'
import { CounsellorOverview } from './CounsellorOverview'
import { CounsellorStudentsInNeed } from './CounsellorStudentsInNeed'
import { CounsellorSupportCases } from './CounsellorSupportCases'
import { ScheduleSessionsView } from '../common/ScheduleSessionsView'
import { AdminAnalyticsPage } from '../admin-portal/AdminAnalyticsPage'
import { ArrowLeft } from 'lucide-react'

const TAB_METADATA: Record<
  CounsellorNavId,
  {
    title: string
    subtitle: string
    description: string
    capabilities: string[]
  }
> = {
  overview: {
    title: 'Counsellor Overview',
    subtitle: 'Student emotional triage and confidential consultation cockpit',
    description:
      'The Counsellor Overview provides student wellbeing advisors with high-level signal queues, active intervention trajectories, and upcoming check-ins.',
    capabilities: [
      'Confidential Student Referral Triage',
      'Urgent Risk & Stress Signal Queue',
      'Daily Session & Consultation Agenda',
      'Case Status & Resolution Funnel',
    ],
  },
  schedule: {
    title: 'Schedule & Calls',
    subtitle: 'Manage one-on-one sessions, office hours and support consultations',
    description:
      'Coordinate private student counseling slots, faculty syncs, and emergency support sessions.',
    capabilities: [
      'Direct Confidential Booking Slots',
      'One-on-One Secure Call Links',
      'Past Consultation Session Notes',
      'Session Rescheduling & Completion Tracking',
    ],
  },
  'students-in-need': {
    title: 'Students in Need',
    subtitle: 'Early warning signals and priority wellbeing assistance queue',
    description:
      'Identify students experiencing academic distress, attendance drop-offs, or negative wellbeing sentiment trends.',
    capabilities: [
      'Early-Warning Signal Monitoring',
      'Severity & Urgency Classification',
      'Student Risk Factor Disaggregation',
      'Direct Escalation & Outreach',
    ],
  },
  'support-cases': {
    title: 'Support Cases',
    subtitle: 'Active counseling trajectories and personalized support plans',
    description:
      'Manage longitudinal counseling cases, action milestones, and inter-departmental collaboration records.',
    capabilities: [
      'Multi-Session Case Histories',
      'Intervention Milestones & Goals',
      'Confidential Faculty Observations',
      'Outcome & Discharge Benchmarks',
    ],
  },
  analytics: {
    title: 'Counsellor Analytics',
    subtitle: 'Cohort wellbeing statistics, referral volumes and resolution trends',
    description:
      'Evaluate aggregate mental wellbeing indicators, common student stressors, and efficacy of supportive interventions.',
    capabilities: [
      'Anonymized Sentiment Trends',
      'Stress Factor Breakdown by Term',
      'Intervention Resolution Velocity',
      'Referral Source Distribution',
    ],
  },
}

interface CounsellorDashboardProps {
  initialTab?: CounsellorNavId
}

export function CounsellorDashboard({ initialTab }: CounsellorDashboardProps) {
  const [activeTab, setActiveTab] = useState<CounsellorNavId>(() => {
    if (initialTab) return initialTab
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase()
      for (const item of COUNSELLOR_NAV_ITEMS) {
        if (path === item.route || path === `/counsellor/${item.id}`) {
          return item.id
        }
      }
    }
    return 'overview'
  })

  // Synchronize browser URL route
  const handleSelectTab = (tab: CounsellorNavId) => {
    setActiveTab(tab)
    if (typeof window !== 'undefined') {
      const newPath = `/counsellor/${tab}`
      if (window.location.pathname !== newPath) {
        window.history.pushState({ role: 'counsellor', tab }, '', newPath)
      }
    }
  }

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      for (const item of COUNSELLOR_NAV_ITEMS) {
        if (path === item.route || path === `/counsellor/${item.id}`) {
          setActiveTab(item.id)
          break
        }
      }
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const currentItem =
    COUNSELLOR_NAV_ITEMS.find((item) => item.id === activeTab) || COUNSELLOR_NAV_ITEMS[0]
  const meta = TAB_METADATA[activeTab] || TAB_METADATA.overview

  return (
    <div className="bg-[#EAEFF8] min-h-screen p-2 sm:p-2.5 md:p-3 flex items-center justify-center font-sans antialiased text-[#1E2433]">
      {/* Outer Card with rounded corners matching DISHA design system */}
      <div className="bg-[#F8F9FD] rounded-[28px] md:rounded-[32px] shadow-sm border border-[#E0E6ED] w-full flex overflow-hidden min-h-[92vh]">
        {/* Left Navigation Sidebar */}
        <CounsellorSidebar activeTab={activeTab} onSelectTab={handleSelectTab} />

        {/* Vertical divider */}
        <div className="w-[1px] bg-[#E8EEF5] shrink-0" />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col p-4 sm:p-5 md:p-6 overflow-y-auto">
          {/* Header */}
          <CounsellorHeader
            pageTitle={meta.title}
            subtitle={meta.subtitle}
            showPageTitle={activeTab !== 'overview'}
          />

          {/* Conditional View by Tab: Overview vs Other Module Placeholders */}
          {activeTab === 'overview' ? (
            <CounsellorOverview />
          ) : (
            <div className="flex flex-col gap-4">
              <button
                type="button"
                onClick={() => handleSelectTab('overview')}
                className="self-start inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-black transition"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Counsellor Overview</span>
              </button>

              {activeTab === 'students-in-need' ? (
                <CounsellorStudentsInNeed />
              ) : activeTab === 'support-cases' ? (
                <CounsellorSupportCases />
              ) : activeTab === 'schedule' ? (
                <ScheduleSessionsView title="Counsellor Schedule & Consultations" />
              ) : (
                <AdminAnalyticsPage />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
