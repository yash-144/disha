import React from 'react'
import { useApp } from './context/AppContext'
import { useSession } from './lib/auth/SessionProvider'
import { LandingView } from './components/landing/LandingView'
import { LoginPage } from './components/auth/LoginPage'
import { OnboardingView } from './components/onboarding/OnboardingView'
import { TeacherDashboard } from './components/teacher-dashboard/TeacherDashboard'
import { StudentDashboard } from './components/student-portal/StudentDashboard'
import { CounsellorDashboard } from './components/counsellor-portal/CounsellorDashboard'
import { AdminDashboard } from './components/admin-portal/AdminDashboard'
import { AuthModal } from './components/common/AuthModal'
import { Toasts } from './components/common/Toasts'
import { CourseDetailModal } from './components/landing/CourseDetailModal'
import { LiveStudioModal } from './components/landing/LiveStudioModal'
import { BlogModal } from './components/landing/BlogModal'
import {
  NoPortalForRole,
  SessionLoading,
} from './components/common/SessionScreens'

function Portal() {
  const { status, portal } = useSession()
  const { userRole } = useApp()

  if (status === 'loading') {
    return <SessionLoading />
  }

  // If authenticated with real server session, honor the verified role:
  if (status === 'authenticated' && portal) {
    switch (portal) {
      case 'student':
        return <StudentDashboard />
      case 'counsellor':
        return <CounsellorDashboard />
      case 'admin':
        return <AdminDashboard />
      case 'instructor':
        return <TeacherDashboard />
      default:
        return <NoPortalForRole />
    }
  }

  // If in demo/unauthenticated mode, fall back to the selected userRole:
  switch (userRole) {
    case 'student':
      return <StudentDashboard />
    case 'counsellor':
      return <CounsellorDashboard />
    case 'admin':
      return <AdminDashboard />
    case 'instructor':
    default:
      return <TeacherDashboard />
  }
}

export default function App() {
  const { currentView } = useApp()

  return (
    <div className="relative min-h-screen">
      {/* Route Router: Route user to appropriate view */}
      {currentView === 'dashboard' ? (
        <Portal />
      ) : currentView === 'login' ? (
        <LoginPage />
      ) : currentView === 'onboarding' ? (
        <OnboardingView />
      ) : (
        <LandingView />
      )}

      {/* Global Interactive Overlays */}
      <AuthModal />
      <Toasts />
      <CourseDetailModal />
      <LiveStudioModal />
      <BlogModal />
    </div>
  )
}
