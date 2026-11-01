import React, { useState } from 'react'
import { ArrowRight, ArrowLeft, Check, Sparkles, Shield, GraduationCap, HeartHandshake, Building2 } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { UserRole } from '../../types'
import { isGoogleAuthLive, buildGoogleOAuthUrl } from '../../config/auth'

const HERO_COLLAB_IMG = 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80'

export function LoginPage() {
  const { switchRole, setCurrentUser, navigateTo } = useApp()
  const [selectedRole, setSelectedRole] = useState<UserRole>('counsellor')
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [showStatusBanner, setShowStatusBanner] = useState(true)

  const ROLE_PERSONAS: Record<UserRole, { name: string; email: string; label: string; id: string }> = {
    instructor: {
      name: 'Prof. Vikramaditya Sen',
      email: 'v.sen@iitb.ac.in',
      label: 'Faculty',
      id: 'FAC-7741',
    },
    counsellor: {
      name: 'Dr. Priya Nair',
      email: 'priya.nair@iitb.ac.in',
      label: 'Counselor',
      id: 'CNS-2098',
    },
    student: {
      name: 'Aarav Sharma',
      email: 'aarav.sharma@iitb.ac.in',
      label: 'Student',
      id: '2024CS-0842',
    },
    admin: {
      name: 'Dean H. Mehta',
      email: 'dean.mehta@iitb.ac.in',
      label: 'Admin',
      id: 'ADM-1001',
    },
  }

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role)
    const persona = ROLE_PERSONAS[role]
    switchRole(role)
    setCurrentUser((prev) => ({
      ...prev,
      name: persona.name,
      email: persona.email,
      role: role,
    }))
  }

  const handleGoogleAuth = () => {
    setIsGoogleLoading(true)

    if (isGoogleAuthLive()) {
      window.location.href = buildGoogleOAuthUrl('disha_login_redirect')
      return
    }

    // Interactive Demo / Simulated Google Institutional Single Sign-On
    setTimeout(() => {
      setIsGoogleLoading(false)
      const googleUser = {
        name: 'Aarav Sharma',
        email: 'aarav.sharma@gmail.com',
        avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80',
      }

      setCurrentUser((prev) => ({
        ...prev,
        ...googleUser,
        role: selectedRole,
      }))

      navigateTo('dashboard', 'overview')
    }, 700)
  }

  const handleOfflineDemo = () => {
    const persona = ROLE_PERSONAS[selectedRole]
    switchRole(selectedRole)
    setCurrentUser((prev) => ({
      ...prev,
      name: persona.name,
      email: persona.email,
      role: selectedRole,
    }))

    navigateTo('dashboard', 'overview')
  }

  const handleStartOnboarding = () => {
    const persona = ROLE_PERSONAS[selectedRole]
    switchRole(selectedRole)
    setCurrentUser((prev) => ({
      ...prev,
      name: persona.name,
      email: persona.email,
      role: selectedRole,
    }))

    navigateTo('onboarding')
  }

  return (
    <div className="min-h-screen w-full bg-[#f4f6f8] text-slate-900 font-sans flex flex-col justify-between p-4 sm:p-6 md:p-10 selection:bg-slate-900 selection:text-white">
      {/* Top Header / Return Navigation */}
      <div className="w-full max-w-6xl mx-auto flex items-center justify-between pb-4">
        <button
          onClick={() => navigateTo('landing')}
          className="text-xl sm:text-2xl font-black tracking-widest text-slate-950 uppercase outline-none hover:opacity-80 transition"
        >
          DISHA
        </button>

        <button
          onClick={() => navigateTo('landing')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Landing Page</span>
        </button>
      </div>

      {/* Main Split Card (Exact match to reference layout) */}
      <div className="w-full max-w-6xl mx-auto my-auto bg-white rounded-3xl md:rounded-[36px] overflow-hidden shadow-2xl shadow-slate-300/40 border border-slate-200/80 grid grid-cols-1 lg:grid-cols-2 min-h-[620px]">
        
        {/* Left Column: Campus Collaboration Photo */}
        <div className="relative hidden lg:block w-full h-full min-h-[620px] bg-slate-900 overflow-hidden">
          <img
            src={HERO_COLLAB_IMG}
            alt="Students and faculty collaborating on laptops"
            className="w-full h-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
          
          {/* Subtle Bottom Image Label */}
          <div className="absolute bottom-8 left-8 right-8 text-white">
            <span className="text-[10px] font-semibold tracking-wider uppercase px-3 py-1 rounded-full bg-white/20 backdrop-blur-md">
              CAMPUS EARLY WARNING RADAR
            </span>
            <p className="mt-3 text-lg font-bold leading-snug">
              "No Alert Without Action."
            </p>
            <p className="mt-1 text-xs text-white/80 font-light">
              Calibrated machine learning &amp; multi-campus case routing.
            </p>
          </div>
        </div>

        {/* Right Column: Clean Authentication Experience (Exact match to reference) */}
        <div className="flex flex-col justify-center items-center p-8 sm:p-12 md:p-14 lg:p-16 text-center">
          <div className="w-full max-w-md flex flex-col items-center">
            
            {/* Top Minimalist Logo Mark */}
            <div className="h-10 w-10 rounded-2xl bg-slate-950 text-white flex items-center justify-center mb-6 shadow-md">
              <span className="font-black text-sm tracking-tighter">D</span>
            </div>

            {/* Title */}
            <h1 className="text-3xl sm:text-[34px] font-black tracking-tight text-slate-950 leading-tight">
              Sign In to DISHA
            </h1>

            {/* Subtitle */}
            <p className="mt-2 text-xs sm:text-sm text-slate-500 font-normal leading-relaxed max-w-sm">
              Institutional Single Sign-On powered by Google Workspace &amp; YugabyteDB
            </p>

            {/* Status / Alert Banner (matching reference green pill banner) */}
            {showStatusBanner && (
              <div className="mt-6 w-full rounded-2xl bg-emerald-50/80 border border-emerald-200/80 px-4 py-2.5 flex items-center justify-between text-xs text-emerald-800">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                    ✓
                  </div>
                  <span className="font-medium text-left">
                    You are connected to DISHA early-warning network.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowStatusBanner(false)}
                  className="text-emerald-500 hover:text-emerald-800 text-sm ml-2 font-bold cursor-pointer"
                >
                  ×
                </button>
              </div>
            )}

            {/* Primary Action: Continue with Google Button */}
            <button
              type="button"
              onClick={handleGoogleAuth}
              disabled={isGoogleLoading}
              className="mt-6 w-full flex items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white py-3.5 px-6 text-sm font-semibold text-slate-800 shadow-xs hover:bg-slate-50 hover:border-slate-300 active:scale-[0.99] transition disabled:opacity-70 cursor-pointer"
            >
              {/* Official Google G Logo */}
              <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>{isGoogleLoading ? 'Connecting...' : 'Continue with Google'}</span>
            </button>

            {/* Divider: "or preview" */}
            <div className="relative my-6 w-full text-center">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <span className="relative bg-white px-3 text-xs text-slate-400 font-normal">
                or preview
              </span>
            </div>

            {/* Dual Action Buttons (Offline Demo & Start Onboarding) */}
            <div className="grid grid-cols-2 gap-3 w-full">
              <button
                type="button"
                onClick={handleOfflineDemo}
                className="w-full rounded-2xl bg-slate-100 hover:bg-slate-200/80 py-3 px-4 text-xs sm:text-sm font-semibold text-slate-800 transition flex items-center justify-center gap-1.5 cursor-pointer active:scale-[0.99]"
              >
                <span>Offline Demo</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>

              <button
                type="button"
                onClick={handleStartOnboarding}
                className="w-full rounded-2xl bg-slate-950 hover:bg-slate-800 py-3 px-4 text-xs sm:text-sm font-semibold text-white shadow-sm transition flex items-center justify-center gap-1.5 cursor-pointer active:scale-[0.99]"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Start Onboarding</span>
              </button>
            </div>

            {/* Instant Role Workspaces */}
            <div className="mt-8 w-full">
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2.5">
                INSTANT ROLE WORKSPACES
              </div>

              {/* 4 Role Selector Buttons (matching reference style) */}
              <div className="grid grid-cols-4 gap-2 w-full p-1 bg-slate-100 rounded-2xl">
                {(['instructor', 'counsellor', 'student', 'admin'] as UserRole[]).map((role) => {
                  const isSelected = selectedRole === role
                  const label = ROLE_PERSONAS[role].label
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => handleRoleSelect(role)}
                      className={`py-2 px-1 text-xs font-semibold rounded-xl transition cursor-pointer ${
                        isSelected
                          ? 'bg-slate-950 text-white shadow-sm'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                      }`}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Bottom Security Footer */}
            <div className="mt-8 pt-4 border-t border-slate-100 w-full flex items-center justify-center text-[10px] sm:text-[11px] text-slate-400 font-normal gap-1 flex-wrap">
              <span>🔒 Enterprise Grade</span>
              <span>•</span>
              <span>YugabyteDB Meko Memory</span>
              <span>•</span>
              <span>DPDP Act 2023 Compliant</span>
              <span>•</span>
              <span>Base Sepolia Verified</span>
            </div>

          </div>
        </div>

      </div>

      {/* Minimal Footer */}
      <footer className="w-full max-w-6xl mx-auto pt-4 text-center text-xs text-slate-400 font-normal">
        DISHA Platform • Calibrated Early-Warning &amp; Accountable Intervention System
      </footer>
    </div>
  )
}
