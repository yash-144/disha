import React from 'react'
import { Loader2, LockKeyhole } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { ErrorState } from './QueryState'

function Shell({ title, children }: { title: string; children?: React.ReactNode }) {
  const { navigateTo } = useApp()
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f7fc] p-6 font-sans">
      <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-8 text-center shadow-sm">
        <LockKeyhole className="mx-auto h-6 w-6 text-[#1E2433]" aria-hidden="true" />
        <h1 className="text-lg font-bold tracking-tight text-[#1E2433]">{title}</h1>
        {children}
        <button
          type="button"
          onClick={() => navigateTo('landing')}
          className="text-xs font-semibold text-[#64748B] underline underline-offset-2 hover:text-[#1E2433]"
        >
          Back to home
        </button>
      </div>
    </main>
  )
}

export function SessionLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f7fc]" role="status">
      <Loader2 className="h-6 w-6 animate-spin text-[#64748B]" aria-hidden="true" />
      <span className="sr-only">Loading</span>
    </div>
  )
}

/** Shown instead of a portal when there is no signed-in user. */
export function SignInNotSetUp() {
  return (
    <Shell title="Sign-in is not set up yet">
      <p className="text-sm text-[#717E95]">
        Portals open once sign-in is available for your campus. Please check back soon.
      </p>
    </Shell>
  )
}

export function NotProvisioned() {
  const { signOut } = useSession()
  return (
    <Shell title="No campus account found">
      <p className="text-sm text-[#717E95]">
        Your sign-in is valid, but it is not linked to a DISHA campus account. Ask your campus admin for an invite.
      </p>
      <button
        type="button"
        onClick={() => void signOut()}
        className="rounded-full border border-gray-200 px-4 py-1.5 text-xs font-semibold text-[#1E2433] hover:bg-gray-50"
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
      <p className="text-sm text-[#717E95]">
        You are signed in as {roleLabel(role)}, which does not have a portal in this version of DISHA.
      </p>
      <button
        type="button"
        onClick={() => void signOut()}
        className="rounded-full border border-gray-200 px-4 py-1.5 text-xs font-semibold text-[#1E2433] hover:bg-gray-50"
      >
        Sign out
      </button>
    </Shell>
  )
}

export function ProfileLoadError() {
  const { error, retry } = useSession()
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f7fc] p-6">
      <div className="w-full max-w-md">
        <ErrorState error={error} onRetry={retry} />
      </div>
    </main>
  )
}
