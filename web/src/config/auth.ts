/**
 * Google OAuth 2.0 & Authentication Configuration for DISHA / SkillsUp
 * Reads variables from Vite's import.meta.env with safe development fallbacks.
 */

export interface GoogleAuthConfig {
  clientId: string
  authUrl: string
  redirectUri: string
  scope: string
  responseType: string
}

export const GOOGLE_AUTH_CONFIG: GoogleAuthConfig = {
  clientId:
    (import.meta.env.VITE_GOOGLE_CLIENT_ID as string) ||
    'placeholder-google-client-id.apps.googleusercontent.com',
  authUrl:
    (import.meta.env.VITE_GOOGLE_AUTH_URL as string) ||
    'https://accounts.google.com/o/oauth2/v2/auth',
  redirectUri:
    (import.meta.env.VITE_GOOGLE_REDIRECT_URI as string) ||
    (typeof window !== 'undefined' ? `${window.location.origin}/auth/callback` : 'http://localhost:5173/auth/callback'),
  scope: 'openid email profile',
  responseType: 'token',
}

/**
 * Returns true if real Google Client credentials are configured
 */
export function isGoogleAuthLive(): boolean {
  const cid = import.meta.env.VITE_GOOGLE_CLIENT_ID
  return Boolean(cid && !cid.includes('placeholder') && !cid.includes('your-google-client-id'))
}

/**
 * Constructs the standard Google OAuth 2.0 authorization URL
 */
export function buildGoogleOAuthUrl(stateParam = 'disha_onboarding'): string {
  const params = new URLSearchParams({
    client_id: GOOGLE_AUTH_CONFIG.clientId,
    redirect_uri: GOOGLE_AUTH_CONFIG.redirectUri,
    response_type: GOOGLE_AUTH_CONFIG.responseType,
    scope: GOOGLE_AUTH_CONFIG.scope,
    include_granted_scopes: 'true',
    prompt: 'select_account',
    state: stateParam,
  })

  return `${GOOGLE_AUTH_CONFIG.authUrl}?${params.toString()}`
}
