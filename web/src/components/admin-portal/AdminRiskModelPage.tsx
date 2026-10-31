import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useDrift, useModelInfo, useRuns, useTriggerRun } from '../../lib/api/endpoints/admin.hooks'
import type { ScoringRun } from '../../lib/api/endpoints/admin'

function PolicySummary({ policy }: { policy: ScoringRun['policy'] }) {
  if (!policy) return <p className="text-xs text-[#717E95]">No active policy: this run did not create case suggestions.</p>
  return (
    <pre className="max-h-48 overflow-auto rounded-xl bg-gray-50 p-3 text-[11px]">{JSON.stringify(policy, null, 2)}</pre>
  )
}

export function AdminRiskModelPage() {
  const info = useModelInfo()
  const runs = useRuns()
  const drift = useDrift()
  const trigger = useTriggerRun()
  const [day, setDay] = useState('')
  const [term, setTerm] = useState('')
  const [last, setLast] = useState<ScoringRun | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = () => {
    setError(null)
    trigger.mutate(
      { as_of_day: day ? Number(day) : null, term_id: term || null },
      { onSuccess: setLast, onError: (e) => setError(errorMessage(e)) },
    )
  }

  return (
    <div className="flex flex-col gap-4 font-sans">
      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Loaded model</h2>
        <div className="mt-3">
          <QueryState query={info}>
            {(m) => (
              <div className="text-xs text-[#4A5568] space-y-1">
                <p>{m.model} {m.model_version} (bundle sha {m.bundle_sha256.slice(0, 12)})</p>
                <p>Trained terms: {m.trained_terms.join(', ') || 'n/a'}</p>
                <p>Cutoffs: {Object.entries(m.cutoffs).map(([k, v]) => `${k} ${v ?? 'n/a'}`).join(', ')}</p>
                <p>Headline metrics (alert precision and related, from training):</p>
                <pre className="rounded-xl bg-gray-50 p-3 text-[11px]">{JSON.stringify(m.headline_metrics, null, 2)}</pre>
                {m.notes.map((n, i) => <p key={i}>{n}</p>)}
              </div>
            )}
          </QueryState>
        </div>
      </section>

      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Run scoring</h2>
        <div className="mt-3 flex flex-wrap items-end gap-3 text-xs">
          <label className="flex flex-col gap-1">As-of day
            <input value={day} onChange={(e) => setDay(e.target.value.replace(/\D/g, ''))} className="rounded-lg border border-gray-200 px-2 py-1" />
          </label>
          <label className="flex flex-col gap-1">Term id (optional)
            <input value={term} onChange={(e) => setTerm(e.target.value)} className="rounded-lg border border-gray-200 px-2 py-1" />
          </label>
          <button type="button" onClick={run} disabled={trigger.isPending} className="rounded-full bg-purple-700 px-4 py-2 font-bold text-white disabled:opacity-50">
            {trigger.isPending ? 'Scoring...' : 'Run scoring'}
          </button>
        </div>
        {error && <p role="alert" className="mt-3 text-xs text-red-600">{error}</p>}
        {last && (
          <div className="mt-3 text-xs">
            <p className="font-bold">Run {last.status}: {last.n_scored} scored. Tiers: {Object.entries(last.tier_counts).map(([k, v]) => `${k} ${v}`).join(', ')}</p>
            <PolicySummary policy={last.policy} />
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Recent runs</h2>
        <div className="mt-3">
          <QueryState query={runs} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="No scoring runs yet" />}>
            {(page) => (
              <ul className="space-y-2 text-xs">
                {page.items.map((r) => (
                  <li key={r.id} className="rounded-xl border border-gray-100 p-3">
                    {new Date(r.started_at).toLocaleString()}: {r.status}, day {r.as_of_day}, {r.n_scored} scored, model {r.model_version}
                    {r.error ? <span className="text-red-600"> ({r.error})</span> : null}
                    <PolicySummary policy={r.policy} />
                  </li>
                ))}
              </ul>
            )}
          </QueryState>
        </div>
      </section>

      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Data drift (PSI)</h2>
        <div className="mt-3">
          <QueryState query={drift} empty={<EmptyState title="No drift report" message="Run scoring first." />}>
            {(d) => <pre className="max-h-64 overflow-auto rounded-xl bg-gray-50 p-3 text-[11px]">{JSON.stringify(d.data_drift, null, 2)}</pre>}
          </QueryState>
        </div>
      </section>
    </div>
  )
}
