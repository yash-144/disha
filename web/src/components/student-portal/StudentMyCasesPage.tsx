import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { friendlyDate, statusLabel } from '../../lib/labels'
import { useSupportRequests } from '../../lib/api/endpoints/student.hooks'

export function StudentMyCasesPage() {
  const reqs = useSupportRequests()
  return (
    <div className="mt-3 font-sans">
      <QueryState query={reqs} empty={<EmptyState title="You have not asked for help yet" message="When you do, it will show up here." />}>
        {(rows) => (
          <ul className="divide-y divide-line rounded-2xl border border-line bg-white text-xs">
            {rows.map((r) => (
              <li key={r.id} className="p-3">
                <div className="flex justify-between"><span className="font-semibold">{r.category}</span><span className="text-muted">{statusLabel(r.status)} · {friendlyDate(r.created_at)}</span></div>
                <p className="mt-1 text-ink-2">{r.student_note}</p>
                {r.faculty_response && <p className="mt-1 text-ink-2">Reply: {r.faculty_response}</p>}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </div>
  )
}
