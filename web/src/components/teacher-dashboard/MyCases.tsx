import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useFacultyCases } from '../../lib/api/endpoints/faculty.hooks'

export function MyCases({ onViewAll }: { onViewAll?: () => void }) {
  const cases = useFacultyCases()
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-line font-sans">
      <div className="flex items-center justify-between pb-2">
        <h2 className="text-sm font-bold text-ink">Cases in your classes</h2>
        <button onClick={onViewAll} className="text-xs font-medium text-muted hover:text-ink transition">
          View all
        </button>
      </div>
      <QueryState query={cases} empty={<EmptyState title="No cases yet" />}>
        {(rows) => (
          <div>
            <span className="text-3xl font-bold tracking-tight text-ink">{rows.length}</span>
            <p className="text-xs text-muted">
              {rows.filter((c) => c.priority === 'high' || c.priority === 'critical').length} high priority
            </p>
          </div>
        )}
      </QueryState>
    </div>
  )
}
