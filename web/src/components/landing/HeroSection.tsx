import React, { useState, useMemo } from 'react'
import { Search, ShieldAlert, Cpu, Award } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const DISHA_SUGGESTIONS = [
  {
    title: 'Checkpoint 0: Baseline Admissions & Prior Qualification Risk',
    category: 'Admissions ML',
    icon: Cpu,
  },
  {
    title: 'Checkpoint 1: Mid-Semester Attendance & Grade Drop Signals',
    category: 'Early Warning',
    icon: ShieldAlert,
  },
  {
    title: 'Checkpoint 2: Exam Eligibility & SLA Case Escalation Queue',
    category: 'Interventions',
    icon: ShieldAlert,
  },
  {
    title: 'Base Sepolia: Tamper-Evident Soulbound Student Identity',
    category: 'Verifiable Credentials',
    icon: Award,
  },
]

export function HeroSection() {
  const {
    navigateTo,
    openAuthModal,
    setCurrentUser,
    addToast,
  } = useApp()

  const [inputVal, setInputVal] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  // Real-time suggestions if user types into input
  const suggestions = useMemo(() => {
    if (!inputVal.trim()) return DISHA_SUGGESTIONS.slice(0, 3)
    return DISHA_SUGGESTIONS.filter(
      (s) =>
        s.title.toLowerCase().includes(inputVal.toLowerCase()) ||
        s.category.toLowerCase().includes(inputVal.toLowerCase())
    )
  }, [inputVal])

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId)
    el?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = inputVal.trim()
    if (!trimmed) {
      navigateTo('login')
      return
    }

    if (trimmed.includes('@') && trimmed.includes('.')) {
      setCurrentUser((prev) => ({ ...prev, email: trimmed }))
      navigateTo('login')
    } else {
      setCurrentUser((prev) => ({ ...prev, name: trimmed }))
      navigateTo('login')
    }
  }

  return (
    <section className="relative w-full min-h-screen overflow-hidden flex flex-col justify-between py-6 sm:py-8 px-4 sm:px-8 lg:px-12 xl:px-16 font-sans select-none">
      {/* 1. Cinematic Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 h-full w-full object-cover object-center pointer-events-none"
      >
        <source src="/herosection.mp4" type="video/mp4" />
      </video>

      {/* 2. Soft Vignette & Cinematic Overlays for perfect contrast */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/30 to-black/70 pointer-events-none" />
      <div className="absolute inset-0 bg-radial-[at_center] from-transparent via-black/15 to-black/50 pointer-events-none" />

      {/* 3. Top Floating Glass Navigation Bar */}
      <div className="relative z-20 w-full pt-2">
        <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between">
          {/* Brand Logo on Left: Bold White Capital DISHA */}
          <button
            onClick={() => navigateTo('landing')}
            className="outline-none group flex items-center"
          >
            <span className="text-2xl sm:text-3xl font-black tracking-widest text-white uppercase drop-shadow-[0_2px_12px_rgba(0,0,0,0.7)] group-hover:opacity-90 transition-opacity">
              DISHA
            </span>
          </button>

          {/* Quick Section Links on Desktop */}
          <div className="hidden md:flex items-center gap-7 text-xs font-medium text-white/90">
            <button
              onClick={() => scrollToSection('why-disha')}
              className="hover:text-white transition drop-shadow-sm"
            >
              Why DISHA
            </button>
            <button
              onClick={() => scrollToSection('solutions')}
              className="hover:text-white transition drop-shadow-sm"
            >
              Solutions
            </button>
            <button
              onClick={() => scrollToSection('faqs')}
              className="hover:text-white transition drop-shadow-sm"
            >
              FAQs
            </button>
          </div>

          {/* Right Floating Actions */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigateTo('login')}
              className="hidden sm:inline-block text-xs font-medium text-white/95 hover:text-white px-2 py-1.5 transition drop-shadow-md cursor-pointer"
            >
              Sign In
            </button>
            <button
              onClick={() => navigateTo('login')}
              className="rounded-full bg-white px-6 py-2.5 text-xs font-semibold text-gray-900 shadow-xl transition hover:bg-white/90 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>

      {/* 4. Center Main Hero Content (Clean & Spacious - Problem & Solution Aligned) */}
      <div className="relative z-20 mx-auto max-w-4xl px-4 text-center my-auto flex flex-col items-center py-12">
        {/* Large Elegant Headline matching Problem & Solution */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[76px] font-light tracking-tight text-white drop-shadow-[0_4px_20px_rgba(0,0,0,0.8)] leading-[1.08]">
          Prevent Student Dropout.
          <br />
          <span className="font-semibold text-white">No Alert Without Action.</span>
        </h1>

        {/* Subtitle description changed according to our problem and solution */}
        <p className="mt-6 max-w-2xl text-sm sm:text-base md:text-lg text-white/90 font-light leading-relaxed drop-shadow-[0_2px_10px_rgba(0,0,0,0.7)]">
          Transforming disparate attendance, grade, and engagement signals into reviewable interventions.
          DISHA uses calibrated ML checkpoints to detect academic slippage long before semester exams, routing every alert to an accountable human owner.
        </p>

        {/* 5. Floating Frosted Glass Input Pill */}
        <div className="relative mt-10 w-full max-w-xl">
          <form
            onSubmit={handleSubmit}
            className="group relative flex items-center justify-between rounded-full border border-white/30 bg-white/20 p-2 sm:p-2.5 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.35)] transition-all focus-within:border-white/60 focus-within:bg-white/25"
          >
            <div className="flex flex-1 items-center gap-3 pl-3 sm:pl-4">
              <Search className="h-4 w-4 text-white/70 shrink-0" />
              <input
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onFocus={() => setIsFocused(true)}
                placeholder="Enter campus email or student ID to run risk radar..."
                className="w-full bg-transparent text-xs sm:text-sm font-normal text-white placeholder:text-white/70 outline-none"
              />
            </div>

            <button
              type="submit"
              className="rounded-full bg-white px-6 sm:px-8 py-2.5 sm:py-3 text-xs sm:text-sm font-semibold text-gray-900 shadow-md transition hover:bg-white/90 hover:scale-[1.02] active:scale-[0.98] shrink-0"
            >
              Start Onboarding
            </button>
          </form>

          {/* Suggestions Dropdown if typing */}
          {isFocused && suggestions.length > 0 && (
            <div
              className="absolute left-0 right-0 top-full mt-2 rounded-2xl border border-white/20 bg-slate-900/95 p-2 backdrop-blur-2xl shadow-2xl text-left text-xs z-30 animate-in fade-in"
              onMouseDown={(e) => e.preventDefault()}
            >
              <div className="px-3 py-1.5 text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                DISHA Early-Warning Signals &amp; Checkpoints
              </div>
              {suggestions.map((s, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    navigateTo('login')
                    setIsFocused(false)
                  }}
                  className="flex items-center justify-between rounded-lg p-2.5 hover:bg-white/10 cursor-pointer text-white transition"
                >
                  <span className="font-medium text-slate-200">{s.title}</span>
                  <span className="text-[10px] text-blue-400 font-semibold">{s.category}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom spacer for clean symmetrical layout */}
      <div className="h-4 sm:h-8" />
    </section>
  )
}
