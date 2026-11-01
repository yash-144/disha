import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useSupportRequests } from '../../lib/api/endpoints/student.hooks'

export function StudentMyCasesPage() {
  const reqs = useSupportRequests()
  return (
    <div className="mt-3 font-sans">
      <QueryState query={reqs} empty={<EmptyState title="No support requests" message="Requests you make will appear here." />}>
        {(rows) => (
          <ul className="divide-y divide-line rounded-2xl border border-line bg-white text-xs">
            {rows.map((r) => (
              <li key={r.id} className="p-3">
                <div className="flex justify-between"><span className="font-semibold">{r.category}</span><span className="text-muted">{r.status}</span></div>
                <p className="mt-1 text-ink-2">{r.student_note}</p>
                {r.faculty_response && <p className="mt-1 text-ink-2">Response: {r.faculty_response}</p>}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </div>
  )
}
