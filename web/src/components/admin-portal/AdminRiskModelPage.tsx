import React, { useMemo, useState } from 'react'
import { AlertTriangle, CalendarClock, CheckCircle2, Cpu, Play, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { QueryState, EmptyState, ErrorState, LoadingSkeleton } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useSession } from '../../lib/auth/SessionProvider'
import { useCohorts, useDrift, useModelInfo, useRuns, useTriggerRun } from '../../lib/api/endpoints/admin.hooks'
import { buildPeopleIndex, displayName, useAllCases, useAllScores, type DriftFeature, type ScoreRow } from '../../lib/api/endpoints/risk'
import { Button, Card, KpiStrip, ColorLegend, DetailsDisclosure, Direction, InfoTip, Kpi, LineChart, TierBadge, TierTrend, TIERS, TIER_STYLE, fmtDateTime, pct, pretty, type Tier } from '../common/ui'
import { EarlyWarningHero } from './EarlyWarning'
import { StudentInsightDrawer } from './StudentInsightDrawer'

const RANK: Record<string, number> = { ON_TRACK: 0, WATCH: 1, MEDIUM: 2, HIGH: 3 }

function Fact({ icon: Icon, title, text }: { icon: React.ComponentType<{ className?: string }>; title: string; text: string }) {
  return (
    <div className="flex gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><Icon className="h-4.5 w-4.5" /></span>
      <div>
        <p className="text-xs font-bold text-ink">{title}</p>
        <p className="text-[11px] leading-snug text-muted">{text}</p>
      </div>
    </div>
  )
}

function ModelHeader() {
  const info = useModelInfo()
  const runs = useRuns()
  const latest = runs.data?.items?.[0]
  return (
    <Card>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white"><Cpu className="h-6 w-6" /></span>
          <div>
            <h2 className="text-lg font-bold text-ink">DISHA Risk Model</h2>
            <p className="text-xs text-muted">
              {latest ? `Last scored ${fmtDateTime(latest.finished_at ?? latest.started_at)} · day ${latest.as_of_day} of term` : 'Not scored yet'}
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-3 lg:max-w-3xl">
          <Fact icon={Sparkles} title="What it predicts" text="The chance a student fails or withdraws from a course." />
          <Fact icon={CalendarClock} title="How often" text="Re-scored weekly as the term progresses." />
          <Fact icon={ShieldCheck} title="Why a student is flagged" text="Every flag comes with plain-language reasons." />
        </div>
      </div>
      <div className="mt-4">
        <QueryState query={info}>
          {(m) => (
            <DetailsDisclosure summary="Model details (technical)">
              <p>Version: {m.model_version}</p>
              <p>Bundle: {m.bundle_sha256}</p>
              <p>Trained on: {m.dataset} · terms {m.trained_terms.join(', ')}</p>
              <p>Inputs ({m.features.length}): {m.features.join(', ')}</p>
              <p>Tier cut-offs: high {m.cutoffs.high?.toFixed(3)}, medium {m.cutoffs.medium?.toFixed(3)}, watch {m.cutoffs.watch?.toFixed(3)} · alert capacity {pct(m.capacity_share)}</p>
            </DetailsDisclosure>
          )}
        </QueryState>
      </div>
    </Card>
  )
}

