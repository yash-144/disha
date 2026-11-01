import React, { useEffect, useState } from 'react'
import { Sparkles, Shield, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { supabase, syncGoogleUserWithBackend } from '../../lib/auth/supabase'
import { UserRole } from '../../types'

export function AuthCallback() {
  const { switchRole, setCurrentUser, navigateTo } = useApp()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState<string>('')

  useEffect(() => {
    let isMounted = true

    async function handleAuthCallback() {
      try {
        const hash = window.location.hash
        const params = new URLSearchParams(window.location.search)

        // Check for error in query or hash
        const errorDesc =
          params.get('error_description') ||
          params.get('error') ||
          new URLSearchParams(hash.replace(/^#/, '')).get('error_description')

        if (errorDesc) {
          throw new Error(decodeURIComponent(errorDesc))
        }

        const savedRole = (localStorage.getItem('disha_selected_role') as UserRole) || 'counsellor'

        // 1. Check Supabase OAuth session
        if (supabase) {
          const { data, error } = await supabase.auth.getSession()
          if (error) throw error

          if (data.session?.user) {
            const user = data.session.user
            const email = user.email || ''
            const fullName =
              user.user_metadata?.full_name ||
              user.user_metadata?.name ||
              email.split('@')[0]
            const avatar =
              user.user_metadata?.avatar_url ||
              user.user_metadata?.picture ||
              'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80'

            // Sync with DISHA backend API
            await syncGoogleUserWithBackend({
              email,
              fullName,
              role: savedRole,
              avatarUrl: avatar,
            })

            if (isMounted) {
              switchRole(savedRole)
              setCurrentUser((prev) => ({
                ...prev,
                name: fullName,
                email,
                avatar,
                role: savedRole,
              }))
              setStatus('success')
              setTimeout(() => {
                window.history.replaceState({}, document.title, '/dashboard')
                navigateTo('dashboard', 'overview')
              }, 600)
              return
            }
          }
        }

        // 2. Check Direct Google OAuth Implicit Hash: #access_token=...
        if (hash.includes('access_token=')) {
          const hashParams = new URLSearchParams(hash.replace(/^#/, ''))
          const accessToken = hashParams.get('access_token')

          if (accessToken) {
            // Fetch Google userinfo
            const userInfoRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
              headers: { Authorization: `Bearer ${accessToken}` },
            })

            if (!userInfoRes.ok) {
              throw new Error('Failed to retrieve user profile from Google')
            }

            const profile = await userInfoRes.json()
            const email = profile.email || ''
            const fullName = profile.name || email.split('@')[0]
            const avatar =
              profile.picture ||
              'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80'

            // Sync with backend
            await syncGoogleUserWithBackend({
              email,
              fullName,
              role: savedRole,
              avatarUrl: avatar,
            })

            if (isMounted) {
              switchRole(savedRole)
              setCurrentUser((prev) => ({
                ...prev,
                name: fullName,
                email,
                avatar,
                role: savedRole,
              }))
              setStatus('success')
              setTimeout(() => {
                window.history.replaceState({}, document.title, '/dashboard')
                navigateTo('dashboard', 'overview')
              }, 600)
              return
            }
          }
        }

        // 3. Fallback: If redirected without credentials, check if user was already signed in
        const existingToken = localStorage.getItem('disha_access_token')
        if (existingToken) {
          setStatus('success')
          setTimeout(() => {
            navigateTo('dashboard', 'overview')
          }, 400)
          return
        }

        throw new Error('No valid authentication token or session found in callback')
      } catch (err: any) {
        console.error('OAuth Callback processing failed:', err)
        if (isMounted) {
          setStatus('error')
          setErrorMessage(err.message || 'Authentication failed. Please try again.')
        }
      }
    }

    void handleAuthCallback()

    return () => {
      isMounted = false
    }
  }, [navigateTo, setCurrentUser, switchRole])

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl text-center">
        {/* DISHA Brand Logo */}
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 mb-6">
          <Shield className="w-8 h-8" />
        </div>

        {status === 'loading' && (
          <div className="space-y-4">
            <div className="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500 mb-2"></div>
            <h2 className="text-xl font-bold text-white tracking-tight">Authenticating with Google</h2>
            <p className="text-slate-400 text-sm">
              Verifying your credentials and establishing your secure institutional tenancy session...
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 mb-2">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">Authentication Successful!</h2>
            <p className="text-slate-400 text-sm">Redirecting you to your role workspace portal...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 mb-2">
              <AlertCircle className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">Sign-in Incomplete</h2>
            <p className="text-rose-300 text-sm bg-rose-950/50 border border-rose-900/50 rounded-lg p-3">
              {errorMessage}
            </p>
            <button
              onClick={() => navigateTo('login')}
              className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all"
            >
              <span>Back to Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

