import React, { useState, useEffect } from 'react'
import { Users, Activity, Flag } from 'lucide-react'
import { TeacherSidebar } from './TeacherSidebar'
import { TeacherHeader } from './TeacherHeader'
import { StatCard } from './StatCard'
import { RecentMessages } from './RecentMessages'
import { MyCases } from './MyCases'
import { ActiveInterventions } from './ActiveInterventions'
import { TeacherProfilePanel } from './TeacherProfilePanel'
import { ScheduleCallsPage } from './ScheduleCallsPage'
import { MyCasesPage } from './MyCasesPage'
import { StudentDirectoryPage } from './StudentDirectoryPage'
import { InterventionsProtocolsPage } from './InterventionsProtocolsPage'
import { DocumentIntegrityPage } from './DocumentIntegrityPage'
import { TeacherAssessmentsPage } from './TeacherAssessmentsPage'
import { useApp } from '../../context/AppContext'

interface TeacherDashboardProps {
  initialTab?: string
}

export function TeacherDashboard({ initialTab }: TeacherDashboardProps) {
  const { dashboardTab, setDashboardTab } = useApp()
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (initialTab) return initialTab
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase()
      if (path.includes('schedule')) return 'schedule'
      if (path.includes('cases')) return 'cases'
      if (path.includes('directory')) return 'directory'
      if (path.includes('interventions')) return 'interventions'
      if (path.includes('integrity')) return 'integrity'
    }
    return dashboardTab === 'schedule' ? 'schedule' : 'overview'
  })

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab)
    }
  }, [initialTab])

  // Synchronize browser URL route
  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
    if (
      tab === 'overview' ||
      tab === 'schedule' ||
      tab === 'cases' ||
      tab === 'directory' ||
      tab === 'interventions' ||
      tab === 'integrity'
    ) {
      setDashboardTab(tab as any)
    }
    if (typeof window !== 'undefined') {
      const newPath = `/faculty/${tab}`
      if (window.location.pathname !== newPath) {
        window.history.pushState({ role: 'instructor', tab }, '', newPath)
      }
    }
  }

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      if (path.includes('schedule')) setActiveTab('schedule')
      else if (path.includes('cases')) setActiveTab('cases')
      else if (path.includes('directory')) setActiveTab('directory')
      else if (path.includes('interventions')) setActiveTab('interventions')
      else if (path.includes('integrity')) setActiveTab('integrity')
      else if (path.includes('overview') || path === '/faculty' || path === '/instructor') {
        setActiveTab('overview')
      }
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const renderTabContent = () => {
    switch (activeTab) {
      case 'schedule':
        return <ScheduleCallsPage />
      case 'cases':
        return <MyCasesPage />
      case 'directory':
        return <StudentDirectoryPage />
      case 'interventions':
        return <InterventionsProtocolsPage />
      case 'assessment':
        return <TeacherAssessmentsPage />
      case 'integrity':
        return <DocumentIntegrityPage />
      case 'overview':
      default:
        return (
          <>
            {/* Center: Main Overview Content */}
            <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
              {/* Header */}
              <TeacherHeader />

              {/* Statistics Cards Row */}
              <section aria-label="Key statistics">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                  <StatCard
                    title="Students in Scope"
                    value={128}
                    icon={Users}
                    variant="yellow"
                  />
                  <StatCard
                    title="Active Support Cases"
                    value={24}
                    icon={Activity}
                    variant="blue"
                  />
                  <StatCard
                    title="Signals Pending Review"
                    value={6}
                    icon={Flag}
                    variant="purple"
                  />
                </div>
              </section>

              {/* Middle Row: Recent Messages and My Cases */}
              <section aria-label="Messages and cases">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <RecentMessages />
                  <MyCases onViewAll={() => handleTabChange('cases')} />
                </div>
              </section>

              {/* Bottom Row: Active Interventions Table */}
              <section aria-label="Active interventions table">
                <ActiveInterventions onViewAll={() => handleTabChange('interventions')} />
              </section>
            </main>

            {/* Right: Teacher Profile & Agenda Panel */}
            <TeacherProfilePanel />
          </>
        )
    }
  }

  return (
    <div className="min-h-screen w-full bg-[#EAEFF8] p-2 sm:p-2.5 md:p-3 flex font-sans antialiased text-[#1E2433]">
      {/* Main Dashboard Canvas */}
      <div className="w-full flex-1 bg-[#F8F9FD] rounded-[24px] sm:rounded-[28px] md:rounded-[32px] shadow-[0_6px_30px_rgba(20,28,45,0.06)] border border-white/80 p-3 sm:p-4 lg:p-5 flex flex-col lg:flex-row gap-3.5 lg:gap-4.5 overflow-hidden min-h-[calc(100vh-1.5rem)]">
        
        {/* Left: Navigation Sidebar */}
        <TeacherSidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />

        {/* Dynamic Tab Page Rendering */}
        {renderTabContent()}
      </div>
    </div>
  )
}
