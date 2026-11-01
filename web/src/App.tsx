import React from 'react'
import { useApp } from './context/AppContext'
import { LandingView } from './components/landing/LandingView'
import { LoginPage } from './components/auth/LoginPage'
import { OnboardingView } from './components/onboarding/OnboardingView'
import { TeacherDashboard } from './components/teacher-dashboard/TeacherDashboard'
import { StudentDashboard } from './components/student-portal/StudentDashboard'
import { CounsellorDashboard } from './components/counsellor-portal/CounsellorDashboard'
import { AdminDashboard } from './components/admin-portal/AdminDashboard'
import { AuthModal } from './components/common/AuthModal'
import { CourseDetailModal } from './components/landing/CourseDetailModal'
import { LiveStudioModal } from './components/landing/LiveStudioModal'
import { BlogModal } from './components/landing/BlogModal'

export default function App() {
  const { currentView, userRole } = useApp()

  const renderDashboardByRole = () => {
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

  return (
    <div className="relative min-h-screen">
      {/* Route Router: Route user to appropriate view */}
      {currentView === 'dashboard' ? (
        renderDashboardByRole()
      ) : currentView === 'login' ? (
        <LoginPage />
      ) : currentView === 'onboarding' ? (
        <OnboardingView />
      ) : (
        <LandingView />
      )}

      {/* Global Interactive Overlays */}
      <AuthModal />
      <CourseDetailModal />
      <LiveStudioModal />
      <BlogModal />
    </div>
  )
}
