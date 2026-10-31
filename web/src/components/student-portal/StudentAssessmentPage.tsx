import React, { useState } from 'react'
import { ErrorState, LoadingSkeleton, EmptyState } from '../common/QueryState'
import { usePulseCurrent, useSubmitPulse } from '../../lib/api/endpoints/student.hooks'
import { ApiError, errorMessage } from '../../lib/api/errors'

export function StudentAssessmentPage() {
  const current = usePulseCurrent()
  const submit = useSubmitPulse()
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [reflection, setReflection] = useState('')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  if (current.isPending) return <LoadingSkeleton />
  if (current.isError) {
    if (current.error instanceof ApiError && (current.error.status === 404 || current.error.status === 409))
      return <EmptyState title="No wellbeing check-in is open" message="Your campus has no active pulse period right now." />
    return <ErrorState error={current.error} onRetry={() => void current.refetch()} />
  }
  const { period, questionnaire, already_submitted } = current.data
  if (already_submitted) return <EmptyState title="Check-in complete" message={`You have already submitted ${period.label}. Thank you.`} />

  const questions = questionnaire.questions as { key: string; text?: string; prompt?: string }[]
  const complete = questions.every((q) => answers[q.key] != null)
  const send = () => {
    setMsg(null)
    submit.mutate({ responses: answers, reflection }, {
      onSuccess: () => setMsg({ ok: true, text: 'Check-in submitted. Thank you.' }),
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  return (
    <div className="mt-3 flex flex-col gap-4 font-sans">
      <h2 className="text-sm font-bold">{period.label}</h2>
      {questions.map((q) => (
        <fieldset key={q.key} className="rounded-2xl border border-gray-100 bg-white p-4 text-xs">
          <legend className="font-semibold">{q.text ?? q.prompt ?? q.key}</legend>
          <div className="mt-2 flex gap-3">
            {[1, 2, 3, 4, 5].map((n) => (
              <label key={n} className="flex items-center gap-1">
                <input type="radio" name={q.key} checked={answers[q.key] === n} onChange={() => setAnswers((a) => ({ ...a, [q.key]: n }))} />
                {n}
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <textarea value={reflection} onChange={(e) => setReflection(e.target.value)} placeholder="Optional reflection" className="rounded-2xl border border-gray-200 p-3 text-xs" />
      <button type="button" disabled={!complete || submit.isPending} onClick={send} className="self-start rounded-full bg-purple-700 px-5 py-2 text-xs font-bold text-white disabled:opacity-50">
        {submit.isPending ? 'Submitting...' : 'Submit check-in'}
      </button>
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</p>}
    </div>
  )
}
