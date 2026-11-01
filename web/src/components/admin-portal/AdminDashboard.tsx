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
    title: 'Overview',
    subtitle: '',
  },
  schedule: {
    title: 'Sessions and calls',
    subtitle: '',
  },
  'case-management': {
    title: 'Cases',
    subtitle: '',
  },
  'student-directory': {
    title: 'Students & staff',
    subtitle: '',
  },
  interventions: {
    title: 'Support options',
    subtitle: '',
  },
  analytics: {
    title: 'Reports',
    subtitle: '',
  },
  'data-import': {
    title: 'Upload data',
    subtitle: '',
  },
  'risk-model': {
    title: 'Early warning',
    subtitle: '',
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
    <div className="bg-paper min-h-screen flex font-sans antialiased text-ink">
      {/* Outer Card with rounded corners matching DISHA design system */}
      <div className="w-full flex min-h-screen">
        {/* Left Navigation Sidebar */}
        <AdminSidebar activeTab={activeTab} onSelectTab={handleSelectTab} />

        {/* Vertical divider */}
        

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 flex flex-col p-4 sm:p-6 lg:px-8 lg:py-6 overflow-y-auto">
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
