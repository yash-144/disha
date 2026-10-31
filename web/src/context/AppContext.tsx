import React, { createContext, useContext, useState, useEffect } from 'react'
import {
  ViewMode,
  DashboardTab,
  Course,
  LiveSession,
  BlogPost,
  ToastMessage,
} from '../types'
import {
  COURSES_DATA,
  LIVE_SESSIONS_DATA,
  BLOG_POSTS,
} from '../mockData'

interface AppContextType {
  currentView: ViewMode
  setCurrentView: (view: ViewMode) => void
  dashboardTab: DashboardTab
  setDashboardTab: (tab: DashboardTab) => void
  courses: Course[]
  enrolledCourseIds: string[]
  searchQuery: string
  setSearchQuery: (query: string) => void
  activeLiveModal: LiveSession | null
  setActiveLiveModal: (session: LiveSession | null) => void
  activeCourseDetail: Course | null
  setActiveCourseDetail: (course: Course | null) => void
  activeBlogPost: BlogPost | null
  setActiveBlogPost: (post: BlogPost | null) => void
  toasts: ToastMessage[]
  addToast: (title: string, message?: string, type?: 'success' | 'info' | 'warning' | 'error') => void
  removeToast: (id: string) => void
  enrollInCourse: (courseId: string) => void
  navigateTo: (view: ViewMode, dashboardTab?: DashboardTab) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentView, setCurrentView] = useState<ViewMode>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const v = params.get('view') as ViewMode
      if (v) return v
      const path = window.location.pathname.toLowerCase()
      if (['/student', '/counsellor', '/admin', '/faculty', '/instructor'].some((p) => path.startsWith(p))) {
        return 'dashboard'
      }
    }
    return 'landing'
  })
  const [dashboardTab, setDashboardTab] = useState<DashboardTab>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const t = params.get('tab') as DashboardTab
      if (t) return t
    }
    return 'cases'
  })
  const [courses] = useState<Course[]>(COURSES_DATA)
  const [enrolledCourseIds, setEnrolledCourseIds] = useState<string[]>(['course-1', 'course-3'])
  const [searchQuery, setSearchQuery] = useState('')
  const [activeLiveModal, setActiveLiveModal] = useState<LiveSession | null>(null)
  const [activeCourseDetail, setActiveCourseDetail] = useState<Course | null>(null)
  const [activeBlogPost, setActiveBlogPost] = useState<BlogPost | null>(null)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  // Load persistence if available
  useEffect(() => {
    try {
      const savedEnrolled = localStorage.getItem('skillsup_enrolled')
      if (savedEnrolled) {
        setEnrolledCourseIds(JSON.parse(savedEnrolled))
      }
    } catch {
      // ignore
    }
  }, [])

  const addToast = (
    title: string,
    message?: string,
    type: 'success' | 'info' | 'warning' | 'error' = 'success'
  ) => {
    const id = Math.random().toString(36).substring(2, 9)
    setToasts((prev) => [...prev, { id, title, message, type }])
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const enrollInCourse = (courseId: string) => {
    if (enrolledCourseIds.includes(courseId)) {
      addToast('Already Enrolled', 'You are already enrolled in this course.', 'info')
      return
    }
    const updated = [...enrolledCourseIds, courseId]
    setEnrolledCourseIds(updated)
    try {
      localStorage.setItem('skillsup_enrolled', JSON.stringify(updated))
    } catch {
      // ignore
    }
    addToast('Enrolled Successfully!', 'Course added to your learning dashboard.', 'success')
  }

  const navigateTo = (view: ViewMode, tab: DashboardTab = 'overview') => {
    setCurrentView(view)
    if (tab) {
      setDashboardTab(tab)
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <AppContext.Provider
      value={{
        currentView,
        setCurrentView,
        dashboardTab,
        setDashboardTab,
        courses,
        enrolledCourseIds,
        searchQuery,
        setSearchQuery,
        activeLiveModal,
        setActiveLiveModal,
        activeCourseDetail,
        setActiveCourseDetail,
        activeBlogPost,
        setActiveBlogPost,
        toasts,
        addToast,
        removeToast,
        enrollInCourse,
        navigateTo,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}
