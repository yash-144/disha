import React, { useMemo, useState } from 'react'
import { AlertTriangle, CalendarClock, CheckCircle2, Cpu, Play, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { QueryState, EmptyState, ErrorState, LoadingSkeleton } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useSession } from '../../lib/auth/SessionProvider'
import { useCohorts, useDrift, useModelInfo, useRuns, useTriggerRun } from '../../lib/api/endpoints/admin.hooks'
import { buildPeopleIndex, displayName, useAllCases, useAllScores, type DriftFeature, type ScoreRow } from '../../lib/api/endpoints/risk'
import { Button, Card, ColorLegend, DetailsDisclosure, Direction, InfoTip, LineChart, TierBadge, TIERS, TIER_STYLE, fmtDateTime, pct, pretty, type Tier } from '../common/ui'
import { friendlyDateTime, courseName, termWeek, tierLabel } from '../../lib/labels'
import { EarlyWarningHero } from './EarlyWarning'
import { ProofCards } from './ProofCards'
import { TierRunsChart } from './charts'
import { StudentInsightDrawer } from './StudentInsightDrawer'

const RANK: Record<string, number> = { ON_TRACK: 0, WATCH: 1, MEDIUM: 2, HIGH: 3 }

function Fact({ icon: Icon, title, text }: { icon: React.ComponentType<{ className?: string }>; title: string; text: string }) {
  return (
    <div className="flex gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><Icon className="h-4.5 w-4.5" /></span>
      <div>
        <p className="text-xs font-bold text-ink">{title}</p>
        <p className="text-xs leading-snug text-muted">{text}</p>
      </div>
    </div>
  )
}

function ModelHeader() {
  const runs = useRuns()
  const latest = runs.data?.items?.[0]
  return (
    <Card>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white"><Cpu className="h-6 w-6" /></span>
          <div>
            <h2 className="text-lg font-bold text-ink">Early-warning check</h2>
            <p className="text-xs text-muted">
              {latest ? `Last checked ${friendlyDateTime(latest.finished_at ?? latest.started_at)} · ${termWeek(latest.as_of_day)}` : 'Not checked yet'}
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-3 lg:max-w-3xl">
          <Fact icon={Sparkles} title="What it predicts" text="The chance a student fails or withdraws from a course." />
          <Fact icon={CalendarClock} title="How often" text="Every student is checked again each week." />
          <Fact icon={ShieldCheck} title="Why a student is flagged" text="Every flag comes with plain-language reasons." />
        </div>
      </div>
    </Card>
  )
}

function Metric({ label, value, caption }: { label: string; value: string; caption: string }) {
  return (
    <div className="bg-panel p-4">
      <p className="font-display text-3xl leading-none tabular-nums">{value}</p>
      <p className="mt-2 text-sm font-semibold text-ink">{label}</p>
      <p className="text-xs text-muted">{caption}</p>
    </div>
  )
}

