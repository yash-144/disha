import React, { useState } from 'react'
import {
  LayoutDashboard,
  GraduationCap,
  Shield,
  Menu,
  X,
  ArrowRight,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function Header() {
  const {
    currentView,
    navigateTo,
    openAuthModal,
    userRole,
    switchRole,
  } = useApp()

  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const handleNavClick = (view: any) => {
    navigateTo(view)
    setMobileNavOpen(false)
  }

  const scrollToSection = (sectionId: string) => {
    setMobileNavOpen(false)
    if (currentView !== 'landing') {
      navigateTo('landing')
      setTimeout(() => {
        const el = document.getElementById(sectionId)
        el?.scrollIntoView({ behavior: 'smooth' })
      }, 150)
    } else {
      const el = document.getElementById(sectionId)
      el?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <header className="sticky top-0 z-40 w-full font-sans">
      {/* Top Notification Ribbon */}
      <div className="border-b border-slate-800 bg-slate-950 px-4 py-2 text-center text-xs text-slate-300 font-medium">
        <div className="mx-auto flex max-w-6xl items-center justify-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-emerald-400 font-semibold">EARLY-WARNING ACTIVE:</span>
          <span className="hidden sm:inline">Calibrated ML checkpoints monitoring 4,424+ student signals across campus cohorts.</span>
          <button
            onClick={() => navigateTo('login')}
            className="ml-1 text-white underline decoration-emerald-400 decoration-1 underline-offset-4 hover:text-emerald-300 transition"
          >
            Run Risk Radar →
          </button>
        </div>
      </div>

      {/* Main Navigation Bar (Clean & Minimalist) */}
      <nav className="border-b border-slate-100 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3.5 sm:px-8 lg:px-12">
          {/* Brand Logo: Bold Capital DISHA */}
          <button
            onClick={() => handleNavClick('landing')}
            className="outline-none group text-left flex items-center"
          >
            <span className="text-2xl font-black tracking-widest text-slate-900 uppercase">
              DISHA
            </span>
          </button>

          {/* Desktop Navigation Links */}
          <ul className="hidden items-center gap-7 text-xs font-medium text-slate-600 md:flex">
            <li>
              <button
                onClick={() => handleNavClick('landing')}
                className={`transition-colors ${
                  currentView === 'landing' ? 'text-blue-600 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                Home
              </button>
            </li>
            <li>
              <button
                onClick={() => scrollToSection('why-disha')}
                className="transition-colors hover:text-slate-900"
              >
                Why DISHA
              </button>
            </li>
            <li>
              <button
                onClick={() => scrollToSection('solutions')}
                className="transition-colors hover:text-slate-900"
              >
                Solutions
              </button>
            </li>
            <li>
              <button
                onClick={() => scrollToSection('faqs')}
                className="transition-colors hover:text-slate-900"
              >
                FAQs
              </button>
            </li>
            <li>
              <button
                onClick={() => handleNavClick('about')}
                className={`transition-colors ${
                  currentView === 'about' ? 'text-blue-600 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                About
              </button>
            </li>
          </ul>

          {/* Right Action Hub */}
          <div className="flex items-center gap-3">
            {/* Segmented Role Switcher */}
            <div className="hidden lg:flex items-center rounded-full bg-slate-100 p-1 text-[11px] font-medium">
              <button
                onClick={() => switchRole('instructor')}
                className={`flex items-center gap-1 rounded-full px-3 py-1 transition ${
                  userRole === 'instructor' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <Shield className="h-3 w-3" />
                <span>Faculty</span>
              </button>
              <button
                onClick={() => switchRole('student')}
                className={`flex items-center gap-1 rounded-full px-3 py-1 transition ${
                  userRole === 'student' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <GraduationCap className="h-3 w-3" />
                <span>Student</span>
              </button>
            </div>

            {/* Launch LMS Cockpit */}
            <button
              onClick={() => navigateTo('dashboard', 'overview')}
              className="hidden sm:flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
            >
              <LayoutDashboard className="h-3.5 w-3.5 text-blue-600" />
              <span>Cockpit</span>
            </button>

            {/* Auth Buttons */}
            <button
              onClick={() => navigateTo('login')}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 px-2 transition cursor-pointer"
            >
              Sign In
            </button>

            <button
              onClick={() => navigateTo('login')}
              className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition cursor-pointer"
            >
              Get Started
            </button>

            {/* Mobile Hamburger Toggle */}
            <button
              onClick={() => setMobileNavOpen(!mobileNavOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100 md:hidden transition"
              aria-label="Toggle navigation menu"
            >
              {mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileNavOpen && (
          <div className="border-t border-slate-100 bg-white px-4 py-4 md:hidden shadow-lg animate-in slide-in-from-top duration-200 text-xs font-medium space-y-2">
            {[
              { label: 'Home', action: () => handleNavClick('landing') },
              { label: 'Why DISHA', action: () => scrollToSection('why-disha') },
              { label: 'Solutions & Interventions', action: () => scrollToSection('solutions') },
              { label: 'FAQs & Architecture', action: () => scrollToSection('faqs') },
              { label: 'About Platform', action: () => handleNavClick('about') },
              { label: 'LMS Cockpit', action: () => handleNavClick('dashboard') },
            ].map((item, idx) => (
              <button
                key={idx}
                onClick={item.action}
                className="flex w-full items-center justify-between p-2.5 rounded-xl hover:bg-slate-50 text-slate-700 text-left"
              >
                <span>{item.label}</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
            ))}
          </div>
        )}
      </nav>
    </header>
  )
}
