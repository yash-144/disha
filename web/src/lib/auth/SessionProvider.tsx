import React, { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useMe } from '../api/hooks'
import { onUnauthorized } from '../api/client'
import { ApiError } from '../api/errors'
import type { Me, Membership } from '../api/endpoints/identity'
import { getAccessToken, getAuthProvider } from './provider'
import { sessionStore } from './sessionStore'
import { portalForRole, type Portal } from './portals'

export type SessionStatus =
  | 'loading' // checking for a token / loading the profile
  | 'unauthenticated' // no token: sign-in is not set up yet (or the user signed out)
  | 'authenticated'
  | 'not_provisioned' // token is valid but the account has no active campus membership
  | 'error' // profile could not be loaded (network/server)

export interface SessionValue {
  status: SessionStatus
  user: Me | null
  /** Active membership (campus + role). The role is what decides the portal. */
  membership: Membership | null
  role: string | null
  /** Portal for the role, or null when the role has no portal. */
  portal: Portal | null
  error: Error | null
  signOut: () => Promise<void>
  retry: () => void
  setActiveCampus: (campusId: string) => void
}

const SessionContext = createContext<SessionValue | undefined>(undefined)

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient()
  // undefined = still checking the auth provider
  const [hasToken, setHasToken] = useState<boolean | undefined>(undefined)
  const campusId = useSyncExternalStore(sessionStore.subscribe, sessionStore.getCampusId)

  useEffect(() => {
    let active = true
    const check = () =>
      getAccessToken().then((t) => {
        if (active) setHasToken(Boolean(t))
      })
    void check()
    const unsubscribe = getAuthProvider().onChange?.(() => {
      queryClient.clear()
      void check()
    })
    return () => {
      active = false
      unsubscribe?.()
    }
  }, [queryClient])

  useEffect(
    () =>
      onUnauthorized(() => {
        queryClient.clear()
        sessionStore.setCampusId(null)
        setHasToken(false)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }),
    [queryClient],
  )

  const me = useMe({ enabled: hasToken === true })

  // A token for an account that no longer exists (404 on /me) is stale: drop it and show sign-in.
  useEffect(() => {
    if (me.error instanceof ApiError && me.error.status === 404) {
      void getAuthProvider().signOut?.()
      queryClient.clear()
      setHasToken(false)
    }
  }, [me.error, queryClient])

  const membership = useMemo<Membership | null>(() => {
    const active = me.data?.memberships.filter((m) => m.is_active) ?? []
    if (!active.length) return null
    return active.find((m) => m.campus_id === campusId) ?? active[0]
  }, [me.data, campusId])

  // Keep X-Campus-ID in step with the resolved membership.
  useEffect(() => {
    if (membership && membership.campus_id !== campusId) sessionStore.setCampusId(membership.campus_id)
  }, [membership, campusId])

  const signOut = useCallback(async () => {
    await getAuthProvider().signOut?.()
    queryClient.clear()
    sessionStore.setCampusId(null)
    setHasToken(false)
    window.location.href = '/login'
  }, [queryClient])

  const value = useMemo<SessionValue>(() => {
    const err = me.error
    const denied = err instanceof ApiError && (err.status === 403 || err.status === 404)
    let status: SessionStatus
    if (hasToken === undefined) status = 'loading'
    else if (!hasToken) status = 'unauthenticated'
    else if (me.isError) status = denied ? 'not_provisioned' : 'error'
    else if (me.isPending) status = 'loading'
    else if (!membership) status = 'not_provisioned'
    else status = 'authenticated'

    const role = membership?.role ?? null
    return {
      status,
      user: me.data ?? null,
      membership,
      role,
      portal: portalForRole(role),
      error: err,
      signOut,
      retry: () => void me.refetch(),
      setActiveCampus: (id) => {
        if (id === sessionStore.getCampusId()) return
        // Drop every campus-scoped cache (keep the profile), then re-resolve the portal for the new membership.
        queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'identity' })
        sessionStore.setCampusId(id)
        if (window.location.pathname !== '/dashboard') window.history.replaceState({}, '', '/dashboard')
      },
    }
  }, [hasToken, me, membership, signOut, queryClient])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): SessionValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within a SessionProvider')
  return ctx
}
