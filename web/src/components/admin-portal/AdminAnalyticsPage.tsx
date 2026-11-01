import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useAnalyticsOverview } from '../../lib/api/endpoints/admin.hooks'

function flatten(o: unknown, prefix = ''): [string, string][] {
  if (o == null || typeof o !== 'object') return [[prefix, String(o)]]
  return Object.entries(o as Record<string, unknown>).flatMap(([k, v]) =>
    v != null && typeof v === 'object' && !Array.isArray(v) ? flatten(v, prefix ? `${prefix}.${k}` : k) : [[prefix ? `${prefix}.${k}` : k, JSON.stringify(v)] as [string, string]],
  )
}

export function AdminAnalyticsPage() {
  const q = useAnalyticsOverview()
  return (
    <QueryState query={q} isEmpty={(d) => !d || Object.keys(d).length === 0} empty={<EmptyState title="No analytics yet" />}>
      {(d) => (
        <dl className="grid grid-cols-2 gap-3 font-sans text-xs md:grid-cols-4">
          {flatten(d).map(([k, v]) => (
            <div key={k} className="rounded-2xl border border-gray-100 bg-white p-4">
              <dd className="text-lg font-bold">{v}</dd>
              <dt className="text-[#717E95]">{k.replace(/[._]/g, ' ')}</dt>
            </div>
          ))}
        </dl>
      )}
    </QueryState>
  )
}
