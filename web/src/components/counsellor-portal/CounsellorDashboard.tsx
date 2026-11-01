import React, { useState, useEffect } from 'react'
import { CounsellorSidebar, CounsellorNavId, COUNSELLOR_NAV_ITEMS } from './CounsellorSidebar'
import { CounsellorHeader } from './CounsellorHeader'
import { CounsellorOverview } from './CounsellorOverview'
import { CounsellorStudentsInNeed } from './CounsellorStudentsInNeed'
import { CounsellorSupportCases } from './CounsellorSupportCases'
import { ScheduleSessionsView } from '../common/ScheduleSessionsView'
import { AdminAnalyticsPage } from '../admin-portal/AdminAnalyticsPage'

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
    title: 'Overview',
    subtitle: '',
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
    subtitle: '',
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
    subtitle: '',
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
    subtitle: '',
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
    subtitle: '',
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
    <div className="bg-paper min-h-screen flex font-sans antialiased text-ink">
      {/* Outer Card with rounded corners matching DISHA design system */}
      <div className="w-full flex min-h-screen">
        {/* Left Navigation Sidebar */}
        <CounsellorSidebar activeTab={activeTab} onSelectTab={handleSelectTab} />

        {/* Vertical divider */}
        

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 flex flex-col p-4 sm:p-6 lg:px-8 lg:py-6 overflow-y-auto">
          {/* Header */}
          <CounsellorHeader
            pageTitle={meta.title}
            subtitle={meta.subtitle}
            showPageTitle
          />

          {/* Conditional View by Tab: Overview vs Other Module Placeholders */}
          {activeTab === 'overview' ? (
            <CounsellorOverview />
          ) : (
            <div className="flex flex-col gap-4">
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
