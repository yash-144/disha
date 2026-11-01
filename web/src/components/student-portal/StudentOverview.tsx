import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { usePulseStatus, usePulseTrends, useRewardBalance, useSupportRequests } from '../../lib/api/endpoints/student.hooks'

export function StudentOverview({ onCheckIn }: { onCheckIn: () => void }) {
  const status = usePulseStatus()
  const trends = usePulseTrends()
  const balance = useRewardBalance()
  const reqs = useSupportRequests()
  return (
    <div className="mt-3 flex flex-col gap-4 font-sans">
      <section className="rounded-3xl border border-gray-100 bg-white p-5 text-xs">
        <h2 className="text-sm font-bold">This week's check-in</h2>
        <QueryState query={status} empty={<EmptyState title="No open check-in" />}>
          {(s) => s.completed ? <p className="mt-2">Completed. Thank you.</p> : (
            <button type="button" onClick={onCheckIn} className="mt-2 rounded-full bg-purple-700 px-4 py-2 font-bold text-white">Take the check-in</button>
          )}
        </QueryState>
      </section>
      <section className="rounded-3xl border border-gray-100 bg-white p-5 text-xs">
        <h2 className="text-sm font-bold">Wellbeing trend</h2>
        <QueryState query={trends} empty={<EmptyState title="No trend data yet" />}>
          {(pts) => (
            <ul className="mt-2 space-y-1">
              {pts.map((p) => <li key={p.period_id}>{p.label}: {p.suppressed || p.index_score == null ? 'not enough responses to show' : Math.round(p.index_score)}</li>)}
            </ul>
          )}
        </QueryState>
      </section>
      <div className="grid gap-4 md:grid-cols-2 text-xs">
        <section className="rounded-3xl border border-gray-100 bg-white p-5">
          <h2 className="text-sm font-bold">Reward points</h2>
          <QueryState query={balance}>{(b) => <p className="mt-2 text-2xl font-bold">{b.balance}</p>}</QueryState>
        </section>
        <section className="rounded-3xl border border-gray-100 bg-white p-5">
          <h2 className="text-sm font-bold">Support requests</h2>
          <QueryState query={reqs} empty={<EmptyState title="None yet" />}>{(r) => <p className="mt-2 text-2xl font-bold">{r.length}</p>}</QueryState>
        </section>
      </div>
    </div>
  )
}