function Reliability() {
  const info = useModelInfo()
  return (
    <QueryState query={info}>
      {(m) => {
        const h = m.headline_metrics as Record<string, any>
        const prec = (h.alert_precision_at_cutoff ?? {}) as Record<string, number>
        return (
          <div className="grid gap-4 lg:grid-cols-5">
            <KpiStrip cols="lg:grid-cols-2" className="lg:col-span-2 self-start">
              <Kpi label="Ranking quality" value={h.roc_auc != null ? h.roc_auc.toFixed(2) : '—'} hint="ROC-AUC" tip="How well the model puts struggling students above others. 0.5 is a coin flip, 1.0 is perfect." />
              <Kpi label="Precision / recall" value={h.pr_auc != null ? h.pr_auc.toFixed(2) : '—'} hint="PR-AUC" tip="Balance between catching at-risk students and avoiding false alarms. Higher is better." />
              <Kpi label="Calibration error" value={h.ece != null ? h.ece.toFixed(3) : '—'} hint="ECE · lower is better" tip="When the model says 70%, about how far off is that from reality. Near 0 means the percentages can be trusted." />
              <Kpi label="Brier score" value={h.brier != null ? h.brier.toFixed(3) : '—'} hint="lower is better" tip="Average squared error of the predicted chances. 0 is perfect." />
            </KpiStrip>
            <Card className="lg:col-span-3" title="How reliable are the alerts?" tip="Alert precision: of the students flagged at this level, the share who really ended up failing or withdrawing. It is not overall accuracy.">
              <ul className="space-y-3">
                {(['high', 'medium', 'watch'] as const).map((k) => {
                  const t = k.toUpperCase() as Tier
                  const v = prec[k]
                  return (
                    <li key={k} className="text-xs">
                      <div className="mb-1 flex items-center justify-between">
                        <span className="flex items-center gap-2 font-semibold text-ink"><TierBadge tier={t} /> alerts</span>
                        <span className="font-bold tabular-nums">{pct(v)}</span>
                      </div>
                      <div className="h-2.5 rounded-full bg-gray-100"><div className="h-2.5 rounded-full" style={{ width: `${(v ?? 0) * 100}%`, background: TIER_STYLE[t].color }} /></div>
                      <p className="mt-0.5 text-[11px] text-muted">About {Math.round((v ?? 0) * 100)} of every 100 {TIER_STYLE[t].label.toLowerCase()} alerts were students who really struggled.</p>
                    </li>
                  )
                })}
              </ul>
              <p className="mt-3 flex items-start gap-1.5 text-[11px] text-muted"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" /> Percentages are calibrated: a 70% risk really means roughly 7 in 10 similar students struggled. Measured on past terms, not this campus.</p>
            </Card>
          </div>
        )
      }}
    </QueryState>
  )
}

