import React from 'react'
import { useApp } from './context/AppContext'
import { useSession } from './lib/auth/SessionProvider'
import { LandingView } from './components/landing/LandingView'
import { TeacherDashboard } from './components/teacher-dashboard/TeacherDashboard'
import { StudentDashboard } from './components/student-portal/StudentDashboard'
import { CounsellorDashboard } from './components/counsellor-portal/CounsellorDashboard'
import { AdminDashboard } from './components/admin-portal/AdminDashboard'
import { Toasts } from './components/common/Toasts'
import { CourseDetailModal } from './components/landing/CourseDetailModal'
import { LiveStudioModal } from './components/landing/LiveStudioModal'
import { BlogModal } from './components/landing/BlogModal'
import {
  NoPortalForRole,
  NotProvisioned,
  ProfileLoadError,
  SessionLoading,
  SignInNotSetUp,
} from './components/common/SessionScreens'

function Portal() {
  const { status, portal } = useSession()

  switch (status) {
    case 'loading':
      return <SessionLoading />
    case 'unauthenticated':
      return <SignInNotSetUp />
    case 'not_provisioned':
      return <NotProvisioned />
    case 'error':
      return <ProfileLoadError />
  }

  // The portal is chosen from the role the server returned by GET /identity/me.
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

export default function App() {
  const { currentView } = useApp()

  return (
    <div className="relative min-h-screen">
      {currentView === 'dashboard' ? <Portal /> : <LandingView />}

      {/* Global Interactive Overlays */}
      <Toasts />
      <CourseDetailModal />
      <LiveStudioModal />
      <BlogModal />
    </div>
  )
}
