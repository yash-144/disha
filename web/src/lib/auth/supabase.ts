import { createClient, SupabaseClient, Session } from '@supabase/supabase-js'
import { AuthProvider, setAuthProvider } from './provider'
import { sessionStore } from './sessionStore'

const supabaseUrl =
  (import.meta.env.VITE_SUPABASE_URL as string) ||
  'https://endyirtqxbepbndqayrh.supabase.co'

const supabaseAnonKey =
  (import.meta.env.VITE_SUPABASE_ANON_KEY as string) || ''

export function isSupabaseConfigured(): boolean {
  return Boolean(
    supabaseAnonKey &&
      !supabaseAnonKey.includes('placeholder') &&
      !supabaseAnonKey.includes('YOUR_') &&
      supabaseAnonKey.length > 20
  )
}

// Create Supabase client instance (or null dummy if no key provided)
export const supabase: SupabaseClient | null = isSupabaseConfigured()
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null

/**
 * Triggers Google OAuth sign-in via Supabase
 */
export async function signInWithGoogle(selectedRole?: string): Promise<{ error: Error | null }> {
  if (selectedRole) {
    localStorage.setItem('disha_selected_role', selectedRole)
  }

  const redirectUri =
    (import.meta.env.VITE_GOOGLE_REDIRECT_URI as string) ||
    `${window.location.origin}/auth/callback`

  if (!supabase) {
    return {
      error: new Error('Supabase anon key is not configured. Add VITE_SUPABASE_ANON_KEY to web/.env'),
    }
  }

  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: redirectUri,
      queryParams: {
        access_type: 'offline',
        prompt: 'select_account',
      },
    },
  })

  return { error: error ? new Error(error.message) : null }
}

/**
 * Syncs authenticated user with DISHA backend to receive canonical JWT & tenancy context
 */
export async function syncGoogleUserWithBackend(payload: {
  email: string
  fullName?: string
  role?: string
  avatarUrl?: string
}): Promise<string | null> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || ''
  const directApi = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'
  const targetUrl = apiBase ? `${apiBase}/api/v1/identity/google` : `${directApi}/api/v1/identity/google`

  try {
    // The server verifies this token; the role and campus come from the database, never from the client.
    const { data: sessionData } = (await supabase?.auth.getSession()) ?? { data: { session: null } }
    const supabaseToken = sessionData.session?.access_token
    if (!supabaseToken) return null

    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${supabaseToken}` },
      body: JSON.stringify({ full_name: payload.fullName, avatar_url: payload.avatarUrl }),
    })
    if (!res.ok) {
      console.warn('Backend sync returned non-OK status:', res.status)
      return null
    }
    return storeBackendSession(await res.json())
  } catch (err) {
    console.error('Failed to sync Google user with backend:', err)
  }

  return null
}

export interface BackendTokenResponse {
  access_token?: string
  memberships?: { campus_id: string }[]
}

function storeBackendSession(data: BackendTokenResponse): string | null {
  if (!data.access_token) return null
  localStorage.setItem('disha_access_token', data.access_token)
  if (data.memberships?.[0]?.campus_id) sessionStore.setCampusId(data.memberships[0].campus_id)
  return data.access_token
}

/** Email + password sign-in against the DISHA API (seeded demo accounts and provisioned staff). */
export async function signInWithPassword(email: string, password: string): Promise<{ error: Error | null }> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || ''
  try {
    const res = await fetch(`${apiBase}/api/v1/identity/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return { error: new Error(body.detail || 'Sign-in failed') }
    }
    storeBackendSession(await res.json())
    return { error: null }
  } catch {
    return { error: new Error('Could not reach the DISHA server') }
  }
}

/**
 * Supabase Auth Provider implementing DISHA AuthProvider interface
 */
export const supabaseAuthProvider: AuthProvider = {
  async getAccessToken(): Promise<string | null> {
    // 1. Check if backend-synced DISHA token exists in localStorage
    const dishaToken = localStorage.getItem('disha_access_token')
    if (dishaToken) return dishaToken

    // 2. Check Supabase session
    if (supabase) {
      try {
        // A Supabase session alone is not accepted by the API: exchange it for a DISHA token.
        const { data } = await supabase.auth.getSession()
        const user = data.session?.user
        if (user?.email) {
          return await syncGoogleUserWithBackend({
            email: user.email,
            fullName: user.user_metadata?.full_name || user.user_metadata?.name,
            avatarUrl: user.user_metadata?.avatar_url,
          })
        }
      } catch (e) {
        console.warn('Error reading Supabase session:', e)
      }
    }

    return null
  },

  async refresh(): Promise<string | null> {
    if (supabase) {
      try {
        const { data, error } = await supabase.auth.refreshSession()
        if (!error && data.session?.access_token) {
          return data.session.access_token
        }
      } catch (e) {
        console.warn('Error refreshing Supabase session:', e)
      }
    }
    return null
  },

  async signOut(): Promise<void> {
    localStorage.removeItem('disha_access_token')
    localStorage.removeItem('disha_selected_role')
    sessionStore.setCampusId(null)
    if (supabase) {
      try {
        await supabase.auth.signOut()
      } catch (e) {
        console.warn('Error signing out of Supabase:', e)
      }
    }
  },

  onChange(listener: () => void): () => void {
    if (!supabase) {
      return () => {}
    }
    const { data: authListener } = supabase.auth.onAuthStateChange(
      (_event: string, _session: Session | null) => {
        listener()
      }
    )
    return () => {
      authListener.subscription.unsubscribe()
    }
  },
}

