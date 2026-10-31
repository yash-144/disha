import React, { useState } from 'react'
import {
  LayoutDashboard,
  GraduationCap,
  Shield,
  Menu,
  X,
  Radio,
  Sparkles,
  ArrowRight,
  BookOpen,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function Header() {
  const {
    currentView,
    navigateTo,
    openAuthModal,
    userRole,
    switchRole,
    currentUser,
    setActiveLiveModal,
  } = useApp()

  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const handleNavClick = (view: any) => {
    navigateTo(view)
    setMobileNavOpen(false)
  }

  return (
    <header className="sticky top-0 z-40 w-full font-mono">
      {/* Top Live Class Notification Ribbon */}
      <div className="border-b-2 border-ink bg-[#0d1b3e] px-4 py-1.5 text-center text-[11px] font-bold text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-[#0f9d58] animate-ping" />
          <span className="text-emerald-400">LIVE NOW:</span>
          <span className="hidden sm:inline">CS402 React 19 Canvas Architecture Cohort is streaming.</span>
          <button
            onClick={() => navigateTo('live-classes')}
            className="ml-1 underline decoration-[#0f9d58] decoration-2 underline-offset-2 hover:text-emerald-300 transition"
          >
            Watch Free Stream →
          </button>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <nav className="border-b-2 border-ink bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          {/* Brand Logo */}
          <button
            onClick={() => handleNavClick('landing')}
            className="flex items-center gap-1 text-2xl font-bold tracking-tight text-left outline-none group"
          >
            <span className="text-[#0f9d58] group-hover:scale-105 transition-transform">Skills</span>
            <span className="text-brand">U</span>
            <span className="text-[#0f9d58]">P</span>
            <span className="ml-2 hidden rounded border border-ink bg-brand/10 px-1.5 py-0.5 text-[10px] font-bold text-brand shadow-[1px_1px_0_#0d1b3e] sm:inline-block">
              v2.0
            </span>
          </button>

          {/* Desktop Navigation Links */}
          <ul className="hidden items-center gap-6 text-xs font-bold md:flex">
            <li>
              <button
                onClick={() => handleNavClick('landing')}
                className={`transition-all pb-1 ${
                  currentView === 'landing'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                Home
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('courses')}
                className={`transition-all pb-1 ${
                  currentView === 'courses'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                Courses Catalog
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('live-classes')}
                className={`flex items-center gap-1.5 transition-all pb-1 ${
                  currentView === 'live-classes'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                Live Classes
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('blogs')}
                className={`transition-all pb-1 ${
                  currentView === 'blogs'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                Blogs
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('about')}
                className={`transition-all pb-1 ${
                  currentView === 'about'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                About Us
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('contact')}
                className={`transition-all pb-1 ${
                  currentView === 'contact'
                    ? 'text-brand border-b-2 border-brand'
                    : 'text-muted hover:text-ink'
                }`}
              >
                Contact
              </button>
            </li>
          </ul>

          {/* Action CTAs */}
          <div className="flex items-center gap-2 sm:gap-3 text-xs">
            {/* Quick Role Toggle */}
            <div className="hidden lg:flex items-center border-2 border-ink bg-white p-0.5 shadow-[2px_2px_0_#0d1b3e]">
              <button
                onClick={() => switchRole('instructor')}
                title="Switch to Instructor Role"
                className={`flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold transition ${
                  userRole === 'instructor' ? 'bg-brand text-white' : 'text-gray-600 hover:text-black'
                }`}
              >
                <Shield className="h-3 w-3" />
                <span>Instructor</span>
              </button>
              <button
                onClick={() => switchRole('student')}
                title="Switch to Student Role"
                className={`flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold transition ${
                  userRole === 'student' ? 'bg-[#0f9d58] text-white' : 'text-gray-600 hover:text-black'
                }`}
              >
                <GraduationCap className="h-3 w-3" />
                <span>Student</span>
              </button>
            </div>

            {/* LMS Dashboard Cockpit Button */}
            <button
              onClick={() => navigateTo('dashboard', 'overview')}
              className="flex items-center gap-1.5 border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-ink shadow-[2.5px_2.5px_0_#0d1b3e] transition hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[4px_4px_0_#0d1b3e] hover:bg-blue-50"
            >
              <LayoutDashboard className="h-3.5 w-3.5 text-brand" />
              <span>LMS Dashboard</span>
            </button>

            {/* Auth Buttons */}
            <button
              onClick={() => openAuthModal('signin')}
              className="hidden sm:block font-bold text-ink hover:text-brand px-2"
            >
              Sign In
            </button>

            <button
              onClick={() => openAuthModal('register')}
              className="border-2 border-ink bg-[#0f9d58] px-3.5 py-1.5 font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
            >
              Register
            </button>

            {/* Mobile Hamburger Menu Toggle */}
            <button
              onClick={() => setMobileNavOpen(!mobileNavOpen)}
              className="flex h-8 w-8 items-center justify-center border-2 border-ink bg-white text-ink md:hidden shadow-[1.5px_1.5px_0_#0d1b3e]"
              aria-label="Toggle navigation menu"
            >
              {mobileNavOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileNavOpen && (
          <div className="border-t-2 border-ink bg-white px-4 py-4 md:hidden shadow-lg animate-in slide-in-from-top duration-200">
            <ul className="space-y-2 text-xs font-bold">
              <li>
                <button
                  onClick={() => handleNavClick('landing')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span>Home</span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNavClick('courses')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span>Courses Catalog (60+)</span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNavClick('live-classes')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                    Live Class Sessions
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNavClick('blogs')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span>Engineering Blogs</span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNavClick('about')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span>About SkillsUp</span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNavClick('contact')}
                  className="flex w-full items-center justify-between border-2 border-ink bg-gray-50 p-2.5 text-left"
                >
                  <span>Contact &amp; Support</span>
                  <ArrowRight className="h-3.5 w-3.5 text-brand" />
                </button>
              </li>
            </ul>

            <div className="mt-4 pt-3 border-t-2 border-ink/10 flex items-center justify-between">
              <span className="text-[11px] text-gray-500">Active Role:</span>
              <button
                onClick={() => switchRole(userRole === 'instructor' ? 'student' : 'instructor')}
                className="border border-ink bg-brand px-2 py-1 text-[10px] font-bold text-white shadow-xs capitalize"
              >
                Switch Role ({userRole})
              </button>
            </div>
          </div>
        )}
      </nav>
    </header>
  )
}
