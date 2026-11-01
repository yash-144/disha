import React, { createContext, useContext, useState, useEffect } from 'react'
import {
  ViewMode,
  DashboardTab,
  UserRole,
  UserProfile,
  Course,
  LiveSession,
  ClassItem,
  StudentRecord,
  BlogPost,
  ToastMessage,
} from '../types'
import {
  INSTRUCTOR_USER,
  STUDENT_USER,
  COUNSELLOR_USER,
  ADMIN_USER,
  COURSES_DATA,
  LIVE_SESSIONS_DATA,
  ACTIVE_CLASSES_DATA,
  STUDENTS_DATA,
  BLOG_POSTS,
} from '../mockData'

export function parseLocationState(): {
  view: ViewMode
  role: UserRole
  tab: DashboardTab
} {
  if (typeof window === 'undefined') {
    return { view: 'landing', role: 'instructor', tab: 'overview' }
  }

  const rawPath = window.location.pathname.toLowerCase()
  const path = rawPath.replace(/\/+$/, '') || '/'
  const params = new URLSearchParams(window.location.search)

  const queryView = params.get('view') as ViewMode | null
  const queryRole = params.get('role') as UserRole | null
  const queryTab = params.get('tab') as DashboardTab | null

  // 1. Root / -> landing page default
  if (path === '/') {
    if (queryView) {
      return {
        view: queryView,
        role: queryRole || 'instructor',
        tab: queryTab || 'overview',
      }
    }
    return { view: 'landing', role: 'instructor', tab: 'overview' }
  }

  // 2. Auth / Login / Register (both signin and register map to login)
  if (
    path === '/login' ||
    path === '/auth/login' ||
    path === '/signin' ||
    path === '/auth' ||
    path === '/register' ||
    path === '/signup'
  ) {
    return { view: 'login', role: queryRole || 'counsellor', tab: 'overview' }
  }

  // 3. Onboarding
  if (path === '/onboarding') {
    return { view: 'onboarding', role: queryRole || 'student', tab: 'overview' }
  }

  // 4. Landing subpages
  if (path === '/courses') {
    return { view: 'courses', role: 'instructor', tab: 'overview' }
  }
  if (path === '/live-classes' || path === '/cohorts') {
    return { view: 'live-classes', role: 'instructor', tab: 'overview' }
  }
  if (path === '/blogs' || path === '/blog') {
    return { view: 'blogs', role: 'instructor', tab: 'overview' }
  }
  if (path === '/about') {
    return { view: 'about', role: 'instructor', tab: 'overview' }
  }
  if (path === '/contact') {
    return { view: 'contact', role: 'instructor', tab: 'overview' }
  }

  // 5. Counsellor Portal (/counsellor, /counsellor/:tab)
  if (path.startsWith('/counsellor')) {
    const parts = path.split('/').filter(Boolean)
    const subTab = (parts[1] as DashboardTab) || queryTab || 'overview'
    return { view: 'dashboard', role: 'counsellor', tab: subTab }
  }

  // 6. Faculty / Instructor Portal (/faculty, /faculty/:tab, /instructor, /instructor/:tab)
  if (path.startsWith('/faculty') || path.startsWith('/instructor')) {
    const parts = path.split('/').filter(Boolean)
    const subTab = (parts[1] as DashboardTab) || queryTab || 'overview'
    return { view: 'dashboard', role: 'instructor', tab: subTab }
  }

  // 7. Student Portal (/student, /student/:tab)
  if (path.startsWith('/student')) {
    const parts = path.split('/').filter(Boolean)
    const subTab = (parts[1] as DashboardTab) || queryTab || 'overview'
    return { view: 'dashboard', role: 'student', tab: subTab }
  }

  // 8. Admin Portal (/admin, /admin/:tab)
  if (path.startsWith('/admin')) {
    const parts = path.split('/').filter(Boolean)
    const subTab = (parts[1] as DashboardTab) || queryTab || 'overview'
    return { view: 'dashboard', role: 'admin', tab: subTab }
  }

  // 9. Generic Dashboard (/dashboard, /dashboard/:tab)
  if (path.startsWith('/dashboard')) {
    const parts = path.split('/').filter(Boolean)
    const subTab = (parts[1] as DashboardTab) || queryTab || 'overview'
    return { view: 'dashboard', role: queryRole || 'instructor', tab: subTab }
  }

  // Default fallback -> Landing page
  return { view: 'landing', role: 'instructor', tab: 'overview' }
}

