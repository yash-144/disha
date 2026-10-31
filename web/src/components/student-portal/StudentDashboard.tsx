import React, { useState, useEffect } from 'react'
import { useApp } from '../../context/AppContext'
import { StudentSidebar, StudentNavId } from './StudentSidebar'
import { StudentHeader } from './StudentHeader'
import { WellbeingStats } from './WellbeingStats'
import { WellbeingTrend } from './WellbeingTrend'
import { WeeklyFocus } from './WeeklyFocus'
import { SelfCareBanner } from './SelfCareBanner'
import { RecentUpdates } from './RecentUpdates'
import { UpcomingTimeline } from './UpcomingTimeline'
import { StudentProfilePanel } from './StudentProfilePanel'
import { BreathingModal } from './BreathingModal'
import { STUDENT_DEMO_DATA, DemoMode } from './studentDemoData'
import { StudentMyCasesPage } from './StudentMyCasesPage'
import { StudentRequestSupportPage } from './StudentRequestSupportPage'
import { StudentAssessmentPage } from './StudentAssessmentPage'
import { StudentMessagesPage } from './StudentMessagesPage'
import { StudentLeaderboardRewardsPage } from './StudentLeaderboardRewardsPage'

interface StudentDashboardProps {
  initialTab?: StudentNavId
}

