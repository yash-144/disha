import React from 'react'
import { Card } from '../common/ui'
import { useAnalyticsOverview, useEarlyWarning } from '../../lib/api/endpoints/admin.hooks'
import { ErrorState, LoadingSkeleton } from '../common/QueryState'

const PROVEN = 'Tested on a past term the system had never seen'

function Proof({ kicker, tag, tone, value, unit, sentence, sub }: {
  kicker: string
  tag: string
  tone: string
  value: string
  unit?: string
  sentence: string
  sub?: string
}) {
  return (
    <section className="flex flex-col rounded-lg border border-line bg-panel p-5">
      <p className="text-sm font-semibold text-ink-2">{kicker}</p>
      <p className={`mt-2 font-display text-[52px] leading-none ${tone}`}>
        {value}
        {unit && <span className="ml-1.5 text-xl text-ink-2">{unit}</span>}
      </p>
      <p className="mt-3 text-base font-semibold leading-snug text-ink">{sentence}</p>
      {sub && <p className="mt-1 text-sm text-ink-2">{sub}</p>}
      <p className="mt-auto pt-4 text-xs text-muted">{tag}</p>
    </section>
  )
}

const tenOf = (v: number | null | undefined) => (v == null ? null : Math.round(v * 10))

/** Four plain-language proof points: three proven on a held-out term, one measured on this campus. */
export function ProofCards() {
  const ew = useEarlyWarning()
  const an = useAnalyticsOverview()
  if (ew.isPending) return <LoadingSkeleton rows={2} />
  if (ew.isError) return <ErrorState error={ew.error} onRetry={() => void ew.refetch()} />
  const b = ew.data.benchmark
  const caught = tenOf(b.struggling_students_caught)
  const right = tenOf(b.flagged_who_really_struggled)

  const iv = ((an.data ?? {}) as { interventions?: { outcomes_recorded?: number | null; by_completion_status?: { label: string; count: number | null }[] } }).interventions
  const total = iv?.outcomes_recorded ?? null
  const improved = iv?.by_completion_status?.find((x) => x.label === 'improved')?.count ?? null
  const hasOutcomes = total != null && total > 0 && improved != null

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="What DISHA delivers">
      <Proof
        kicker="Early warning" tag={PROVEN} tone="text-accent"
        value={String(Math.round(b.median_days_warning))} unit="days"
        sentence={`We flag students a median of ${Math.round(b.median_days_warning)} days before they leave.`}
        sub={`Typically ${Math.round(b.p25_days)} to ${Math.round(b.p75_days)} days.`}
      />
      <Proof
        kicker="We catch them" tag={PROVEN} tone="text-accent"
        value={caught == null ? '—' : String(caught)} unit="of 10"
        sentence={caught == null ? 'Not available yet.' : `We spot ${caught} of every 10 students who go on to struggle.`}
      />
      <Proof
        kicker="Flags are right" tag={PROVEN} tone="text-accent"
        value={right == null ? '—' : String(right)} unit="of 10"
        sentence={right == null ? 'Not available yet.' : `${right} of every 10 flagged students really needed help.`}
      />
      <Proof
        kicker="Support works" tag="This campus" tone="text-tier-ok"
        value={hasOutcomes ? `${Math.round((improved! / total!) * 100)}%` : '—'}
        sentence={hasOutcomes ? `${Math.round((improved! / total!) * 100)}% of recorded support outcomes showed improvement.` : 'No outcomes yet.'}
        sub={hasOutcomes ? `${improved} of ${total} outcomes recorded.` : 'Shown once counsellors record how support went.'}
      />
    </div>
  )
}
