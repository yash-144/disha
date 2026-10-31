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
  const [currentView, setCurrentView] = useState<ViewMode>('landing')
  const [dashboardTab, setDashboardTab] = useState<DashboardTab>('overview')
  const [userRole, setUserRole] = useState<UserRole>('instructor')
  const [currentUser, setCurrentUser] = useState<UserProfile>(INSTRUCTOR_USER)
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
    setTimeout(() => {
      removeToast(id)
    }, 4500)
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const enrollInCourse = (courseId: string) => {
    if (enrolledCourseIds.includes(courseId)) {
      addToast('Already Enrolled', 'You have already enrolled in this course!', 'info')
      return
    }
    const updated = [...enrolledCourseIds, courseId]
    setEnrolledCourseIds(updated)
    try {
      localStorage.setItem('skillsup_enrolled', JSON.stringify(updated))
    } catch {}
    const c = courses.find((item) => item.id === courseId)
    addToast('🎉 Successfully Enrolled!', `Welcome to "${c?.title || 'the course'}".`, 'success')
  }

  const toggleStudentAttendance = (studentId: string) => {
    setStudents((prev) =>
      prev.map((s) => {
        if (s.id !== studentId) return s
        const nextStatus = s.status === 'Present' ? 'Late' : s.status === 'Late' ? 'Absent' : 'Present'
        addToast(`Attendance Updated`, `${s.name} is now marked ${nextStatus}.`, 'info')
        return { ...s, status: nextStatus }
      })
    )
  }

  const addNewCourse = (course: Partial<Course>) => {
    const newId = `course-${courses.length + 1}`
    const fullCourse: Course = {
      id: newId,
      title: course.title || 'Untitled Course',
      category: course.category || 'web',
      categoryLabel: course.categoryLabel || 'Computer Science & IT',
      level: course.level || 'Beginner',
      duration: course.duration || '20 Hours',
      lecturesCount: course.lecturesCount || 24,
      desc: course.desc || 'Comprehensive curriculum with practical exercises.',
      price: course.price || '₹1,599',
      originalPrice: course.originalPrice || '₹3,999',
      rating: 5.0,
      reviewsCount: '1',
      badge: 'New',
      badgeColor: 'bg-[#0f9d58]',
      instructorName: currentUser.name,
      instructorTitle: currentUser.title,
      instructorAvatar: currentUser.avatar,
      iconName: 'Code2',
      accentBg: 'bg-[#1d5fd1]',
      modules: course.modules || [
        {
          title: 'Module 1: Introduction & Environment Setup',
          duration: '3 hrs',
          lessons: ['Introduction to key concepts', 'Setting up tools & code editor'],
        },
      ],
      prerequisites: course.prerequisites || ['None'],
    }
    setCourses((prev) => [fullCourse, ...prev])
    addToast('Course Created!', `"${fullCourse.title}" is now published in the catalog.`, 'success')
  }

  const addNewClass = (cls: Partial<ClassItem>) => {
    const newClass: ClassItem = {
      id: `class-${Date.now()}`,
      name: cls.name || 'New Live Cohort Class',
      code: cls.code || `CS${Math.floor(100 + Math.random() * 900)}`,
      instructor: currentUser.name,
      accessCode: Math.random().toString(36).substring(2, 12),
      term: cls.term || 'Jul 1, 2025 - Aug 15, 2025',
      activeStudents: 1,
      createdAt: 'Just now',
      subject: cls.subject || 'Engineering',
      color: 'bg-indigo-600',
    }
    setActiveClasses((prev) => [newClass, ...prev])
    addToast('Class Room Created!', `Access Code: ${newClass.accessCode}`, 'success')
  }

  const switchRole = (role: UserRole) => {
    setUserRole(role)
    if (role === 'instructor') {
      setCurrentUser(INSTRUCTOR_USER)
      addToast('Switched to Instructor Mode', 'You now have teaching and management permissions.', 'info')
    } else {
      setCurrentUser(STUDENT_USER)
      addToast('Switched to Student Mode', 'You are now viewing as an enrolled student.', 'info')
    }
  }

  const openAuthModal = (mode: 'signin' | 'register' = 'signin') => {
    setAuthModal({ isOpen: true, mode })
  }

  const closeAuthModal = () => {
    setAuthModal((prev) => ({ ...prev, isOpen: false }))
  }

  const navigateTo = (view: ViewMode, tab: DashboardTab = 'overview') => {
    setCurrentView(view)
    if (view === 'dashboard') {
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
