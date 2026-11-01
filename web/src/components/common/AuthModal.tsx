import React, { useState } from 'react'
import { X, Lock, Mail, User, ArrowRight } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { isGoogleAuthLive, buildGoogleOAuthUrl, GOOGLE_AUTH_CONFIG } from '../../config/auth'

export function AuthModal() {
  const { authModal, closeAuthModal, switchRole, addToast, navigateTo, setCurrentUser } = useApp()
  const [tab, setTab] = useState<'signin' | 'register'>(authModal.mode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<'instructor' | 'student'>('student')
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)

  if (!authModal.isOpen) return null

  const handleGoogleLogin = () => {
    setIsGoogleLoading(true)

    if (isGoogleAuthLive()) {
      addToast(
        'Redirecting to Google...',
        'Connecting with Google Accounts OAuth 2.0 endpoint.',
        'info'
      )
      window.location.href = buildGoogleOAuthUrl('disha_onboarding')
      return
    }

    // Development / Demo Mode with Google OAuth Placeholders
    setTimeout(() => {
      setIsGoogleLoading(false)
      switchRole(role)
      setCurrentUser((prev) => ({
        ...prev,
        name: name.trim(),
        email: email.trim(),
        avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80',
        role: role,
      }))
      addToast(
        'Google Login Successful!',
        'Signed in with Google OAuth. Redirecting to onboarding...',
        'success'
      )
      closeAuthModal()
      navigateTo('login')
    }, 600)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    switchRole(role)
    if (tab === 'register') {
      setCurrentUser((prev) => ({
        ...prev,
        name: name.trim() || prev.name,
        email: email.trim() || prev.email,
        role: role,
      }))
      addToast(
        'Account Registered!',
        `Welcome ${name || 'Learner'}! Redirecting to login...`,
        'success'
      )
      closeAuthModal()
      navigateTo('login')
    } else {
      addToast(
        'Welcome Back!',
        `Logged in as ${role === 'instructor' ? 'Faculty Instructor' : 'Enrolled Student'}.`,
        'success'
      )
      closeAuthModal()
      navigateTo('dashboard', 'overview')
    }
  }

  const handleDemoLogin = (targetRole: 'instructor' | 'student') => {
    switchRole(targetRole)
    addToast('Demo Account Loaded', `Welcome to the ${targetRole} dashboard view!`, 'success')
    closeAuthModal()
    navigateTo('dashboard', 'overview')
  }

  const isLive = isGoogleAuthLive()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-in fade-in font-sans">
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-6 py-4">
          <span className="text-base font-black tracking-widest text-slate-900 uppercase">DISHA</span>
          <button
            onClick={closeAuthModal}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
            aria-label="Close authentication modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 border-b border-slate-100 text-center text-xs font-semibold p-1.5 bg-slate-50/50">
          <button
            onClick={() => setTab('signin')}
            className={`py-2 rounded-xl transition ${tab === 'signin' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
              }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setTab('register')}
            className={`py-2 rounded-xl transition ${tab === 'register' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
              }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Body */}
        <div className="max-h-[85vh] overflow-y-auto p-6">
          {/* Google Sign In Button */}
          <div className="space-y-2">
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading}
              className="flex w-full items-center justify-center gap-3 rounded-full border border-slate-200 bg-white py-2.5 px-4 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 hover:border-slate-300 transition active:scale-[0.99] disabled:opacity-60"
            >
              <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.97 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
              <span>{isGoogleLoading ? 'Connecting...' : tab === 'signin' ? 'Continue with Google' : 'Sign up with Google'}</span>
            </button>

            <div className="flex items-center justify-between px-2 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className={`h-1.5 w-1.5 rounded-full ${isLive ? 'bg-emerald-500 animate-ping' : 'bg-slate-300'}`} />
                {isLive ? 'Google OAuth Live' : 'Google OAuth Dev/Mock Mode'}
              </span>
              <span>Client ID Configured</span>
            </div>
          </div>

          {/* Divider */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-100" />
            </div>
            <div className="relative flex justify-center text-xs uppercase font-medium text-slate-400">
              <span className="bg-white px-2">or email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3.5">
            {tab === 'register' && (
              <div>
                <label className="text-xs font-medium text-slate-700">Full Name</label>
                <div className="mt-1 flex items-center rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2 text-xs focus-within:bg-white focus-within:border-blue-500 transition">
                  <User className="mr-2 h-4 w-4 text-slate-400" />
                  <input
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your full name"
                    className="w-full bg-transparent outline-none"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-medium text-slate-700">Academic / Official Email</label>
              <div className="mt-1 flex items-center rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2 text-xs focus-within:bg-white focus-within:border-blue-500 transition">
                <Mail className="mr-2 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@university.edu"
                  className="w-full bg-transparent outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-700">Password</label>
              <div className="mt-1 flex items-center rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2 text-xs focus-within:bg-white focus-within:border-blue-500 transition">
                <Lock className="mr-2 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-transparent outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-700">Role</label>
              <div className="mt-1 grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setRole('student')}
                  className={`rounded-xl border p-2 font-medium transition ${role === 'student'
                      ? 'border-blue-500 bg-blue-50/60 font-semibold text-blue-700'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                >
                  🎓 Student
                </button>
                <button
                  type="button"
                  onClick={() => setRole('instructor')}
                  className={`rounded-xl border p-2 font-medium transition ${role === 'instructor'
                      ? 'border-blue-500 bg-blue-50/60 font-semibold text-blue-700'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                >
                  👨‍🏫 Faculty
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-slate-900 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              {tab === 'signin' ? 'Sign In & Enter' : 'Create Account & Begin Onboarding'}{' '}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          {/* Quick Demo Switcher */}
          <div className="mt-5 rounded-2xl bg-slate-50 p-3 text-center">
            <span className="text-xs font-medium text-slate-500">Instant Demo 1-Click:</span>
            <div className="mt-2 flex justify-center gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleDemoLogin('instructor')}
                className="rounded-full bg-white border border-slate-200 px-3 py-1 font-medium text-slate-700 hover:bg-slate-100 transition shadow-2xs"
              >
                Faculty Demo
              </button>
              <button
                type="button"
                onClick={() => handleDemoLogin('student')}
                className="rounded-full bg-white border border-slate-200 px-3 py-1 font-medium text-slate-700 hover:bg-slate-100 transition shadow-2xs"
              >
                Student Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