function getProfileForRole(role: UserRole): UserProfile {
  switch (role) {
    case 'student':
      return STUDENT_USER
    case 'counsellor':
      return COUNSELLOR_USER
    case 'admin':
      return ADMIN_USER
    case 'instructor':
    default:
      return INSTRUCTOR_USER
  }
}

interface AppContextType {
  currentView: ViewMode
  setCurrentView: (view: ViewMode) => void
  dashboardTab: DashboardTab
  setDashboardTab: (tab: DashboardTab) => void
  userRole: UserRole
  setUserRole: (role: UserRole) => void
  currentUser: UserProfile
  setCurrentUser: React.Dispatch<React.SetStateAction<UserProfile>>
  courses: Course[]
  activeClasses: ClassItem[]
  students: StudentRecord[]
  enrolledCourseIds: string[]
  searchQuery: string
  setSearchQuery: (query: string) => void
  activeLiveModal: LiveSession | null
  setActiveLiveModal: (session: LiveSession | null) => void
  activeCourseDetail: Course | null
  setActiveCourseDetail: (course: Course | null) => void
  activeBlogPost: BlogPost | null
  setActiveBlogPost: (post: BlogPost | null) => void
  authModal: { isOpen: boolean; mode: 'signin' | 'register' }
  openAuthModal: (mode?: 'signin' | 'register') => void
  closeAuthModal: () => void
  toasts: ToastMessage[]
  addToast: (title: string, message?: string, type?: 'success' | 'info' | 'warning' | 'error') => void
  removeToast: (id: string) => void
  enrollInCourse: (courseId: string) => void
  toggleStudentAttendance: (studentId: string) => void
  addNewCourse: (course: Partial<Course>) => void
  addNewClass: (cls: Partial<ClassItem>) => void
  switchRole: (role: UserRole) => void
  navigateTo: (view: ViewMode, dashboardTab?: DashboardTab) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const initial = parseLocationState()
  const [currentView, setCurrentView] = useState<ViewMode>(initial.view)
  const [dashboardTab, setDashboardTab] = useState<DashboardTab>(initial.tab)
  const [userRole, setUserRole] = useState<UserRole>(initial.role)
  const [currentUser, setCurrentUser] = useState<UserProfile>(() => getProfileForRole(initial.role))

  const [courses, setCourses] = useState<Course[]>(COURSES_DATA)
  const [activeClasses, setActiveClasses] = useState<ClassItem[]>(ACTIVE_CLASSES_DATA)
  const [students, setStudents] = useState<StudentRecord[]>(STUDENTS_DATA)
  const [enrolledCourseIds, setEnrolledCourseIds] = useState<string[]>(['course-1', 'course-3'])
  const [searchQuery, setSearchQuery] = useState('')
  const [activeLiveModal, setActiveLiveModal] = useState<LiveSession | null>(null)
  const [activeCourseDetail, setActiveCourseDetail] = useState<Course | null>(null)
  const [activeBlogPost, setActiveBlogPost] = useState<BlogPost | null>(null)
  const [authModal, setAuthModal] = useState<{ isOpen: boolean; mode: 'signin' | 'register' }>({
    isOpen: false,
    mode: 'signin',
  })
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

