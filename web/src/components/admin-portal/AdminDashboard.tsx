import React, { useState, useEffect } from 'react'
import { AdminSidebar, AdminNavId, ADMIN_NAV_ITEMS } from './AdminSidebar'
import { AdminHeader } from './AdminHeader'
import { AdminOverviewPage } from './AdminOverviewPage'
import { AdminSchedulePage } from './AdminSchedulePage'
import { AdminCaseManagementPage } from './AdminCaseManagementPage'
import { AdminStudentDirectoryPage } from './AdminStudentDirectoryPage'
import { AdminInterventionsPage } from './AdminInterventionsPage'
import { AdminAnalyticsPage } from './AdminAnalyticsPage'
import { AdminDataImportPage } from './AdminDataImportPage'
import { AdminRiskModelPage } from './AdminRiskModelPage'

const TAB_METADATA: Record<
  AdminNavId,
  {
    title: string
    subtitle: string
  }
> = {
  overview: {
    title: 'Administrator Overview',
    subtitle: 'Institutional governance, student welfare health and campus-wide benchmarks',
  },
  schedule: {
    title: 'Schedule & Calls',
    subtitle: 'Institutional review calendars, committee syncs and faculty briefings',
  },
  'case-management': {
    title: 'Case Management',
    subtitle: 'Centralized institution-wide student case governance and escalations',
  },
  'student-directory': {
    title: 'Student Directory',
    subtitle: 'Master institutional roster across all faculties, batches and departments',
  },
  interventions: {
    title: 'Interventions & Protocols',
    subtitle: 'Institutional standard operating procedures, triggers and escalation rules',
  },
  analytics: {
    title: 'Institution Analytics',
    subtitle: 'Macro retention modeling, demographic breakdowns and longitudinal KPIs',
  },
  'data-import': {
    title: 'Data Import',
    subtitle: 'Upload canonical student data, validate it and review import history',
  },
  'risk-model': {
    title: 'Risk Model',
    subtitle: 'Loaded model, scoring runs, active policy and data drift',
  },
}

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<AdminNavId>(() => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase()
      for (const item of ADMIN_NAV_ITEMS) {
        if (path === item.route || path === `/admin/${item.id}`) {
          return item.id
        }
      }
    }
    return 'overview'
  })

  // Synchronize browser URL route
  const handleSelectTab = (tab: AdminNavId) => {
    setActiveTab(tab)
    if (typeof window !== 'undefined') {
      const newPath = `/admin/${tab}`
      if (window.location.pathname !== newPath) {
        window.history.pushState({ role: 'admin', tab }, '', newPath)
      }
    }
  }

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      for (const item of ADMIN_NAV_ITEMS) {
        if (path === item.route || path === `/admin/${item.id}`) {
          setActiveTab(item.id)
          break
        }
      }
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const meta = TAB_METADATA[activeTab] || TAB_METADATA.overview

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <AdminOverviewPage onNavigateTab={(tab) => handleSelectTab(tab as AdminNavId)} />
      case 'schedule':
        return <AdminSchedulePage />
      case 'case-management':
        return <AdminCaseManagementPage />
      case 'student-directory':
        return <AdminStudentDirectoryPage />
      case 'interventions':
        return <AdminInterventionsPage />
      case 'analytics':
        return <AdminAnalyticsPage />
      case 'data-import':
        return <AdminDataImportPage />
      case 'risk-model':
        return <AdminRiskModelPage />
      default:
        return <AdminOverviewPage onNavigateTab={(tab) => handleSelectTab(tab as AdminNavId)} />
    }
  }

  return (
    <div className="bg-[#EAEFF8] min-h-screen p-2 sm:p-2.5 md:p-3 flex items-center justify-center font-sans antialiased text-[#1E2433]">
      {/* Outer Card with rounded corners matching DISHA design system */}
      <div className="bg-[#F8F9FD] rounded-[28px] md:rounded-[32px] shadow-sm border border-[#E0E6ED] w-full flex overflow-hidden min-h-[92vh]">
        {/* Left Navigation Sidebar */}
        <AdminSidebar activeTab={activeTab} onSelectTab={handleSelectTab} />

        {/* Vertical divider */}
        <div className="w-[1px] bg-[#E8EEF5] shrink-0" />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col p-4 sm:p-5 md:p-6 overflow-y-auto">
          {/* Header */}
          <AdminHeader pageTitle={meta.title} subtitle={meta.subtitle} />

          {/* Render Current Active Page */}
          <div className="mt-2">
            {renderActivePage()}
          </div>
        </main>
      </div>
    </div>
  )
}
