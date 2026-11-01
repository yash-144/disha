import React from 'react'
import { useEarlyWarning } from '../../lib/api/endpoints/admin.hooks'
import { ErrorState, LoadingSkeleton } from '../common/QueryState'
import { InfoTip, pct } from '../common/ui'

/** Range graphic: how many days of warning students got (25th to 75th percentile, median tick). */
function WarningRange({ p25, med, p75 }: { p25: number; med: number; p75: number }) {
  const max = Math.ceil((p75 * 1.15) / 10) * 10
  const x = (v: number) => (v / max) * 100
  return (
    <div>
      <div className="relative h-9">
        <div className="absolute inset-x-0 top-4 h-px bg-white/25" />
        <div className="absolute top-2.5 h-3 bg-white/30" style={{ left: `${x(p25)}%`, width: `${x(p75) - x(p25)}%` }} />
        <div className="absolute top-1 h-6 w-[3px] bg-white" style={{ left: `${x(med)}%` }} />
        <span className="absolute -top-0.5 -translate-x-1/2 text-[11px] font-semibold text-white" style={{ left: `${x(med)}%`, top: '-14px' }}>{Math.round(med)}</span>
      </div>
      <div className="relative mt-1 h-4 text-[10px] text-white/55">
        <span className="absolute -translate-x-1/2" style={{ left: `${x(p25)}%` }}>{Math.round(p25)}</span>
        <span className="absolute -translate-x-1/2" style={{ left: `${x(p75)}%` }}>{Math.round(p75)}</span>
      </div>
      <p className="text-[11px] text-white/55">Days of warning before leaving. Middle half of students shaded; white tick is the median.</p>
    </div>
  )
}

function FlaggedChart({ points }: { points: { day: number; flagged_students: number }[] }) {
  const W = 420
  const H = 150
  const pad = { l: 34, r: 28, t: 10, b: 22 }
  if (points.length < 2) return <p className="text-xs text-white/60">Needs at least two scoring runs.</p>
  const x0 = Math.min(...points.map((p) => p.day))
  const x1 = Math.max(...points.map((p) => p.day))
  const ymax = Math.max(...points.map((p) => p.flagged_students)) * 1.1
  const sx = (d: number) => pad.l + ((d - x0) / Math.max(1, x1 - x0)) * (W - pad.l - pad.r)
  const sy = (v: number) => H - pad.b - (v / ymax) * (H - pad.t - pad.b)
  let d = `M${sx(points[0].day)},${sy(points[0].flagged_students)}`
  for (let i = 1; i < points.length; i++) d += ` H${sx(points[i].day)} V${sy(points[i].flagged_students)}`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Students flagged over the term">
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line x1={pad.l} x2={W - pad.r} y1={sy(ymax * f)} y2={sy(ymax * f)} stroke="#fff" strokeOpacity="0.12" />
          <text x={pad.l - 5} y={sy(ymax * f) + 3} textAnchor="end" fontSize="9" fill="#fff" fillOpacity="0.55">{Math.round(ymax * f)}</text>
        </g>
      ))}
      <path d={`${d} V${H - pad.b} H${sx(points[0].day)} Z`} fill="#fff" fillOpacity="0.1" />
      <path d={d} fill="none" stroke="#fff" strokeWidth="2" />
      {points.map((p) => (
        <g key={p.day}>
          <circle cx={sx(p.day)} cy={sy(p.flagged_students)} r="3.5" fill="#fff"><title>{`Day ${p.day}: ${p.flagged_students} flagged`}</title></circle>
          <text x={sx(p.day)} y={H - 6} textAnchor="middle" fontSize="10" fill="#fff" fillOpacity="0.6">Day {p.day}</text>
        </g>
      ))}
    </svg>
  )
}

export function EarlyWarningHero() {
  const q = useEarlyWarning()
  if (q.isPending) return <LoadingSkeleton rows={1} />
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />
  const { campus: c, benchmark: b } = q.data
  const firstHalf = c.flagged_in_first_half_of_term
  return (
    <section className="overflow-hidden rounded-lg bg-night text-white" aria-label="How early we flag students">
      <div className="grid gap-px bg-white/10 lg:grid-cols-5">
        <div className="bg-night p-6 lg:col-span-2">
          <h2 className="flex items-center gap-1.5 text-[13px] font-semibold text-white/70">
            How early we flag students
            <span className="[&_button]:text-white/50 [&_button:hover]:text-white"><InfoTip text="Benchmark: a held-out test on real student data. This campus: the latest scoring runs." /></span>
          </h2>
          <p className="mt-4 font-display text-[64px] leading-none tracking-tight tabular-nums">{Math.round(b.median_days_warning)} <span className="text-[28px] text-white/70">days</span></p>
          <p className="mt-2 max-w-xs text-[15px] leading-snug text-white/85">median warning before students left their course.</p>
          <p className="mt-5 text-[13px] text-white/70">
            <b className="font-semibold text-white">{pct(b.detection_rate)}</b> of students who later withdrew were flagged first.
          </p>
          <p className="mt-1 text-[11px] text-white/45">Benchmark: held-out test, {b.left_course.toLocaleString()} students who left.</p>
          <div className="mt-6 border-t border-white/15 pt-4">
            <p className="font-display text-[34px] leading-none tabular-nums">{firstHalf != null ? pct(firstHalf) : '—'}</p>
            <p className="mt-1.5 text-[13px] text-white/85">of flagged students were caught in the first half of the term.</p>
            <p className="mt-0.5 text-[11px] text-white/45">This campus{c.median_first_flag_day != null ? `, median first flag on day ${Math.round(c.median_first_flag_day)}` : ''}.</p>
          </div>
        </div>
        <div className="bg-night p-6 lg:col-span-3">
          <p className="text-[13px] font-semibold text-white/70">Students flagged over the term <span className="font-normal text-white/45">· this campus</span></p>
          <div className="mt-3"><FlaggedChart points={c.cumulative_flagged} /></div>
          <p className="mt-1 text-[11px] text-white/55">{c.enrolments_flagged} of {c.enrolments_scored} enrolments flagged so far ({pct(c.enrolments_flagged / Math.max(1, c.enrolments_scored))}).</p>
          <div className="mt-6 border-t border-white/15 pt-4">
            <p className="mb-3 text-[13px] font-semibold text-white/70">Warning time before leaving <span className="font-normal text-white/45">· benchmark</span></p>
            <WarningRange p25={b.p25_days} med={b.median_days_warning} p75={b.p75_days} />
          </div>
        </div>
      </div>
    </section>
  )
}
