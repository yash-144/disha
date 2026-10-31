import React, { useState } from 'react'
import { X, Lock, Mail, User, ShieldCheck, ArrowRight, Sparkles } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function AuthModal() {
  const { authModal, closeAuthModal, switchRole, addToast, navigateTo } = useApp()
  const [tab, setTab] = useState<'signin' | 'register'>(authModal.mode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<'instructor' | 'student'>('instructor')

  if (!authModal.isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    switchRole(role)
    addToast(
      tab === 'signin' ? 'Welcome Back!' : 'Registration Complete!',
      `Logged in as ${role === 'instructor' ? 'Lead Instructor' : 'Enrolled Student'}.`,
      'success'
    )
    closeAuthModal()
    navigateTo('dashboard', 'overview')
  }

  const handleDemoLogin = (targetRole: 'instructor' | 'student') => {
    switchRole(targetRole)
    addToast('Demo Account Loaded', `Welcome to the ${targetRole} dashboard view!`, 'success')
    closeAuthModal()
    navigateTo('dashboard', 'overview')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl border-4 border-ink bg-white shadow-[8px_8px_0_#0d1b3e]">
        {/* Header decoration */}
        <div className="flex items-center justify-between border-b-2 border-ink bg-[#f5f7fc] px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-white font-bold text-xs">
              UP
            </span>
            <span className="text-sm font-bold tracking-tight">SkillsUp Authentication</span>
          </div>
          <button
            onClick={closeAuthModal}
            className="rounded p-1 text-gray-500 hover:bg-gray-200 hover:text-black"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 border-b-2 border-ink text-center text-sm font-bold">
          <button
            onClick={() => setTab('signin')}
            className={`py-3 transition-colors ${
              tab === 'signin' ? 'bg-[#0f9d58] text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setTab('register')}
            className={`py-3 transition-colors ${
              tab === 'register' ? 'bg-[#0f9d58] text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6">
          {/* Quick Demo Switcher */}
          <div className="mb-5 rounded-lg border-2 border-dashed border-brand/40 bg-blue-50/60 p-3">
            <p className="flex items-center gap-1.5 text-xs font-bold text-brand">
              <Sparkles className="h-4 w-4" /> Instant Demo Access (1-Click):
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleDemoLogin('instructor')}
                className="rounded border border-ink bg-white px-2 py-1.5 font-semibold text-ink shadow-[2px_2px_0_#0d1b3e] hover:bg-gray-50"
              >
                👨‍🏫 As Instructor
              </button>
              <button
                type="button"
                onClick={() => handleDemoLogin('student')}
                className="rounded border border-ink bg-white px-2 py-1.5 font-semibold text-ink shadow-[2px_2px_0_#0d1b3e] hover:bg-gray-50"
              >
                🎓 As Student
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {tab === 'register' && (
              <div>
                <label className="text-xs font-bold text-gray-700">Your Full Name</label>
                <div className="mt-1 flex items-center rounded-md border-2 border-ink bg-[#f8fafc] px-3 py-2 text-sm focus-within:bg-white">
                  <User className="mr-2 h-4 w-4 text-gray-400" />
                  <input
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Joseph Jackson"
                    className="w-full bg-transparent outline-none text-xs"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-bold text-gray-700">Email Address</label>
              <div className="mt-1 flex items-center rounded-md border-2 border-ink bg-[#f8fafc] px-3 py-2 text-sm focus-within:bg-white">
                <Mail className="mr-2 h-4 w-4 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full bg-transparent outline-none text-xs"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-700">Password</label>
              <div className="mt-1 flex items-center rounded-md border-2 border-ink bg-[#f8fafc] px-3 py-2 text-sm focus-within:bg-white">
                <Lock className="mr-2 h-4 w-4 text-gray-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-transparent outline-none text-xs"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-700">Select Role</label>
              <div className="mt-1 grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setRole('instructor')}
                  className={`rounded border-2 p-2 font-medium transition ${
                    role === 'instructor'
                      ? 'border-brand bg-brand/10 font-bold text-brand'
                      : 'border-gray-200 text-gray-600'
                  }`}
                >
                  Instructor / Host
                </button>
                <button
                  type="button"
                  onClick={() => setRole('student')}
                  className={`rounded border-2 p-2 font-medium transition ${
                    role === 'student'
                      ? 'border-[#0f9d58] bg-[#0f9d58]/10 font-bold text-[#0f9d58]'
                      : 'border-gray-200 text-gray-600'
                  }`}
                >
                  Student / Learner
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="mt-2 flex w-full items-center justify-center gap-2 border-2 border-ink bg-[#0f9d58] py-3 text-sm font-bold text-white shadow-[4px_4px_0_#0d1b3e] transition hover:bg-[#0b7a43]"
            >
              {tab === 'signin' ? 'Sign In to SkillsUp' : 'Create Free Account'}{' '}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <p className="mt-4 text-center text-[10px] text-gray-500">
            By signing in you agree to our Terms of Service & Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  )
}
