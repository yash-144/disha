import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useAdminCases } from '../../lib/api/endpoints/admin.hooks'

export function AdminCaseManagementPage() {
  const q = useAdminCases()
  return (
    <QueryState query={q} empty={<EmptyState title="No cases" />}>
      {(rows) => (
        <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white font-sans text-xs">
          {rows.map((c) => (
            <li key={c.id} className="flex justify-between gap-3 p-3">
              <span>{c.student_name ?? c.student_ref ?? 'Student'}{c.department ? ` (${c.department})` : ''}</span>
              <span className="text-[#717E95]">{c.state}, {c.priority}{c.owner_name ? `, ${c.owner_name}` : ''}{c.is_overdue ? ', overdue' : ''}</span>
            </li>
          ))}
        </ul>
      )}
    </QueryState>
  )
}
