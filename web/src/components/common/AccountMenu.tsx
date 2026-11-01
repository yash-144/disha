import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQueries } from '@tanstack/react-query'
import { Check, ChevronDown, LogOut, Repeat } from 'lucide-react'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { api } from '../../lib/api/client'
import { useT } from '../../i18n'
import { UserAvatar } from './UserAvatar'

/** The user's active memberships with campus names (one lookup per campus, cached). */
export function useMembershipOptions() {
  const { user, membership } = useSession()
  const active = (user?.memberships ?? []).filter((m) => m.is_active)
  const names = useQueries({
    queries: active.map((m) => ({
      queryKey: ['identity', 'campus-name', m.campus_id],
      queryFn: () => api.get<{ name: string }>('/api/v1/campus', { campusId: m.campus_id }),
      staleTime: 30 * 60_000,
      retry: false,
    })),
  })
  const options = active.map((m, i) => ({
    key: m.id ?? `${m.campus_id}-${m.role}`,
    campusId: m.campus_id,
    role: m.role,
    campusName: names[i]?.data?.name ?? `Campus ${m.campus_id.slice(0, 4)}`,
    current: m.campus_id === membership?.campus_id && m.role === membership?.role,
  }))
  return options
}

/** Popover that never clips: fixed to the viewport, opens up or down depending on room, scrolls if still too tall. */
export function Popover({ anchor, open, onClose, align = 'start', width = 288, children, label }: {
  anchor: React.RefObject<HTMLElement | null>
  open: boolean
  onClose: () => void
  align?: 'start' | 'end'
  width?: number
  children: React.ReactNode
  label: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState<{ top: number; left: number; maxH: number } | null>(null)

  const place = useCallback(() => {
    const a = anchor.current
    const m = ref.current
    if (!a || !m) return
    const r = a.getBoundingClientRect()
    const vw = window.innerWidth
    const vh = window.innerHeight
    const w = Math.min(width, vw - 16)
    const h = m.scrollHeight
    const above = r.top - 12
    const below = vh - r.bottom - 12
    const up = below < h && above > below
    const maxH = Math.max(160, up ? above : below)
    const height = Math.min(h, maxH)
    const top = up ? r.top - 8 - height : r.bottom + 8
    let left = align === 'end' ? r.right - w : r.left
    left = Math.max(8, Math.min(left, vw - w - 8))
    setPos({ top: Math.max(8, top), left, maxH })
  }, [anchor, align, width])

  useLayoutEffect(() => { if (open) place() }, [open, place, children])
  useEffect(() => {
    if (!open) { setPos(null); return }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { onClose(); (anchor.current as HTMLElement | null)?.focus() } }
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node
      if (!ref.current?.contains(t) && !anchor.current?.contains(t)) onClose()
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onDown)
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onDown)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
  }, [open, onClose, place, anchor])
  useEffect(() => { if (pos) ref.current?.querySelector<HTMLElement>('button, select, [tabindex]')?.focus() }, [!!pos]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return null
  return createPortal(
    <div
      ref={ref}
      role="dialog"
      aria-label={label}
      style={{ position: 'fixed', top: pos?.top ?? 0, left: pos?.left ?? 0, width: Math.min(width, window.innerWidth - 16), maxHeight: pos?.maxH, visibility: pos ? 'visible' : 'hidden' }}
      className="z-[70] overflow-y-auto rounded-lg border border-line bg-panel font-sans text-ink shadow-xl"
    >
      {children}
    </div>,
    document.body,
  )
}

/** Signed-in user menu: who you are, current role + campus, switch between memberships, sign out. */
export function AccountMenu({ tone = 'light', variant = 'default' }: { tone?: 'light' | 'dark'; variant?: 'default' | 'sidebar' }) {
  const side = variant === 'sidebar'
  if (side) tone = 'dark'
  const t = useT()
  const { user, membership, setActiveRole, signOut } = useSession()
  const [open, setOpen] = useState(false)
  const btn = useRef<HTMLButtonElement>(null)
  const options = useMembershipOptions()
  const current = options.find((o) => o.current)
  const close = useCallback(() => setOpen(false), [])

  return (
    <div className="relative font-sans">
      <button
        ref={btn}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={t('Account menu')}
        className={`flex items-center gap-2.5 text-left transition ${side ? 'w-full justify-center rounded-md p-1.5 hover:bg-night-2 lg:justify-start' : `rounded-full border py-1 pl-1 pr-2.5 ${tone === 'dark' ? 'border-white/20 text-white hover:bg-white/10' : 'border-line bg-white hover:bg-sunken'}`}`}
      >
        <UserAvatar name={user?.full_name} />
        <span className={`min-w-0 flex-1 ${side ? 'hidden lg:block' : 'hidden sm:block'}`}>
          <span className="block truncate text-xs font-semibold leading-tight">{user?.full_name}</span>
          <span className={`block truncate text-xs leading-tight ${tone === 'dark' ? 'text-white/55' : 'text-muted'}`}>{t(roleLabel(membership?.role))}</span>
        </span>
        <ChevronDown className={`h-3.5 w-3.5 opacity-60 ${side ? 'hidden lg:block' : ''}`} />
      </button>

      <Popover anchor={btn} open={open} onClose={close} align="start" label={t('Account menu')}>
        <div className="border-b border-line p-3.5">
          <p className="truncate text-sm font-bold">{user?.full_name}</p>
          <p className="truncate text-xs text-muted">{user?.email}</p>
          {current && <p className="mt-1.5 text-xs font-semibold text-accent">{t(roleLabel(current.role))} · {current.campusName}</p>}
        </div>
        {options.length > 1 && (
          <div className="border-b border-line p-2">
            <p className="flex items-center gap-1.5 px-2 pb-1 pt-1 text-xs font-semibold text-muted"><Repeat className="h-3 w-3" /> {t('Switch role')}</p>
            {options.map((o) => (
              <button key={o.key} type="button" role="menuitemradio" aria-checked={o.current} onClick={() => { close(); setActiveRole(o.campusId, o.role) }} className="flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-2 text-left text-xs hover:bg-sunken">
                <span className="min-w-0"><span className="block truncate font-semibold">{t(roleLabel(o.role))}</span><span className="block truncate text-xs text-muted">{o.campusName}</span></span>
                {o.current && <Check className="h-4 w-4 text-accent" />}
              </button>
            ))}
          </div>
        )}
        <button type="button" onClick={() => void signOut()} className="flex w-full items-center gap-2 px-4 py-3 text-xs font-semibold text-tier-high hover:bg-rose-50">
          <LogOut className="h-4 w-4" /> {t('Sign out')}
        </button>
      </Popover>
    </div>
  )
}