function ModelDetails() {
  const info = useModelInfo()
  return (
    <details className="group rounded-lg border border-line bg-panel">
      <summary className="cursor-pointer select-none px-5 py-4 text-sm font-bold text-ink">Model details <span className="font-normal text-muted">for data teams and auditors</span></summary>
      <div className="flex flex-col gap-4 border-t border-line p-5">
        <QueryState query={info}>
          {(m) => {
            const h = m.headline_metrics as Record<string, any>
            const prec = (h.alert_precision_at_cutoff ?? {}) as Record<string, number>
            const f = (v: unknown, d: number) => (typeof v === 'number' ? v.toFixed(d) : '—')
            return (
              <>
                <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line lg:grid-cols-4">
                  <Metric label="Ranking quality (ROC-AUC)" value={f(h.roc_auc, 2)} caption="Struggling students are ranked above others. 0.5 is a coin flip." />
                  <Metric label="Catch vs false alarms (PR-AUC)" value={f(h.pr_auc, 2)} caption="Higher means fewer missed students and fewer false alarms." />
                  <Metric label="Calibration error (ECE)" value={f(h.ece, 3)} caption="Calibrated: when we say 80%, about 80% struggle. Lower is better." />
                  <Metric label="Brier score" value={f(h.brier, 3)} caption="Average error of the predicted chances. Lower is better." />
                </div>
                <Card title="How right are the flags at each level?" tip="Of the students flagged at this level, the share who really struggled.">
                  <ul className="space-y-3">
                    {(['high', 'medium', 'watch'] as const).map((k) => {
                      const t = k.toUpperCase() as Tier
                      const v = prec[k]
                      return (
                        <li key={k} className="text-sm">
                          <div className="mb-1 flex items-center justify-between">
                            <span className="flex items-center gap-2 font-semibold text-ink"><TierBadge tier={t} /> flags</span>
                            <span className="font-bold tabular-nums">{pct(v)}</span>
                          </div>
                          <div className="h-2.5 rounded-full bg-sunken"><div className="h-2.5 rounded-full" style={{ width: `${(v ?? 0) * 100}%`, background: TIER_STYLE[t].color }} /></div>
                          <p className="mt-0.5 text-xs text-muted">About {Math.round((v ?? 0) * 100)} of every 100 students marked “{tierLabel(t)}” really struggled.</p>
                        </li>
                      )
                    })}
                  </ul>
                  <p className="mt-3 flex items-start gap-1.5 text-xs text-muted"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-tier-ok" /> Tested on a past term the system had never seen, not on this campus.</p>
                </Card>
                <DetailsDisclosure summary="Version and inputs">
                  <p>Model version: {m.model_version}</p>
                  <p>Fingerprint: {m.bundle_sha256}</p>
                  <p>Inputs ({m.features.length}): {m.features.join(', ')}</p>
                  <p>Cut-offs: needs help now {m.cutoffs.high?.toFixed(3)}, closer look {m.cutoffs.medium?.toFixed(3)}, keep an eye on {m.cutoffs.watch?.toFixed(3)} · alert capacity {pct(m.capacity_share)}</p>
                </DetailsDisclosure>
              </>
            )
          }}
        </QueryState>
        <Drift />
      </div>
    </details>
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
    <Card title="Run the weekly check" tip="Checks every student with the latest imported data and suggests cases for those who need help.">
      {!canRun ? (
        <p className="text-xs text-muted">Only campus admins can run the weekly check.</p>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end gap-3 text-xs">
            <label className="flex flex-col gap-1 font-semibold text-ink-2">
              Day of term (optional)
              <input value={day} onChange={(e) => setDay(e.target.value.replace(/\D/g, '').slice(0, 3))} placeholder="Latest" inputMode="numeric" className="w-28 rounded-lg border border-line px-3 py-2 font-normal outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100" />
            </label>
            {days.length > 0 && (
              <div className="flex items-center gap-1.5">
                {days.map((d) => (
                  <button key={d} type="button" onClick={() => setDay(String(d))} className="rounded-full border border-line bg-white px-3 py-1.5 font-semibold text-ink-2 hover:bg-gray-50">{termWeek(d).replace(' of 17', '')}</button>
                ))}
              </div>
            )}
            <Button onClick={run} disabled={trigger.isPending}>{trigger.isPending ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Checking…</> : <><Play className="h-3.5 w-3.5" /> Run weekly check</>}</Button>
          </div>
          {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
          {last && (
            <div role="status" className="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-900">
              <p className="font-bold">Done: checked {last.n_scored} student-courses ({termWeek(last.as_of_day)}).</p>
              <p className="mt-1">{TIERS.map((t) => `${tierLabel(t)}: ${last.tier_counts?.[t] ?? 0}`).join(' · ')}</p>
              {last.policy ? <p className="mt-1">New cases were suggested for students who need help.</p> : <p className="mt-1">No case rules are switched on yet, so no cases were suggested.</p>}
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
            <span className="truncate font-semibold text-ink">{name(r)} <span className="font-normal text-muted">· {courseName(r.course_id)}</span></span>
            <span className={`flex shrink-0 items-center gap-1 text-xs font-semibold ${tone}`}>{tierLabel(r.previous_tier)} → {tierLabel(r.tier)}</span>
          </button>
        </li>
      ))}
      {items.length === 0 && <li className="px-2 text-xs text-muted">None this week.</li>}
    </ul>
  )
  return (
    <Card title="Who moved up or down a level" tip="How many students moved to a different level between the last two weekly checks.">
      <div className="mb-3 flex gap-3 text-xs">
        <span className="flex items-center gap-1 rounded-full bg-rose-50 px-3 py-1 font-bold text-rose-700"><Direction d="up" /> {worse.length} got worse</span>
        <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 font-bold text-emerald-700"><Direction d="down" /> {better.length} improved</span>
        <span className="rounded-full bg-gray-100 px-3 py-1 font-bold text-gray-600">{rows.length - moved.length} unchanged</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div><p className="mb-1 text-xs font-bold uppercase tracking-wider text-muted">Getting worse</p><List items={worse} tone="text-rose-600" /></div>
        <div><p className="mb-1 text-xs font-bold uppercase tracking-wider text-muted">Recovering</p><List items={better} tone="text-emerald-600" /></div>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-center text-xs">
          <caption className="pb-1 text-left text-xs font-bold uppercase tracking-wider text-muted">Last week (down) to this week (across)</caption>
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
    <Card title="Where students struggle most" tip="Courses ranked by the share of students who need help. Select a course to see how quickly students got flagged.">
      <QueryState query={q} isEmpty={(d) => !d.cohorts?.length} empty={<EmptyState title="No course data yet" />}>
        {(d) => {
          const sorted = [...d.cohorts].sort((a, b) => b.at_risk_share - a.at_risk_share)
          const cur = sorted.find((c) => c.course_id === sel) ?? sorted[0]
          return (
            <div className="grid gap-5 lg:grid-cols-2">
              <ul className="space-y-1">
                {sorted.slice(0, 10).map((c) => (
                  <li key={c.course_id}>
                    <button type="button" onClick={() => setSel(c.course_id)} aria-pressed={cur.course_id === c.course_id} className={`flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-xs ${cur.course_id === c.course_id ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
                      <span className="w-16 shrink-0 text-left font-semibold">{c.course_id}</span>
                      <div className="h-2.5 flex-1 rounded-full bg-gray-100"><div className="h-2.5 rounded-full bg-rose-400" style={{ width: `${Math.min(100, c.at_risk_share * 100)}%` }} /></div>
                      <span className="w-20 text-right tabular-nums text-ink-2">{pct(c.at_risk_share)} of {c.n_active}</span>
                    </button>
                  </li>
                ))}
              </ul>
              <div>
                <p className="flex items-center gap-1 text-xs font-bold text-ink">How quickly students got flagged in {courseName(cur.course_id)} <InfoTip text="Share of students flagged as needing help at any weekly check up to each week." /></p>
                <LineChart points={(cur.time_to_risk ?? []).map((p) => ({ x: p.day, y: p.cumulative_signalled_share }))} color="#F43F5E" />
                {cur.hotspot && (
                  <p className="mt-2 rounded-xl bg-amber-50 p-2.5 text-xs text-amber-900">
                    Students most often first slipped at <b>{cur.hotspot.label}</b> ({termWeek(cur.hotspot.due_day).toLowerCase()}){cur.hotspot.share_of_at_risk != null ? `: ${pct(cur.hotspot.share_of_at_risk)} of struggling students` : ''}.
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
    <Card title="Has the student population changed?" tip="Compares this campus's data with the data the model learned from (PSI score). Above 0.2 means the data looks quite different.">
      <QueryState query={q} empty={<EmptyState title="No comparison yet" message="Run the weekly check first." />} isEmpty={(d) => !d.data_drift}>
        {(d) => {
          const dd = d.data_drift as { features?: DriftFeature[]; retrain_recommended?: boolean; max_psi?: number; current_rows?: number; reference_rows?: number }
          const feats = dd.features ?? []
          const shifted = feats.filter((f) => f.status === 'shift').length
          const maxP = Math.max(0.3, ...feats.map((f) => Math.min(f.psi, 1)))
          return (
            <>
              <div className={`mb-3 flex items-start gap-2 rounded-xl p-3 text-xs ${dd.retrain_recommended ? 'bg-amber-50 text-amber-900' : 'bg-emerald-50 text-emerald-900'}`}>
                {dd.retrain_recommended ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
                <p>{dd.retrain_recommended ? `${shifted} of ${feats.length} things we look at have changed a lot since the model was built. Treat results as a guide until it is refreshed.` : 'The students look like the ones the model learned from.'}</p>
              </div>
              <ul className="grid gap-x-8 gap-y-1.5 md:grid-cols-2">
                {feats.slice(0, 12).map((f) => (
                  <li key={f.feature} className="flex items-center gap-3 text-xs">
                    <span className="w-36 shrink-0 truncate text-ink-2" title={f.feature}>{pretty(f.feature)}</span>
                    <div className="h-2 flex-1 rounded-full bg-gray-100"><div className={`h-2 rounded-full ${f.status === 'shift' ? 'bg-rose-400' : f.status === 'watch' ? 'bg-amber-400' : 'bg-emerald-500'}`} style={{ width: `${Math.max(2, (Math.min(f.psi, 1) / maxP) * 100)}%` }} /></div>
                    <span className="w-10 text-right tabular-nums text-xs text-muted">{f.psi.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-muted">The 12 biggest changes. Red is above 0.2, amber 0.1 to 0.2.</p>
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
  const trend = useMemo(() => [...(runs.data?.items ?? [])].reverse().map((r) => ({ label: `Week ${Math.max(1, Math.round(r.as_of_day / 7))}`, counts: r.tier_counts as Record<string, number> })), [runs.data])
  const name = (r: ScoreRow) => displayName(people, r)
  const openRow = (r: ScoreRow) => setOpen({ key: r.student_id ?? r.external_student_ref_hash ?? r.student_ref, name: name(r) })

  return (
    <div className="flex flex-col gap-4 font-sans">
      <ModelHeader />
      <ProofCards />
      <EarlyWarningHero />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="How the picture changed week by week" tip="Each column is one weekly check. Watch the red and orange shrink as support works.">
          {runs.isPending ? <LoadingSkeleton rows={2} /> : runs.isError ? <ErrorState error={runs.error} onRetry={() => void runs.refetch()} /> : trend.length < 2 ? <p className="text-xs text-muted">Needs at least two weekly checks.</p> : (<><TierRunsChart runs={trend} /><div className="mt-2"><ColorLegend /></div></>)}
        </Card>
        <RunScoring />
      </div>
      <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="No results yet" message="Run the weekly check to see who moved." />}>
        {(d) => <Movement rows={d.items} name={name} onOpen={openRow} />}
      </QueryState>
      <Hotspots />
      <ModelDetails />
      <StudentInsightDrawer studentKey={open?.key ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}