function RunScoring() {
  const { role } = useSession()
  const runs = useRuns()
  const trigger = useTriggerRun()
  const [day, setDay] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [last, setLast] = useState<any>(null)
  const canRun = role === 'institution_admin' || role === 'platform_admin'
  const days = Array.from(new Set((runs.data?.items ?? []).map((r) => r.as_of_day))).sort((a, b) => a - b)

  const run = () => {
    setError(null)
    setLast(null)
    trigger.mutate({ as_of_day: day ? Number(day) : null, term_id: null }, { onSuccess: setLast, onError: (e) => setError(errorMessage(e)) })
  }
  return (
    <Card title="Run scoring" tip="Scores every enrolment with the latest imported data and creates case suggestions according to the active policy.">
      {!canRun ? (
        <p className="text-xs text-muted">Only institution admins can run scoring.</p>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end gap-3 text-xs">
            <label className="flex flex-col gap-1 font-semibold text-ink-2">
              Score as of day
              <input value={day} onChange={(e) => setDay(e.target.value.replace(/\D/g, '').slice(0, 3))} placeholder="Latest" inputMode="numeric" className="w-28 rounded-lg border border-line px-3 py-2 font-normal outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100" />
            </label>
            {days.length > 0 && (
              <div className="flex items-center gap-1.5">
                {days.map((d) => (
                  <button key={d} type="button" onClick={() => setDay(String(d))} className="rounded-full border border-line bg-white px-3 py-1.5 font-semibold text-ink-2 hover:bg-gray-50">Day {d}</button>
                ))}
              </div>
            )}
            <Button onClick={run} disabled={trigger.isPending}>{trigger.isPending ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Scoring…</> : <><Play className="h-3.5 w-3.5" /> Run scoring</>}</Button>
          </div>
          {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
          {last && (
            <div role="status" className="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-900">
              <p className="font-bold">Done: {last.n_scored} enrolments scored for day {last.as_of_day}.</p>
              <p className="mt-1">{TIERS.map((t) => `${TIER_STYLE[t].label} ${last.tier_counts?.[t] ?? 0}`).join(' · ')}</p>
              {last.policy ? <p className="mt-1">Case suggestions created under the active policy.</p> : <p className="mt-1">No active policy, so no case suggestions were created.</p>}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

function Movement({ rows, name, onOpen }: { rows: ScoreRow[]; name: (r: ScoreRow) => string; onOpen: (r: ScoreRow) => void }) {
  const moved = rows.filter((r) => r.previous_tier && r.previous_tier !== r.tier)
  const worse = moved.filter((r) => RANK[r.tier] > RANK[r.previous_tier!]).sort((a, b) => b.probability - a.probability)
  const better = moved.filter((r) => RANK[r.tier] < RANK[r.previous_tier!]).sort((a, b) => b.probability - a.probability)
  const matrix: Record<string, Record<string, number>> = {}
  for (const r of rows) if (r.previous_tier) { (matrix[r.previous_tier] ??= {})[r.tier] = ((matrix[r.previous_tier] ?? {})[r.tier] ?? 0) + 1 }
  const List = ({ items, tone }: { items: ScoreRow[]; tone: string }) => (
    <ul className="space-y-1.5">
      {items.slice(0, 5).map((r) => (
        <li key={r.id}>
          <button type="button" onClick={() => onOpen(r)} className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left text-xs hover:bg-gray-50">
            <span className="truncate font-semibold text-ink">{name(r)} <span className="font-normal text-muted">· {r.course_id}</span></span>
            <span className={`flex shrink-0 items-center gap-1 text-[11px] font-semibold ${tone}`}>{TIER_STYLE[r.previous_tier as Tier].label} → {TIER_STYLE[r.tier].label}</span>
          </button>
        </li>
      ))}
      {items.length === 0 && <li className="px-2 text-xs text-muted">None this week.</li>}
    </ul>
  )
  return (
    <Card title="Tier movement since the previous run" tip="How many enrolments moved to a higher or lower risk tier between the last two scoring runs.">
      <div className="mb-3 flex gap-3 text-xs">
        <span className="flex items-center gap-1 rounded-full bg-rose-50 px-3 py-1 font-bold text-rose-700"><Direction d="up" /> {worse.length} got worse</span>
        <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 font-bold text-emerald-700"><Direction d="down" /> {better.length} improved</span>
        <span className="rounded-full bg-gray-100 px-3 py-1 font-bold text-gray-600">{rows.length - moved.length} unchanged</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div><p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted">Rising risk</p><List items={worse} tone="text-rose-600" /></div>
        <div><p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted">Recovering</p><List items={better} tone="text-emerald-600" /></div>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-center text-[11px]">
          <caption className="pb-1 text-left text-[10px] font-bold uppercase tracking-wider text-muted">From (rows) to (columns)</caption>
          <thead><tr><th />{TIERS.map((t) => <th key={t} className="p-1 font-semibold">{TIER_STYLE[t].label}</th>)}</tr></thead>
          <tbody>
            {TIERS.map((from) => (
              <tr key={from}>
                <th className="p-1 text-left font-semibold">{TIER_STYLE[from].label}</th>
                {TIERS.map((to) => {
                  const n = matrix[from]?.[to] ?? 0
                  return <td key={to} className={`p-1 tabular-nums ${from === to ? 'bg-gray-50 font-semibold' : n ? 'font-bold' : 'text-gray-300'}`} style={n && from !== to ? { background: `${TIER_STYLE[RANK[to] > RANK[from] ? to : to].color}22` } : undefined}>{n}</td>
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

function Hotspots() {
  const q = useCohorts()
  const [sel, setSel] = useState<string | null>(null)
  return (
    <Card title="Course hotspots" tip="Courses ranked by the share of students at High or Medium risk. Select a course to see when students started to be flagged.">
      <QueryState query={q} isEmpty={(d) => !d.cohorts?.length} empty={<EmptyState title="No course data" />}>
        {(d) => {
          const sorted = [...d.cohorts].sort((a, b) => b.at_risk_share - a.at_risk_share)
          const cur = sorted.find((c) => c.course_id === sel) ?? sorted[0]
          return (
            <div className="grid gap-5 lg:grid-cols-2">
              <ul className="space-y-1">
                {sorted.slice(0, 10).map((c) => (
                  <li key={c.course_id}>
                    <button type="button" onClick={() => setSel(c.course_id)} aria-pressed={cur.course_id === c.course_id} className={`flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-xs ${cur.course_id === c.course_id ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
                      <span className="w-14 shrink-0 text-left font-semibold">{c.course_id}</span>
                      <div className="h-2.5 flex-1 rounded-full bg-gray-100"><div className="h-2.5 rounded-full bg-rose-400" style={{ width: `${Math.min(100, c.at_risk_share * 100)}%` }} /></div>
                      <span className="w-20 text-right tabular-nums text-ink-2">{pct(c.at_risk_share)} of {c.n_active}</span>
                    </button>
                  </li>
                ))}
              </ul>
              <div>
                <p className="flex items-center gap-1 text-xs font-bold text-ink">{cur.course_id}: flagged students over the term <InfoTip text="Cumulative share of students who have been flagged High or Medium at any weekly check up to that day." /></p>
                <LineChart points={(cur.time_to_risk ?? []).map((p) => ({ x: p.day, y: p.cumulative_signalled_share }))} color="#F43F5E" />
                {cur.hotspot && (
                  <p className="mt-2 rounded-xl bg-amber-50 p-2.5 text-[11px] text-amber-900">
                    Biggest trigger: <b>{cur.hotspot.label}</b> (day {cur.hotspot.due_day}){cur.hotspot.share_of_at_risk != null ? `, where ${pct(cur.hotspot.share_of_at_risk)} of at-risk students first slipped` : ''}.
                  </p>
                )}
              </div>
            </div>
          )
        }}
      </QueryState>
    </Card>
  )
}

function Drift() {
  const q = useDrift()
  return (
    <Card title="Has the data changed since training?" tip="PSI compares this campus's data with the data the model learned from. Above 0.2 means the inputs look quite different, so scores deserve extra care.">
      <QueryState query={q} empty={<EmptyState title="No drift report" message="Run scoring first." />} isEmpty={(d) => !d.data_drift}>
        {(d) => {
          const dd = d.data_drift as { features?: DriftFeature[]; retrain_recommended?: boolean; max_psi?: number; current_rows?: number; reference_rows?: number }
          const feats = dd.features ?? []
          const shifted = feats.filter((f) => f.status === 'shift').length
          const maxP = Math.max(0.3, ...feats.map((f) => Math.min(f.psi, 1)))
          return (
            <>
              <div className={`mb-3 flex items-start gap-2 rounded-xl p-3 text-xs ${dd.retrain_recommended ? 'bg-amber-50 text-amber-900' : 'bg-emerald-50 text-emerald-900'}`}>
                {dd.retrain_recommended ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
                <p>{dd.retrain_recommended ? `${shifted} of ${feats.length} inputs look different from training data. Treat scores as a guide and plan a retrain.` : 'Inputs look consistent with training data.'}</p>
              </div>
              <ul className="grid gap-x-8 gap-y-1.5 md:grid-cols-2">
                {feats.slice(0, 12).map((f) => (
                  <li key={f.feature} className="flex items-center gap-3 text-xs">
                    <span className="w-36 shrink-0 truncate text-ink-2" title={f.feature}>{pretty(f.feature)}</span>
                    <div className="h-2 flex-1 rounded-full bg-gray-100"><div className={`h-2 rounded-full ${f.status === 'shift' ? 'bg-rose-400' : f.status === 'watch' ? 'bg-amber-400' : 'bg-emerald-500'}`} style={{ width: `${Math.max(2, (Math.min(f.psi, 1) / maxP) * 100)}%` }} /></div>
                    <span className="w-10 text-right tabular-nums text-[11px] text-muted">{f.psi.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[11px] text-muted">Showing the 12 biggest differences. Red above 0.2, amber 0.1 to 0.2.</p>
            </>
          )
        }}
      </QueryState>
    </Card>
  )
}

export function AdminRiskModelPage() {
  const runs = useRuns()
  const scores = useAllScores()
  const cases = useAllCases()
  const people = useMemo(() => buildPeopleIndex(cases.data), [cases.data])
  const [open, setOpen] = useState<{ key: string; name: string } | null>(null)
  const trend = useMemo(() => [...(runs.data?.items ?? [])].reverse().map((r) => ({ label: `Day ${r.as_of_day}`, counts: r.tier_counts as Record<string, number> })), [runs.data])
  const name = (r: ScoreRow) => displayName(people, r)
  const openRow = (r: ScoreRow) => setOpen({ key: r.student_id ?? r.external_student_ref_hash ?? r.student_ref, name: name(r) })

  return (
    <div className="flex flex-col gap-4 font-sans">
      <ModelHeader />
      <EarlyWarningHero />
      <Reliability />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Risk across scoring runs" tip="Each column is one weekly scoring run. Watch the red and orange shrink as support works.">
          {runs.isPending ? <LoadingSkeleton rows={2} /> : runs.isError ? <ErrorState error={runs.error} onRetry={() => void runs.refetch()} /> : trend.length < 2 ? <p className="text-xs text-muted">Needs at least two runs.</p> : (<><TierTrend points={trend} /><div className="mt-2"><ColorLegend /></div></>)}
        </Card>
        <RunScoring />
      </div>
      <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="No scores yet" message="Run scoring to see tier movement." />}>
        {(d) => <Movement rows={d.items} name={name} onOpen={openRow} />}
      </QueryState>
      <Hotspots />
      <Drift />
      <StudentInsightDrawer studentKey={open?.key ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}
