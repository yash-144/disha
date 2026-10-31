import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useFacultyCases } from '../../lib/api/endpoints/faculty.hooks'

export function MyCasesPage() {
  const cases = useFacultyCases()
  return (
    <main className="flex-1 p-4 font-sans">
      <h1 className="mb-3 text-lg font-bold text-[#1E2433]">My Cases</h1>
      <QueryState query={cases} empty={<EmptyState title="No cases" message="Cases you can see will appear here." />}>
        {(rows) => (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
            {rows.map((c) => (
              <li key={c.id} className="flex justify-between gap-3 p-3">
                <span>{c.student_name ?? c.student_ref ?? 'Student'}{c.department ? ` (${c.department})` : ''}</span>
                <span className="text-[#717E95]">{c.state}, {c.priority}{c.is_overdue ? ', overdue' : ''}</span>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </main>
  )
}
