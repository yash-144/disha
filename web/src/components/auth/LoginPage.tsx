import React, { useState } from 'react'
import { ArrowLeft, Shield, AlertCircle } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { UserRole } from '../../types'
import { isGoogleAuthLive, buildGoogleOAuthUrl } from '../../config/auth'
import { isSupabaseConfigured, signInWithGoogle } from '../../lib/auth/supabase'

const HERO_COLLAB_IMG = 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80'

const ROLES: { id: UserRole; label: string; description: string }[] = [
  { id: 'counsellor', label: 'Counselor', description: 'Early-warning cases & interventions' },
  { id: 'instructor', label: 'Faculty', description: 'Academic signals & student reviews' },
  { id: 'student', label: 'Student', description: 'Academic profile & support requests' },
  { id: 'admin', label: 'Admin', description: 'Multi-campus policy & governance' },
]

export function LoginPage() {
  const { navigateTo } = useApp()
  const [selectedRole, setSelectedRole] = useState<UserRole>('counsellor')
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role)
    setAuthError(null)
  }

  const handleGoogleAuth = async () => {
    setIsGoogleLoading(true)
    setAuthError(null)
    localStorage.setItem('disha_selected_role', selectedRole)

    // 1. Supabase Google OAuth Provider
    if (isSupabaseConfigured()) {
      const { error } = await signInWithGoogle(selectedRole)
      if (error) {
        setIsGoogleLoading(false)
        setAuthError(error.message || 'Supabase authentication failed')
      }
      return
    }

    // 2. Direct Google OAuth 2.0
    if (isGoogleAuthLive()) {
      window.location.href = buildGoogleOAuthUrl('disha_login_redirect')
      return
    }

    // If neither is configured, show configuration prompt
    setIsGoogleLoading(false)
    setAuthError(
      'OAuth credentials not configured. Please set VITE_SUPABASE_ANON_KEY or VITE_GOOGLE_CLIENT_ID in web/.env'
    )
  }

  return (
    <div className="min-h-screen w-full bg-[#f4f6f8] text-slate-900 font-sans flex flex-col justify-between p-4 sm:p-6 md:p-10 selection:bg-slate-900 selection:text-white">
      {/* Top Header / Return Navigation */}
      <div className="w-full max-w-6xl mx-auto flex items-center justify-between pb-4">
        <button
          onClick={() => navigateTo('landing')}
          className="text-xl sm:text-2xl font-black tracking-widest text-slate-950 uppercase outline-none hover:opacity-80 transition cursor-pointer"
        >
          DISHA
        </button>

        <button
          onClick={() => navigateTo('landing')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Home</span>
        </button>
      </div>

      {/* Main Split Card */}
      <div className="w-full max-w-6xl mx-auto my-auto bg-white rounded-3xl md:rounded-[36px] overflow-hidden shadow-2xl shadow-slate-300/40 border border-slate-200/80 grid grid-cols-1 lg:grid-cols-2 min-h-[600px]">
        
        {/* Left Column: Campus Collaboration Photo */}
        <div className="relative hidden lg:block w-full h-full min-h-[600px] bg-slate-900 overflow-hidden">
          <img
            src={HERO_COLLAB_IMG}
            alt="Students and faculty collaborating on campus"
            className="w-full h-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/20" />
          
          <div className="absolute bottom-8 left-8 right-8 text-white">
            <span className="text-[10px] font-semibold tracking-wider uppercase px-3 py-1 rounded-full bg-white/20 backdrop-blur-md">
              CAMPUS EARLY WARNING RADAR
            </span>
            <p className="mt-3 text-xl font-bold leading-snug">
              "No Alert Without Action."
            </p>
            <p className="mt-1 text-xs text-white/80 font-light">
              Calibrated machine learning &amp; multi-campus intervention routing.
            </p>
          </div>
        </div>

        {/* Right Column: Clean Authentication Experience */}
        <div className="flex flex-col justify-center items-center p-8 sm:p-12 md:p-14 lg:p-16 text-center">
          <div className="w-full max-w-md flex flex-col items-center">
            
            {/* Top Minimalist Logo Mark */}
            <div className="h-12 w-12 rounded-2xl bg-slate-950 text-white flex items-center justify-center mb-6 shadow-lg shadow-slate-950/20">
              <Shield className="w-6 h-6 text-indigo-400" />
            </div>

            {/* Title */}
            <h1 className="text-3xl sm:text-[34px] font-black tracking-tight text-slate-950 leading-tight">
              Sign In to DISHA
            </h1>

            {/* Subtitle */}
            <p className="mt-2 text-xs sm:text-sm text-slate-500 font-normal leading-relaxed max-w-sm">
              Institutional Single Sign-On for students, faculty, counselors, and campus administrators.
            </p>

            {/* Role / Workspace Selection */}
            <div className="mt-6 w-full text-left">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 block text-center">
                Select Your Workspace Portal
              </label>

              <div className="grid grid-cols-2 gap-2 w-full p-1.5 bg-slate-100 rounded-2xl">
                {ROLES.map((r) => {
                  const isSelected = selectedRole === r.id
                  return (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => handleRoleSelect(r.id)}
                      className={`p-2.5 text-xs font-semibold rounded-xl transition flex flex-col items-center justify-center cursor-pointer ${
                        isSelected
                          ? 'bg-slate-950 text-white shadow-sm'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                      }`}
                    >
                      <span className="font-bold">{r.label}</span>
                      <span className={`text-[10px] mt-0.5 line-clamp-1 ${isSelected ? 'text-slate-300' : 'text-slate-400'}`}>
                        {r.description}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Error Message Alert */}
            {authError && (
              <div className="mt-4 w-full rounded-2xl bg-rose-50 border border-rose-200/80 p-3.5 flex items-start gap-2.5 text-left text-xs text-rose-800">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{authError}</span>
              </div>
            )}

            {/* Primary Action: Continue with Google Button */}
            <button
              type="button"
              onClick={handleGoogleAuth}
              disabled={isGoogleLoading}
              className="mt-6 w-full flex items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white py-3.5 px-6 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-50 hover:border-slate-300 active:scale-[0.99] transition disabled:opacity-70 cursor-pointer"
            >
              {isGoogleLoading ? (
                <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-slate-900"></div>
              ) : (
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
              )}
              <span>{isGoogleLoading ? 'Connecting to Google...' : `Continue with Google as ${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}`}</span>
            </button>

            {/* Bottom Security Footer */}
            <div className="mt-8 pt-4 border-t border-slate-100 w-full flex items-center justify-center text-[11px] text-slate-400 font-normal gap-1.5 flex-wrap">
              <span>🔒 Enterprise SSO</span>
              <span>•</span>
              <span>DPDP Act 2023 Compliant</span>
              <span>•</span>
              <span>Audit Anchored</span>
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
