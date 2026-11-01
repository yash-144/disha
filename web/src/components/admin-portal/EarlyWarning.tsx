import React from 'react'
import { useEarlyWarning } from '../../lib/api/endpoints/admin.hooks'
import { ErrorState, LoadingSkeleton } from '../common/QueryState'
import { Card, pct } from '../common/ui'
import { FlaggedLine } from './charts'

/** Warning-time range: where the middle half of students sat (25th to 75th percentile) and the median. */
function WarningRange({ p25, med, p75 }: { p25: number; med: number; p75: number }) {
  const max = Math.ceil((p75 * 1.1) / 20) * 20
  const x = (v: number) => (v / max) * 100
  return (
    <div className="pt-8">
      <div className="relative h-4 rounded-full bg-sunken">
        <div className="absolute inset-y-0 rounded-full bg-accent/25" style={{ left: `${x(p25)}%`, width: `${x(p75) - x(p25)}%` }} />
        <div className="absolute -top-1.5 h-7 w-1 rounded bg-accent" style={{ left: `calc(${x(med)}% - 2px)` }} />
        <span className="absolute -top-8 -translate-x-1/2 whitespace-nowrap text-sm font-bold text-accent" style={{ left: `${x(med)}%` }}>median {Math.round(med)}</span>
      </div>
      <div className="relative mt-2 h-5 text-xs text-ink-2">
        <span className="absolute -translate-x-1/2" style={{ left: `${x(p25)}%` }}>{Math.round(p25)}</span>
        <span className="absolute -translate-x-1/2" style={{ left: `${x(p75)}%` }}>{Math.round(p75)}</span>
        <span className="absolute right-0 text-muted">days</span>
      </div>
      <p className="text-xs text-muted">The shaded band covers the middle half of students who left.</p>
    </div>
  )
}

/** "How early we catch them": benchmark warning time plus this campus's cumulative flagged line. */
export function EarlyWarningHero() {
  const q = useEarlyWarning()
  if (q.isPending) return <LoadingSkeleton rows={2} />
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />
  const { campus: c, benchmark: b } = q.data
  const half = c.flagged_in_first_half_of_term
  return (
    <section aria-label="How early we catch students" className="grid gap-4 lg:grid-cols-5">
      <Card className="lg:col-span-2" title="Warning before students leave" tip="Benchmark from a held-out test on real student data, not this campus.">
        <p className="font-display text-[56px] leading-none text-accent">{Math.round(b.median_days_warning)} <span className="text-2xl text-ink-2">days</span></p>
        <p className="mt-2 text-base font-semibold text-ink">median warning before a student left the course.</p>
        <p className="mt-1 text-sm text-ink-2"><b>{pct(b.detection_rate)}</b> of students who later withdrew were flagged first ({b.flagged_before_leaving.toLocaleString()} of {b.left_course.toLocaleString()}).</p>
        <WarningRange p25={b.p25_days} med={b.median_days_warning} p75={b.p75_days} />
        <p className="mt-3 border-t border-line pt-3 text-xs text-muted">Benchmark: held-out test data.</p>
      </Card>
      <Card className="lg:col-span-3" title="Students flagged as the term goes on" tip="Cumulative student-courses flagged High or Medium at each weekly scoring run on this campus.">
        <p className="text-base font-semibold text-ink">
          {half != null ? `${pct(half)} of flagged students were caught in the first half of the term.` : 'Flags build up as the term goes on.'}
        </p>
        <FlaggedLine points={c.cumulative_flagged} />
        <p className="text-sm text-ink-2">{c.enrolments_flagged} of {c.enrolments_scored} student-courses flagged so far{c.median_first_flag_day != null ? `. Typical first flag: day ${Math.round(c.median_first_flag_day)}.` : '.'} <span className="text-muted">This campus.</span></p>
      </Card>
    </section>
  )
}
