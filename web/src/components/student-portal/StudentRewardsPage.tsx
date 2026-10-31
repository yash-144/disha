import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { NotAvailable } from '../common/NotAvailable'
import { errorMessage } from '../../lib/api/errors'
import { useMyRedemptions, useRedeem, useRewardBalance, useRewardCatalog } from '../../lib/api/endpoints/student.hooks'

export function StudentRewardsPage() {
  const balance = useRewardBalance()
  const catalog = useRewardCatalog()
  const mine = useMyRedemptions()
  const redeem = useRedeem()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const doRedeem = (id: string, name: string) => {
    setMsg(null)
    redeem.mutate(id, {
      onSuccess: () => setMsg({ ok: true, text: `Redemption requested for ${name}.` }),
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  return (
    <div className="mt-3 flex flex-col gap-4 font-sans">
      <QueryState query={balance}>{(b) => <p className="text-sm font-bold">Points balance: {b.balance}</p>}</QueryState>
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</p>}
      <QueryState query={catalog} empty={<EmptyState title="No rewards available" />}>
        {(items) => (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
            {items.map((i) => (
              <li key={i.id} className="flex items-center justify-between gap-3 p-3">
                <span><b>{i.name}</b> {i.description}</span>
                <span className="text-[#717E95]">{i.cost_points} pts, stock {i.stock}</span>
                <button type="button" disabled={!i.is_available || redeem.isPending} onClick={() => doRedeem(i.id, i.name)} className="rounded-full bg-purple-700 px-3 py-1 font-bold text-white disabled:opacity-50">Redeem</button>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
      <h3 className="text-sm font-bold">My redemptions</h3>
      <QueryState query={mine} empty={<EmptyState title="No redemptions yet" />}>
        {(rows) => (
          <ul className="rounded-2xl border border-gray-100 bg-white text-xs">
            {rows.map((r) => <li key={r.id} className="flex justify-between p-3"><span>{new Date(r.created_at).toLocaleDateString()}, {r.cost_points} pts</span><span>{r.status}</span></li>)}
          </ul>
        )}
      </QueryState>
      <NotAvailable title="Leaderboard" />
    </div>
  )
}
