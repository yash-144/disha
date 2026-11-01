import React, { useState, useEffect } from 'react'
import { Users, Activity, Flag } from 'lucide-react'
import { TeacherSidebar } from './TeacherSidebar'
import { TeacherHeader } from './TeacherHeader'
import { StatCard } from './StatCard'
import { QueryState } from '../common/QueryState'
import { useFacultyDashboard } from '../../lib/api/endpoints/faculty.hooks'
import { MyCases } from './MyCases'
import { UpcomingSessionsCard } from './UpcomingSessionsCard'
import { ScheduleCallsPage } from './ScheduleCallsPage'
import { MyCasesPage } from './MyCasesPage'
import { StudentDirectoryPage } from './StudentDirectoryPage'
import { InterventionsProtocolsPage } from './InterventionsProtocolsPage'
import { TeacherAssessmentsPage } from './TeacherAssessmentsPage'
import { useApp } from '../../context/AppContext'

interface TeacherDashboardProps {
  initialTab?: string
}

function Stats() {
  const dash = useFacultyDashboard()
  return (
    <QueryState query={dash}>
      {(d) => (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          <StatCard title="Students in your classes" value={d.metrics.total_students_monitored} icon={Users} variant="yellow" />
          <StatCard title="Your classes" value={d.metrics.active_sections} icon={Activity} variant="blue" />
          <StatCard title="Alerts waiting for you" value={d.metrics.unreviewed_signals} icon={Flag} variant="purple" />
        </div>
      )}
    </QueryState>
  )
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
      if (path.includes('assessment')) return 'assessment'
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
      tab === 'interventions'
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
      else if (path.includes('assessment')) setActiveTab('assessment')
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
      case 'overview':
      default:
        return (
          <>
            {/* Center: Main Overview Content */}
            <main className="flex-1 flex flex-col gap-4 min-w-0 p-4 sm:p-6 lg:px-8 lg:py-6 font-sans">
              {/* Header */}
              <TeacherHeader />

              {/* Statistics Cards Row */}
              <section aria-label="Key statistics">
                <Stats />
              </section>

              {/* Middle Row: Upcoming Consultations and My Cases */}
              <section aria-label="Sessions and cases">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <UpcomingSessionsCard onViewSchedule={() => handleTabChange('schedule')} />
                  <MyCases onViewAll={() => handleTabChange('cases')} />
                </div>
              </section>

            </main>

          </>
        )
    }
  }

  return (
    <div className="min-h-screen w-full bg-paper flex font-sans antialiased text-ink">
      {/* Main Dashboard Canvas */}
      <div className="w-full flex-1 flex flex-col lg:flex-row min-h-screen">
        
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
