import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useCaseDecision, useCases } from '../../lib/api/endpoints/counsellor.hooks'
import { errorMessage } from '../../lib/api/errors'

export function CounsellorSupportCases() {
  const cases = useCases()
  const decide = useCaseDecision()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const act = (id: string, version: number, action: 'accept' | 'dismiss') => {
    setMsg(null)
    decide.mutate(
      { id, version, action },
      {
        onSuccess: () => setMsg({ ok: true, text: action === 'accept' ? 'Case accepted.' : 'Case dismissed.' }),
        onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
      },
    )
  }
  return (
    <div className="flex flex-col gap-3 font-sans">
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</p>}
      <QueryState query={cases} empty={<EmptyState title="No cases" />}>
        {(rows) => (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
            {rows.map((c) => (
              <li key={c.id} className="flex items-center justify-between gap-3 p-3">
                <span>{c.student_name ?? c.student_ref ?? 'Student'}</span>
                <span className="text-[#717E95]">{c.state}, {c.priority}{c.is_overdue ? ', overdue' : ''}</span>
                {c.state === 'suggested' ? (
                  <span className="flex gap-2">
                    <button type="button" disabled={decide.isPending} onClick={() => act(c.id, c.version, 'accept')} className="rounded-full bg-purple-700 px-3 py-1 font-bold text-white disabled:opacity-50">Accept</button>
                    <button type="button" disabled={decide.isPending} onClick={() => act(c.id, c.version, 'dismiss')} className="rounded-full border border-gray-200 px-3 py-1 font-semibold disabled:opacity-50">Dismiss</button>
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </div>
  )
}
