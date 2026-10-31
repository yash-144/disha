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
  const [currentView, setCurrentView] = useState<ViewMode>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const v = params.get('view') as ViewMode
      if (v) return v
    }
    return 'dashboard'
  })
  const [dashboardTab, setDashboardTab] = useState<DashboardTab>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const t = params.get('tab') as DashboardTab
      if (t) return t
    }
    return 'cases'
  })
  const [userRole, setUserRole] = useState<UserRole>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const r = params.get('role') as UserRole
      if (r && ['instructor', 'student', 'counsellor', 'admin'].includes(r)) return r
      const path = window.location.pathname.toLowerCase()
      if (path.startsWith('/counsellor')) return 'counsellor'
      if (path.startsWith('/admin')) return 'admin'
      if (path.startsWith('/student')) return 'student'
      if (path.startsWith('/faculty') || path.startsWith('/instructor')) return 'instructor'
    }
    return 'instructor'
  })
  const [currentUser, setCurrentUser] = useState<UserProfile>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const r = params.get('role') as UserRole
      const path = window.location.pathname.toLowerCase()
      const role = r || (path.startsWith('/counsellor') ? 'counsellor' : path.startsWith('/admin') ? 'admin' : path.startsWith('/student') ? 'student' : 'instructor')
      if (role === 'counsellor') return COUNSELLOR_USER
      if (role === 'admin') return ADMIN_USER
      if (role === 'student') return STUDENT_USER
    }
    return INSTRUCTOR_USER
  })
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
    setAuthModal({ isOpen: true, mode })
  }

  const closeAuthModal = () => {
    setAuthModal((prev) => ({ ...prev, isOpen: false }))
  }

  const switchRole = (role: UserRole) => {
    setUserRole(role)
    const rolePrefix = role === 'instructor' ? 'faculty' : role
    if (typeof window !== 'undefined') {
      window.history.pushState({ role }, '', `/${rolePrefix}/overview`)
    }
    if (role === 'instructor') {
      setCurrentUser(INSTRUCTOR_USER)
    } else if (role === 'student') {
      setCurrentUser(STUDENT_USER)
    } else if (role === 'counsellor') {
      setCurrentUser(COUNSELLOR_USER)
    } else if (role === 'admin') {
      setCurrentUser(ADMIN_USER)
    }
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
