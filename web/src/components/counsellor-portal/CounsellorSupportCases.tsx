import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useCaseDecision, useCases } from '../../lib/api/endpoints/counsellor.hooks'
import { errorMessage } from '../../lib/api/errors'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { ChevronRight, AlertTriangle } from 'lucide-react'

export function CounsellorSupportCases() {
  const cases = useCases()
  const decide = useCaseDecision()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  const act = (e: React.MouseEvent, id: string, version: number, action: 'accept' | 'dismiss') => {
    e.stopPropagation()
    setMsg(null)
    decide.mutate(
      { id, version, action },
      {
        onSuccess: () => setMsg({ ok: true, text: action === 'accept' ? 'Case accepted.' : 'Case dismissed.' }),
        onError: (err) => setMsg({ ok: false, text: errorMessage(err) }),
      },
    )
  }

  return (
    <div className="flex flex-col gap-3 font-sans">
      {msg && (
        <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>
          {msg.text}
        </p>
      )}

      <QueryState query={cases} empty={<EmptyState title="No active cases" message="Students requiring accountable interventions will appear here." />}>
        {(rows) => (
          <div className="rounded-2xl border border-gray-100 bg-white shadow-xs overflow-hidden">
            <ul className="divide-y divide-gray-100 text-xs">
              {rows.map((c) => (
                <li
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className="flex items-center justify-between gap-3 p-3.5 hover:bg-gray-50 transition cursor-pointer"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900">{c.student_name ?? c.student_ref ?? 'Student'}</span>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 uppercase font-semibold">
                        {c.priority}
                      </span>
                      {c.is_overdue && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold flex items-center gap-1 border border-rose-200">
                          <AlertTriangle className="w-3 h-3" /> Overdue
                        </span>
                      )}
                    </div>
                    <span className="text-gray-500 text-[11px]">
                      State: <span className="font-semibold uppercase text-indigo-600">{c.state}</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {c.state === 'suggested' ? (
                      <span className="flex gap-2">
                        <button
                          type="button"
                          disabled={decide.isPending}
                          onClick={(e) => act(e, c.id, c.version, 'accept')}
                          className="rounded-full bg-purple-700 px-3 py-1 font-bold text-white hover:bg-purple-800 disabled:opacity-50 cursor-pointer"
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          disabled={decide.isPending}
                          onClick={(e) => act(e, c.id, c.version, 'dismiss')}
                          className="rounded-full border border-gray-200 px-3 py-1 font-semibold hover:bg-gray-50 disabled:opacity-50 cursor-pointer"
                        >
                          Dismiss
                        </button>
                      </span>
                    ) : (
                      <span className="text-xs text-indigo-600 font-bold flex items-center gap-0.5 hover:underline">
                        Manage <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </QueryState>

      {/* Case Detail Drawer */}
      {selectedCaseId && (
        <CaseDetailDrawer
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
          userRole="counsellor"
        />
      )}
    </div>
  )
}
