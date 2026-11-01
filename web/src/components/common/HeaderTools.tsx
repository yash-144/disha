import React, { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, CheckCheck } from 'lucide-react'
import { api } from '../../lib/api/client'
import { fmtDateTime } from './ui'
import { LanguageSwitcher, RoleSwitcher } from './HeaderControls'

interface Notif {
  id: string
  title: string
  body?: string | null
  is_read: boolean
  created_at: string
}

/** Real notification bell (GET /notifications). */
export function NotificationBell() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const unread = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: ({ signal }) => api.get<{ unread: number }>('/api/v1/notifications/unread-count', { signal }),
    refetchInterval: 60_000,
    retry: false,
  })
  const list = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: ({ signal }) => api.get<{ items: Notif[] }>('/api/v1/notifications', { query: { limit: 10 }, signal }),
    enabled: open,
    retry: false,
  })
  const refresh = () => void qc.invalidateQueries({ queryKey: ['notifications'] })
  const readOne = useMutation({ mutationFn: (id: string) => api.patch(`/api/v1/notifications/${id}/read`), onSuccess: refresh })
  const readAll = useMutation({ mutationFn: () => api.post('/api/v1/notifications/read-all'), onSuccess: refresh })

  useEffect(() => {
    if (!open) return
    const h = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [open])

  const n = unread.data?.unread ?? 0
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={n ? `Notifications, ${n} unread` : 'Notifications'}
        aria-expanded={open}
        className="relative flex h-8 w-8 cursor-pointer items-center justify-center rounded-md border border-line bg-panel text-muted transition hover:text-ink"
      >
        <Bell className="h-4 w-4" />
        {n > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#EF4444] px-1 text-xs font-bold text-white ring-2 ring-panel">
            {n > 9 ? '9+' : n}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-lg border border-line bg-panel shadow-xl">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <p className="text-sm font-bold text-ink">Notifications</p>
            <button type="button" disabled={!n || readAll.isPending} onClick={() => readAll.mutate()} className="flex items-center gap-1 text-xs font-semibold text-indigo-600 disabled:opacity-40">
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </button>
          </div>
          <ul className="max-h-80 divide-y divide-line overflow-y-auto">
            {list.isPending && <li className="p-4 text-xs text-muted">Loading…</li>}
            {list.isError && <li className="p-4 text-xs text-rose-600">Could not load notifications.</li>}
            {list.data?.items.length === 0 && <li className="p-6 text-center text-xs text-muted">You are all caught up.</li>}
            {list.data?.items.map((x) => (
              <li key={x.id}>
                <button type="button" onClick={() => !x.is_read && readOne.mutate(x.id)} className={`w-full px-4 py-3 text-left hover:bg-gray-50 ${x.is_read ? '' : 'bg-indigo-50/40'}`}>
                  <p className="flex items-center gap-1.5 text-xs font-bold text-ink">
                    {!x.is_read && <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />}
                    {x.title}
                  </p>
                  {x.body && <p className="mt-0.5 text-xs text-ink-2">{x.body}</p>}
                  <p className="mt-0.5 text-xs text-muted">{fmtDateTime(x.created_at)}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export function HeaderTools() {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <RoleSwitcher />
      <LanguageSwitcher />
      <NotificationBell />
    </div>
  )
}