export function StudentDashboard({ initialTab }: StudentDashboardProps) {
  const { addToast } = useApp()
  const [activeTab, setActiveTab] = useState<StudentNavId>(() => {
    if (initialTab) return initialTab
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase()
      if (path.includes('cases')) return 'cases'
      if (path.includes('request-support')) return 'request-support'
      if (path.includes('assessment')) return 'assessment'
      if (path.includes('messages')) return 'messages'
      if (path.includes('leaderboard')) return 'leaderboard'
      const params = new URLSearchParams(window.location.search)
      const tab = params.get('tab') as StudentNavId
      if (tab) return tab
    }
    return 'overview'
  })

  const [demoMode, setDemoMode] = useState<DemoMode>('normalStudent')
  const [isBreathingOpen, setIsBreathingOpen] = useState(false)

  const scenario = STUDENT_DEMO_DATA[demoMode]

  const handleSelectTab = (tab: StudentNavId) => {
    setActiveTab(tab)
    if (typeof window !== 'undefined') {
      const newPath = `/student/${tab}`
      if (window.location.pathname !== newPath) {
        window.history.pushState({ role: 'student', tab }, '', newPath)
      }
    }
  }

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      if (path.includes('cases')) setActiveTab('cases')
      else if (path.includes('request-support')) setActiveTab('request-support')
      else if (path.includes('assessment')) setActiveTab('assessment')
      else if (path.includes('messages')) setActiveTab('messages')
      else if (path.includes('leaderboard')) setActiveTab('leaderboard')
      else if (path.includes('overview') || path === '/student') setActiveTab('overview')
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const handleSelectDemoMode = (mode: DemoMode) => {
    setDemoMode(mode)
    const labels: Record<DemoMode, string> = {
      normalStudent: 'Normal Student',
      needsAttention: 'Needs Attention',
      activeSupport: 'Active Support',
    }
    addToast('Demo Mode Changed', `Viewing synthetic scenario: ${labels[mode]}`, 'info')
  }

  const handleTakeCheckIn = () => {
    handleSelectTab('assessment')
  }

  const handleRequestSupport = () => {
    handleSelectTab('request-support')
  }

  const handleStartAssessment = () => {
    handleSelectTab('assessment')
  }

  const getHeaderTitle = () => {
    switch (activeTab) {
      case 'cases':
        return 'My Cases'
      case 'request-support':
        return 'Request Support'
      case 'assessment':
        return 'Wellbeing Assessment'
      case 'messages':
        return 'Messages'
      case 'leaderboard':
        return 'Leaderboard & Rewards'
      case 'overview':
      default:
        return undefined
    }
  }

  const getHeaderSubtitle = () => {
    switch (activeTab) {
      case 'cases':
        return 'Your support cases, interventions, and progress — all in one place.'
      case 'request-support':
        return "Reach out for the right support. You're not alone in this."
      case 'assessment':
        return "Take a moment to understand how you've been feeling lately."
      case 'messages':
        return 'Communicate with your assigned faculty mentor and student counsellors in a secure, confidential environment.'
      case 'leaderboard':
        return 'Earn wellbeing points, sustain healthy streaks, and redeem campus wellness rewards.'
      case 'overview':
      default:
        return "Here's your wellbeing overview for this week."
    }
  }

  return (
    <div className="bg-[#EAEFF8] min-h-screen p-2 sm:p-2.5 md:p-3 flex items-center justify-center font-sans antialiased text-[#1E2433]">
      {/* Outer Card with rounded corners matching DISHA design system */}
      <div className="bg-[#F8F9FD] rounded-[28px] md:rounded-[32px] shadow-sm border border-[#E0E6ED] w-full flex overflow-hidden min-h-[92vh]">
        {/* Left Navigation Sidebar */}
        <StudentSidebar activeTab={activeTab} onSelectTab={handleSelectTab} />

        {/* Vertical divider */}
        <div className="w-[1px] bg-[#E8EEF5] shrink-0" />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col p-4 sm:p-5 md:p-6 overflow-y-auto">
          {/* Header */}
          <StudentHeader
            title={getHeaderTitle()}
            subtitle={getHeaderSubtitle()}
            demoMode={demoMode}
            onSelectDemoMode={handleSelectDemoMode}
          />

          {/* Conditional View by Tab */}
          {activeTab === 'cases' ? (
            <StudentMyCasesPage demoMode={demoMode} />
          ) : activeTab === 'request-support' ? (
            <StudentRequestSupportPage
              demoMode={demoMode}
              onNavigateToCases={() => handleSelectTab('cases')}
            />
          ) : activeTab === 'assessment' ? (
            <StudentAssessmentPage
              demoMode={demoMode}
              onRequestSupport={() => handleSelectTab('request-support')}
              onNavigateToOverview={() => handleSelectTab('overview')}
            />
          ) : activeTab === 'messages' ? (
            <StudentMessagesPage
              demoMode={demoMode}
              onScheduleCall={() => handleSelectTab('request-support')}
            />
          ) : activeTab === 'leaderboard' ? (
            <StudentLeaderboardRewardsPage demoMode={demoMode} />
          ) : (
            /* Student Overview */
            <div className="flex flex-col xl:flex-row gap-5 mt-3">
              {/* Center Content Column */}
              <div className="flex-1 flex flex-col gap-4">
                {/* 1. Statistics Cards */}
                <WellbeingStats
                  wellbeingScore={scenario.wellbeingScore}
                  scoreDelta={scenario.scoreDelta}
                  isScorePositive={scenario.isScorePositive}
                  checkInsCompleted={scenario.checkInsCompleted}
                  checkInsTotal={scenario.checkInsTotal}
                  streakWeeks={scenario.streakWeeks}
                />

                {/* 2. Middle Row: Wellbeing Trend + This Week's Focus */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3.5">
                  <div className="md:col-span-7">
                    <WellbeingTrend trendData={scenario.trendData} />
                  </div>
                  <div className="md:col-span-5">
                    <WeeklyFocus initialItems={scenario.focusItems} />
                  </div>
                </div>

                {/* 3. Self-Care Banner */}
                <SelfCareBanner onStartBreathing={() => setIsBreathingOpen(true)} />

                {/* 4. Bottom Row: Recent Updates + Upcoming Timeline */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <RecentUpdates updates={scenario.recentUpdates} />
                  <UpcomingTimeline events={scenario.upcomingEvents} />
                </div>
              </div>

              {/* Right Profile & Action Panel */}
              <StudentProfilePanel
                scenario={scenario}
                onTakeCheckIn={handleTakeCheckIn}
                onRequestSupport={handleRequestSupport}
                onStartAssessment={handleStartAssessment}
              />
            </div>
          )}
        </main>
      </div>

      {/* Mindful Breathing Modal */}
      <BreathingModal
        isOpen={isBreathingOpen}
        onClose={() => setIsBreathingOpen(false)}
      />
    </div>
  )
}
