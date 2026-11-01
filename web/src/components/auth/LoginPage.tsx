import React, { useState } from 'react'
import { AlertCircle, ArrowLeft, Loader2, ShieldCheck } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { SignalArt } from '../common/SignalArt'
import { Wordmark } from '../common/AppSidebar'
import { LanguageSwitcher } from '../common/HeaderControls'
import { useT } from '../../i18n'
import { isSupabaseConfigured, signInWithGoogle } from '../../lib/auth/supabase'

const GOOGLE_ICON = (
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
)

export function LoginPage() {
  const { navigateTo } = useApp()
  const t = useT()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(() => {
    const p = new URLSearchParams(window.location.search)
    return p.get('error_description') || p.get('error')
  })

  const handleGoogle = async () => {
    setBusy(true)
    setError(null)
    if (!isSupabaseConfigured()) {
      setBusy(false)
      setError('Google sign-in is not set up on this server yet.')
      return
    }
    try {
      const { error: err } = await signInWithGoogle()
      if (err) {
        setBusy(false)
        setError(err.message || 'Sign-in failed. Please try again.')
      }
    } catch {
      setBusy(false)
      setError('Could not reach Google. Check your connection and try again.')
    }
  }

  return (
    <div className="min-h-screen w-full bg-paper font-sans text-ink lg:grid lg:grid-cols-2">
      {/* Brand panel */}
      <aside className="hidden bg-night p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Wordmark />
        <div>
          <SignalArt className="w-full max-w-md" />
          <h2 className="mt-10 max-w-md font-display text-[44px] leading-[1.05] tracking-tight">Catch struggling students early. Act on every alert.</h2>
          <p className="mt-4 max-w-sm text-sm text-white/65">Weekly risk scores, plain-language reasons, and a named owner for every case.</p>
        </div>
        <p className="text-xs text-white/40">No alert without action.</p>
      </aside>

      {/* Sign-in */}
      <main className="relative flex min-h-screen flex-col items-center justify-center p-6">
        <button
          onClick={() => navigateTo('landing')}
          className="absolute left-6 top-6 flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Home
        </button>
        <div className="absolute right-6 top-5"><LanguageSwitcher /></div>
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden"><span className="font-display text-3xl">Disha</span></div>
          <h1 className="font-display text-[40px] leading-none tracking-tight">{t('Sign in')}</h1>
          <p className="mt-1.5 text-sm text-muted">Sign in with your campus Google account.</p>

          {error && (
            <div role="alert" className="mt-6 flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{error}</span>
            </div>
          )}

          <button
            type="button"
            onClick={handleGoogle}
            disabled={busy}
            className="mt-6 flex w-full cursor-pointer items-center justify-center gap-3 rounded-md border border-ink bg-panel py-3.5 text-sm font-semibold transition hover:bg-sunken disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : GOOGLE_ICON}
            {busy ? 'Connecting to Google…' : t('Continue with Google')}
          </button>

          <p className="mt-6 flex items-start gap-2 text-xs leading-relaxed text-muted">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
            Your role is set by your campus. We never see your Google password.
          </p>
          <p className="mt-3 text-xs text-muted">Can't sign in? Ask your campus admin to add your email.</p>
        </div>
      </main>
    </div>
  )
}

