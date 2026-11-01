import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useFacultyCases } from '../../lib/api/endpoints/faculty.hooks'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { ChevronRight, AlertTriangle } from 'lucide-react'

export function MyCasesPage() {
  const cases = useFacultyCases()
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  return (
    <main className="flex-1 p-4 font-sans">
      <h1 className="mb-3 text-lg font-bold text-ink">My Monitored Cases</h1>
      <QueryState query={cases} empty={<EmptyState title="No cases" message="Cases within your academic department or sections will appear here." />}>
        {(rows) => (
          <div className="rounded-2xl border border-line bg-white shadow-xs overflow-hidden">
            <ul className="divide-y divide-line text-xs">
              {rows.map((c) => (
                <li
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className="flex justify-between items-center gap-3 p-3.5 hover:bg-gray-50 transition cursor-pointer"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900">{c.student_name ?? c.student_ref ?? 'Student'}</span>
                      {c.department && <span className="text-muted">({c.department})</span>}
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 uppercase">
                        {c.priority}
                      </span>
                      {c.is_overdue && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold flex items-center gap-1 border border-rose-200">
                          <AlertTriangle className="w-3 h-3" /> Overdue
                        </span>
                      )}
                    </div>
                    <span className="text-muted text-[11px]">
                      State: <span className="font-semibold uppercase text-indigo-600">{c.state}</span>
                    </span>
                  </div>

                  <span className="text-xs text-indigo-600 font-bold flex items-center gap-0.5 hover:underline">
                    View Trajectory <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </QueryState>

      {selectedCaseId && (
        <CaseDetailDrawer
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
          userRole="instructor"
        />
      )}
    </main>
  )
}
