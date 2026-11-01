import React, { useState } from 'react'
import { EmptyState, ErrorState, LoadingSkeleton } from '../common/QueryState'
import { useMlStudents } from '../../lib/api/endpoints/counsellor.hooks'
import { ApiError } from '../../lib/api/errors'

const TIERS = ['HIGH', 'MEDIUM', 'WATCH']

export function CounsellorStudentsInNeed() {
  const [tier, setTier] = useState('HIGH')
  const q = useMlStudents(tier)
  const noRun = q.error instanceof ApiError && (q.error.status === 404 || q.error.status === 409)
  return (
    <div className="flex flex-col gap-3 font-sans">
      <div className="flex gap-2">
        {TIERS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTier(t)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${tier === t ? 'bg-purple-700 text-white' : 'bg-white'}`}
          >
            {t}
          </button>
        ))}
      </div>
      {q.isPending ? (
        <LoadingSkeleton />
      ) : noRun ? (
        <EmptyState title="No scoring run yet" message="An administrator needs to import data and run scoring before risk tiers appear here." />
      ) : q.isError ? (
        <ErrorState error={q.error} onRetry={() => void q.refetch()} />
      ) : q.data.items.length === 0 ? (
        <EmptyState title={`No ${tier} tier students`} />
      ) : (
        <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
          {q.data.items.map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-3 p-3">
              <span className="font-mono">{s.student_ref}</span>
              <span>{s.tier} ({Math.round(s.probability * 100)}%){s.direction ? `, ${s.direction}` : ''}</span>
              <span className="text-[#717E95]">{s.reasons.length} reasons</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
