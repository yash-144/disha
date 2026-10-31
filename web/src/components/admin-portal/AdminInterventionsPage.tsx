import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useCatalogue } from '../../lib/api/endpoints/admin.hooks'

export function AdminInterventionsPage() {
  const q = useCatalogue()
  return (
    <QueryState query={q} empty={<EmptyState title="No interventions in the catalogue" />}>
      {(rows) => (
        <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white font-sans text-xs">
          {rows.map((i) => (
            <li key={i.id} className="p-3">
              <b>{i.name}</b> <span className="text-[#717E95]">{i.category ?? ''}{i.is_active ? '' : ' (inactive)'}</span>
              {i.description && <p className="mt-1 text-[#4A5568]">{i.description}</p>}
            </li>
          ))}
        </ul>
      )}
    </QueryState>
  )
}
