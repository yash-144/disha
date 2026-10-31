import React, { useState, useEffect } from 'react'
import { StudentSidebar, StudentNavId } from './StudentSidebar'
import { StudentHeader } from './StudentHeader'
import { NotAvailable } from '../common/NotAvailable'
import { StudentOverview } from './StudentOverview'
import { StudentRewardsPage } from './StudentRewardsPage'
import { StudentMyCasesPage } from './StudentMyCasesPage'
import { StudentAssessmentPage } from './StudentAssessmentPage'

interface StudentDashboardProps {
  initialTab?: StudentNavId
}

export function StudentDashboard({ initialTab }: StudentDashboardProps) {
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
          />

          {activeTab === 'cases' ? (
            <StudentMyCasesPage />
          ) : activeTab === 'request-support' ? (
            <NotAvailable title="Request Support" message="Requesting support needs a faculty directory endpoint, which the server does not expose yet." />
          ) : activeTab === 'assessment' ? (
            <StudentAssessmentPage />
          ) : activeTab === 'messages' ? (
            <NotAvailable title="Messages" />
          ) : activeTab === 'leaderboard' ? (
            <StudentRewardsPage />
          ) : (
            <StudentOverview onCheckIn={() => handleSelectTab('assessment')} />
          )}
        </main>
      </div>

    </div>
  )
}
