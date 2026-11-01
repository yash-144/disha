import React, { useEffect, useState } from 'react'
import { supabase, syncGoogleUserWithBackend } from '../../lib/auth/supabase'

/** Finishes Google sign-in: swaps the Supabase session for a DISHA token, then opens the portal for the server-assigned role. */
export function AuthCallback() {
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
        const oauthError = params.get('error_description') || hash.get('error_description')
        if (oauthError) throw new Error(oauthError)

        const { data } = (await supabase?.auth.getSession()) ?? { data: { session: null } }
        const user = data.session?.user
        if (!user?.email) throw new Error('No Google session found. Please try again.')

        const token = await syncGoogleUserWithBackend({
          email: user.email,
          fullName: user.user_metadata?.full_name || user.user_metadata?.name,
          avatarUrl: user.user_metadata?.avatar_url,
        })
        if (!token) throw new Error('Could not sign you in to DISHA. Please try again.')
        localStorage.removeItem('disha_selected_role')
        if (!cancelled) window.location.replace('/dashboard')
      } catch (e) {
        if (!cancelled) setError('We could not sign you in. Please try again.')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f4f6f8] font-sans text-sm text-slate-600">
      {error ? (
        <div className="text-center">
          <p role="alert" className="text-rose-700">{error}</p>
          <a href="/login" className="mt-3 inline-block font-semibold text-slate-900 underline">Back to sign in</a>
        </div>
      ) : (
        <div className="flex items-center gap-2"><span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" /> Signing you in…</div>
      )}
    </div>
  )
}
