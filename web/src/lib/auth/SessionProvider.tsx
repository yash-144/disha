import React, { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useMe } from '../api/hooks'
import { onUnauthorized } from '../api/client'
import { ApiError } from '../api/errors'
import type { Me, Membership } from '../api/endpoints/identity'
import { getAccessToken, getAuthProvider } from './provider'
import { sessionStore } from './sessionStore'
import { portalForRole, type Portal } from './portals'

// Same default order as the backend when no X-Role is sent.
const ROLE_PRIORITY = ['platform_admin', 'institution_admin', 'hod', 'counsellor', 'faculty', 'mentor', 'student']

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
  /** Switch to another membership (campus + role) without reloading or signing out. */
  setActiveRole: (campusId: string, role: string) => void
}

const SessionContext = createContext<SessionValue | undefined>(undefined)

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient()
  // undefined = still checking the auth provider
  const [hasToken, setHasToken] = useState<boolean | undefined>(undefined)
  const campusId = useSyncExternalStore(sessionStore.subscribe, sessionStore.getCampusId)
  const activeRole = useSyncExternalStore(sessionStore.subscribe, sessionStore.getRole)

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
    const rank = (m: Membership) => {
      const i = ROLE_PRIORITY.indexOf(m.role)
      return i === -1 ? 99 : i
    }
    const inCampus = active.filter((m) => m.campus_id === campusId)
    const pool = inCampus.length ? inCampus : active
    return pool.find((m) => m.role === activeRole && (inCampus.length || m.campus_id === campusId || !campusId)) ?? [...pool].sort((x, y) => rank(x) - rank(y))[0]
  }, [me.data, campusId, activeRole])

  // Keep X-Campus-ID and X-Role in step with the resolved membership.
  useEffect(() => {
    if (!membership) return
    if (membership.campus_id !== campusId) sessionStore.setCampusId(membership.campus_id)
    if (membership.role !== activeRole) sessionStore.setRole(membership.role)
  }, [membership, campusId, activeRole])

  const signOut = useCallback(async () => {
    await getAuthProvider().signOut?.()
    queryClient.clear()
    sessionStore.setCampusId(null)
    sessionStore.setRole(null)
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
      setActiveRole: (cid, r) => {
        if (cid === sessionStore.getCampusId() && r === sessionStore.getRole()) return
        // Different role means different data: drop every campus-scoped cache (keep the profile), no reload, no sign-out.
        queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'identity' })
        sessionStore.setCampusId(cid)
        sessionStore.setRole(r)
        if (window.location.pathname !== '/dashboard') window.history.replaceState({}, '', '/dashboard')
      },
      setActiveCampus: (id) => {
        if (id === sessionStore.getCampusId()) return
        // Drop every campus-scoped cache (keep the profile), then re-resolve the portal for the new membership.
        queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'identity' })
        sessionStore.setCampusId(id)
        sessionStore.setRole(null)
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
