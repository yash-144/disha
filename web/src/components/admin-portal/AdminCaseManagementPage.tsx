import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useAdminCases } from '../../lib/api/endpoints/admin.hooks'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { ChevronRight, AlertTriangle } from 'lucide-react'

export function AdminCaseManagementPage() {
  const q = useAdminCases()
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  return (
    <div className="font-sans">
      <div className="mb-3 flex justify-between items-center">
        <div>
          <h2 className="text-base font-bold text-[#1E2433]">Campus Case Governance</h2>
          <p className="text-xs text-gray-500">Monitor multi-campus escalations, case owners, and SLA deadlines.</p>
        </div>
      </div>

      <QueryState query={q} empty={<EmptyState title="No active cases across campus" />}>
        {(rows) => (
          <div className="rounded-2xl border border-gray-100 bg-white shadow-xs overflow-hidden">
            <ul className="divide-y divide-gray-100 text-xs">
              {rows.map((c) => (
                <li
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className="flex justify-between items-center gap-3 p-3.5 hover:bg-gray-50 transition cursor-pointer"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900">{c.student_name ?? c.student_ref ?? 'Student'}</span>
                      {c.department && <span className="text-[#717E95]">({c.department})</span>}
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 uppercase font-semibold">
                        {c.priority}
                      </span>
                      {c.is_overdue && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold flex items-center gap-1 border border-rose-200">
                          <AlertTriangle className="w-3 h-3" /> Overdue
                        </span>
                      )}
                    </div>
                    <span className="text-[#717E95] text-[11px]">
                      State: <span className="font-semibold uppercase text-indigo-600">{c.state}</span>
                      {c.owner_name && <> • Assigned to: <span className="text-gray-700 font-medium">{c.owner_name}</span></>}
                    </span>
                  </div>

                  <span className="text-xs text-indigo-600 font-bold flex items-center gap-0.5 hover:underline">
                    Govern &amp; Audit <ChevronRight className="w-3.5 h-3.5" />
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
          userRole="admin"
        />
      )}
    </div>
  )
}