  // Synchronize browser history and back/forward buttons (popstate)
  useEffect(() => {
    const handlePopState = () => {
      const state = parseLocationState()
      setCurrentView(state.view)
      setUserRole(state.role)
      setDashboardTab(state.tab)
      setCurrentUser(getProfileForRole(state.role))
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const addToast = (
    _title: string,
    _message?: string,
    _type: 'success' | 'info' | 'warning' | 'error' = 'success'
  ) => {
    // Notifications disabled per user request
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

  const toggleStudentAttendance = (studentId: string) => {
    setStudents((prev) =>
      prev.map((student) => {
        if (student.id !== studentId) return student
        const nextStatus =
          student.status === 'Present'
            ? 'Late'
            : student.status === 'Late'
            ? 'Absent'
            : 'Present'
        return { ...student, status: nextStatus }
      })
    )
  }

  const addNewCourse = (courseData: Partial<Course>) => {
    const newId = `course-${Date.now()}`
    const fullCourse: Course = {
      id: newId,
      title: courseData.title || 'Untitled Course',
      category: courseData.category || 'web',
      categoryLabel: courseData.categoryLabel || 'Web Development',
      level: courseData.level || 'Beginner',
      duration: courseData.duration || '4 Weeks',
      lecturesCount: courseData.lecturesCount || 12,
      desc: courseData.desc || 'No description provided.',
      price: courseData.price || 'Free',
      originalPrice: courseData.originalPrice || '₹999',
      rating: 5.0,
      reviewsCount: '0',
      instructorName: currentUser.name,
      instructorTitle: currentUser.title,
      instructorAvatar: currentUser.avatar,
      iconName: 'Code',
      accentBg: 'bg-blue-500',
      modules: courseData.modules || [
        {
          title: 'Module 1: Getting Started',
          duration: '1 hr',
          lessons: ['Introduction', 'Core Concepts'],
        },
      ],
      prerequisites: courseData.prerequisites || ['Basic Computer Knowledge'],
    }
    setCourses((prev) => [fullCourse, ...prev])
    addToast('Course Published!', `"${fullCourse.title}" is now available.`, 'success')
  }

  const addNewClass = (clsData: Partial<ClassItem>) => {
    const newId = `class-${Date.now()}`
    const fullClass: ClassItem = {
      id: newId,
      name: clsData.name || 'Untitled Class',
      code: clsData.code || 'CLS-101',
      instructor: currentUser.name,
      accessCode: clsData.accessCode || Math.random().toString(36).substring(2, 8).toUpperCase(),
      term: clsData.term || 'Fall 2025',
      activeStudents: 0,
      createdAt: 'Just now',
      subject: clsData.subject || 'Computer Science',
      color: clsData.color || 'bg-brand',
    }
    setActiveClasses((prev) => [fullClass, ...prev])
    addToast('Class Created!', `Class "${fullClass.name}" code: ${fullClass.accessCode}`, 'success')
  }

  const openAuthModal = (mode: 'signin' | 'register' = 'signin') => {
    setAuthModal({ isOpen: false, mode })
    navigateTo('login')
  }

  const closeAuthModal = () => {
    setAuthModal((prev) => ({ ...prev, isOpen: false }))
  }

  const switchRole = (role: UserRole) => {
    setUserRole(role)
    setCurrentUser(getProfileForRole(role))

    if (typeof window !== 'undefined' && currentView === 'dashboard') {
      const rolePrefix = role === 'instructor' ? 'faculty' : role
      const targetPath = `/${rolePrefix}/${dashboardTab || 'overview'}`
      if (window.location.pathname !== targetPath) {
        window.history.pushState({ view: 'dashboard', role, tab: dashboardTab || 'overview' }, '', targetPath)
      }
    }
  }

  const navigateTo = (view: ViewMode, tab: DashboardTab = 'overview') => {
    setCurrentView(view)
    if (tab) {
      setDashboardTab(tab)
    }

    if (typeof window !== 'undefined') {
      let targetPath = '/'
      if (view === 'landing') {
        targetPath = '/'
      } else if (view === 'login') {
        targetPath = '/login'
      } else if (view === 'onboarding') {
        targetPath = '/onboarding'
      } else if (view === 'courses') {
        targetPath = '/courses'
      } else if (view === 'live-classes') {
        targetPath = '/live-classes'
      } else if (view === 'blogs') {
        targetPath = '/blogs'
      } else if (view === 'about') {
        targetPath = '/about'
      } else if (view === 'contact') {
        targetPath = '/contact'
      } else if (view === 'dashboard') {
        const rolePrefix = userRole === 'instructor' ? 'faculty' : userRole
        const activeTab = tab || dashboardTab || 'overview'
        targetPath = `/${rolePrefix}/${activeTab}`
      }

      if (window.location.pathname !== targetPath) {
        window.history.pushState({ view, tab, role: userRole }, '', targetPath)
      }
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
        userRole,
        setUserRole,
        currentUser,
        setCurrentUser,
        courses,
        activeClasses,
        students,
        enrolledCourseIds,
        searchQuery,
        setSearchQuery,
        activeLiveModal,
        setActiveLiveModal,
        activeCourseDetail,
        setActiveCourseDetail,
        activeBlogPost,
        setActiveBlogPost,
        authModal,
        openAuthModal,
        closeAuthModal,
        toasts,
        addToast,
        removeToast,
        enrollInCourse,
        toggleStudentAttendance,
        addNewCourse,
        addNewClass,
        switchRole,
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
