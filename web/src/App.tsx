import React from 'react'
import { useApp } from './context/AppContext'
import { LandingView } from './components/landing/LandingView'
import { DashboardLayout } from './components/dashboard/DashboardLayout'
import { Toasts } from './components/common/Toasts'
import { AuthModal } from './components/common/AuthModal'
import { CourseDetailModal } from './components/landing/CourseDetailModal'
import { LiveStudioModal } from './components/landing/LiveStudioModal'
import { BlogModal } from './components/landing/BlogModal'

export default function App() {
  const { currentView } = useApp()

  return (
    <div className="relative min-h-screen">
      {/* Route Router */}
      {currentView === 'dashboard' ? <DashboardLayout /> : <LandingView />}

      {/* Global Interactive Overlays */}
      <Toasts />
      <AuthModal />
      <CourseDetailModal />
      <LiveStudioModal />
      <BlogModal />
    </div>
  )
}
