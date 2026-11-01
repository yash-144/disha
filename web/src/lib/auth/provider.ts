/**
 * Minimal auth seam for the API client.
 *
 * Implements AuthProvider backed by Supabase Google sign-in and local token cache.
 */
import { supabaseAuthProvider } from './supabase'

export interface AuthProvider {
  /** Current bearer token, or null when nobody is signed in. */
  getAccessToken(): Promise<string | null>
  /** Try to renew the token after a 401. Return the new token, or null. */
  refresh?(): Promise<string | null>
  signOut?(): Promise<void>
  /** Subscribe to sign-in/out/token changes. Returns an unsubscribe function. */
  onChange?(listener: () => void): () => void
}

let provider: AuthProvider = supabaseAuthProvider

export function setAuthProvider(next: AuthProvider | null) {
  provider = next ?? supabaseAuthProvider
}

export function getAuthProvider(): AuthProvider {
  return provider
}

/** Convenience used by the API client. */
export function getAccessToken(): Promise<string | null> {
  return provider.getAccessToken()
}
