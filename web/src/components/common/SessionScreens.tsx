import React from 'react'
import { Loader2, LockKeyhole } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { ErrorState } from './QueryState'

function Shell({ title, children }: { title: string; children?: React.ReactNode }) {
  const { navigateTo } = useApp()
  return (
    <main className="flex min-h-screen items-center justify-center bg-paper p-6 font-sans">
      <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-8 text-center shadow-sm">
        <LockKeyhole className="mx-auto h-6 w-6 text-ink" aria-hidden="true" />
        <h1 className="text-lg font-bold tracking-tight text-ink">{title}</h1>
        {children}
        <button
          type="button"
          onClick={() => navigateTo('landing')}
          className="text-xs font-semibold text-muted underline underline-offset-2 hover:text-ink"
        >
          Back to home
        </button>
      </div>
    </main>
  )
}

export function SessionLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper" role="status">
      <Loader2 className="h-6 w-6 animate-spin text-muted" aria-hidden="true" />
      <span className="sr-only">Loading</span>
    </div>
  )
}

/** Shown instead of a portal when there is no signed-in user. */
export function SignInNotSetUp() {
  return (
    <Shell title="Sign-in is not set up yet">
      <p className="text-sm text-muted">
        Portals open once sign-in is available for your campus. Please check back soon.
      </p>
    </Shell>
  )
}

export function NotProvisioned() {
  const { signOut } = useSession()
  return (
    <Shell title="No campus account found">
      <p className="text-sm text-muted">
        Your sign-in is valid, but it is not linked to a DISHA campus account. Ask your campus admin for an invite.
      </p>
      <button
        type="button"
        onClick={() => void signOut()}
        className="rounded-full border border-line px-4 py-1.5 text-xs font-semibold text-ink hover:bg-gray-50"
      >
        Sign out
      </button>
    </Shell>
  )
}

export function NoPortalForRole() {
  const { role, signOut } = useSession()
  return (
    <Shell title="No portal for your role yet">
      <p className="text-sm text-muted">
        You are signed in as {roleLabel(role)}, which does not have a portal in this version of DISHA.
      </p>
      <button
        type="button"
        onClick={() => void signOut()}
        className="rounded-full border border-line px-4 py-1.5 text-xs font-semibold text-ink hover:bg-gray-50"
      >
        Sign out
      </button>
    </Shell>
  )
}

export function ProfileLoadError() {
  const { error, retry } = useSession()
  return (
    <main className="flex min-h-screen items-center justify-center bg-paper p-6">
      <div className="w-full max-w-md">
        <ErrorState error={error} onRetry={retry} />
      </div>
    </main>
  )
}
