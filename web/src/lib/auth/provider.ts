/**
 * Minimal auth seam for the API client.
 *
 * No sign-in is wired up yet, so the default provider has no token. The
 * planned provider is Supabase Google sign-in: implement `AuthProvider` with
 * supabase-js (getAccessToken from `supabase.auth.getSession()`, refresh from
 * `refreshSession()`, signOut from `supabase.auth.signOut()`) and register it
 * with `setAuthProvider()` in main.tsx. Nothing else needs to change.
 */
export interface AuthProvider {
  /** Current bearer token, or null when nobody is signed in. */
  getAccessToken(): Promise<string | null>
  /** Try to renew the token after a 401. Return the new token, or null. */
  refresh?(): Promise<string | null>
  signOut?(): Promise<void>
  /** Subscribe to sign-in/out/token changes. Returns an unsubscribe function. */
  onChange?(listener: () => void): () => void
}

const noProvider: AuthProvider = {
  getAccessToken: async () => null,
}

let provider: AuthProvider = noProvider

export function setAuthProvider(next: AuthProvider | null) {
  provider = next ?? noProvider
}

export function getAuthProvider(): AuthProvider {
  return provider
}

/** Convenience used by the API client. */
export function getAccessToken(): Promise<string | null> {
  return provider.getAccessToken()
}
