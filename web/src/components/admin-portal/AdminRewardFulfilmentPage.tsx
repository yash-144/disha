import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useAdminRedemptions, useSetRedemptionStatus } from '../../lib/api/endpoints/admin.hooks'

export function AdminRewardFulfilmentPage() {
  const q = useAdminRedemptions()
  const set = useSetRedemptionStatus()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const act = (id: string, status: string) => {
    setMsg(null)
    set.mutate({ id, status }, {
      onSuccess: () => setMsg({ ok: true, text: `Redemption marked ${status}.` }),
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  return (
    <div className="flex flex-col gap-3 font-sans">
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</p>}
      <QueryState query={q} empty={<EmptyState title="No redemptions" />}>
        {(rows) => (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
            {rows.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-3 p-3">
                <span>{new Date(r.created_at).toLocaleDateString()}, {r.cost_points} pts</span>
                <span>{r.status}</span>
                {r.status === 'pending' && (
                  <span className="flex gap-2">
                    {['approved', 'rejected'].map((s) => (
                      <button key={s} type="button" disabled={set.isPending} onClick={() => act(r.id, s)} className="rounded-full border border-gray-200 px-3 py-1 font-semibold capitalize disabled:opacity-50">{s}</button>
                    ))}
                  </span>
                )}
                {r.status === 'approved' && (
                  <button type="button" disabled={set.isPending} onClick={() => act(r.id, 'fulfilled')} className="rounded-full bg-purple-700 px-3 py-1 font-bold text-white disabled:opacity-50">Mark fulfilled</button>
                )}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </div>
  )
}
