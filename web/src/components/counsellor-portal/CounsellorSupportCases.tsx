import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useCaseDecision, useCases } from '../../lib/api/endpoints/counsellor.hooks'
import { errorMessage } from '../../lib/api/errors'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { ChevronRight, AlertTriangle } from 'lucide-react'
import { useT } from '../../i18n'
import { priorityLabel, stageLabel, studentName } from '../../lib/labels'

/** Steps a counsellor may take themselves. Assigning an owner (action_planned -> assigned) is an admin action in the backend. */
const STEP: Record<string, { target: string; label: string; done: string }> = {
  suggested: { target: 'under_review', label: 'Start review', done: 'Review started.' },
  under_review: { target: 'action_planned', label: 'Approve plan', done: 'Plan approved. An admin can now give it to a counsellor.' },
  assigned: { target: 'accepted', label: 'Accept case', done: 'Case accepted.' },
}

export function CounsellorSupportCases() {
  const cases = useCases()
  const t = useT()
  const decide = useCaseDecision()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  const act = (e: React.MouseEvent, id: string, version: number, target: string, doneText: string) => {
    e.stopPropagation()
    setMsg(null)
    decide.mutate(
      { id, version, action: 'advance', target },
      {
        onSuccess: () => setMsg({ ok: true, text: doneText }),
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

      <QueryState query={cases} empty={<EmptyState title="No cases yet" message="When a student needs support, their case will show up here." />}>
        {(rows) => (
          <div className="rounded-2xl border border-line bg-white shadow-xs overflow-hidden">
            <ul className="divide-y divide-line text-xs">
              {rows.map((c) => (
                <li
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className="flex items-center justify-between gap-3 p-3.5 hover:bg-sunken/60 transition cursor-pointer"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-ink">{studentName(c.student_name, c.student_ref)}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-sunken text-ink-2 font-semibold">
                        {priorityLabel(c.priority)}
                      </span>
                      {c.is_overdue && (
                        <span className="text-xs px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-bold flex items-center gap-1 border border-rose-200">
                          <AlertTriangle className="w-3 h-3" /> Overdue
                        </span>
                      )}
                    </div>
                    <span className="text-muted text-xs">
                      <span className="font-semibold text-accent">{stageLabel(c.state)}</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {STEP[c.state] ? (
                      <span className="flex gap-2">
                        <button
                          type="button"
                          disabled={decide.isPending}
                          onClick={(e) => act(e, c.id, c.version, STEP[c.state].target, STEP[c.state].done)}
                          className="rounded-md bg-ink px-3 py-1.5 font-semibold text-white hover:bg-ink-2 disabled:opacity-50 cursor-pointer"
                        >
                          {t(STEP[c.state].label)}
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
