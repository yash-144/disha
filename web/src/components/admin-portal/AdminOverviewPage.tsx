import React, { useMemo, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { QueryState, EmptyState, ErrorState, LoadingSkeleton } from '../common/QueryState'
import { Bars, Card, KpiStrip, Direction, Donut, Kpi, TierBadge, ColorLegend, TierTrend, TIERS, TIER_STYLE, pct, Button, type Bucket, type Tier } from '../common/ui'
import { useAnalyticsOverview, useCohorts, useRuns } from '../../lib/api/endpoints/admin.hooks'
import { buildPeopleIndex, displayName, useAllCases, useAllScores } from '../../lib/api/endpoints/risk'
import { EarlyWarningHero } from './EarlyWarning'
import { StudentInsightDrawer } from './StudentInsightDrawer'

const STAGES: { label: string; states: string[]; tone: string }[] = [
  { label: 'New', states: ['suggested', 'under_review', 'action_planned'], tone: 'bg-tier-medium' },
  { label: 'Assigned', states: ['assigned', 'accepted'], tone: 'bg-tier-watch' },
  { label: 'In support', states: ['contact_attempted', 'support_in_progress', 'failed_contact', 'service_unavailable', 'reopened'], tone: 'bg-accent' },
  { label: 'Follow-up', states: ['follow_up_due', 'outcome_reviewed'], tone: 'bg-accent-dark' },
  { label: 'Closed', states: ['closed', 'dismissed'], tone: 'bg-tier-ok' },
]
function Pipeline({ cases }: { cases: { by_state: Bucket[] } }) {
  const vals = STAGES.map((st) => {
    const rows = cases.by_state.filter((b) => st.states.includes(b.label))
    return { ...st, n: rows.reduce((x, b) => x + (b.count ?? 0), 0), suppressed: rows.some((b) => b.suppressed) }
  })
  const max = Math.max(1, ...vals.map((v) => v.n))
  return (
    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-md bg-line sm:grid-cols-5">
      {vals.map((v) => (
        <div key={v.label} className="bg-panel p-4">
          <p className="text-xs font-semibold text-ink-2">{v.label}</p>
          <p className="mt-1 font-display text-[34px] leading-none tabular-nums">{v.n === 0 && v.suppressed ? '<5' : v.n}</p>
          <div className="mt-3 h-1.5 rounded-full bg-sunken"><div className={`h-1.5 rounded-full ${v.tone}`} style={{ width: `${(v.n / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

interface Overview {
  cases?: { total_cases: number; open_cases: number; by_state: Bucket[]; open_by_age: Bucket[]; open_by_owner: Bucket[] }
  interventions?: { interventions_total: number; outcomes_recorded: number }
  followups?: { completion_rate: number | null; on_time_rate: number | null }
}

export function AdminOverviewPage({ onNavigateTab }: { onNavigateTab: (tab: string) => void }) {
  const analytics = useAnalyticsOverview()
  const runs = useRuns()
  const scores = useAllScores()
  const cases = useAllCases()
  const cohorts = useCohorts()
  const [open, setOpen] = useState<{ key: string; name: string } | null>(null)

  const people = useMemo(() => buildPeopleIndex(cases.data), [cases.data])
  const latest = runs.data?.items?.[0]
  const counts = (latest?.tier_counts ?? {}) as Record<string, number>
  const total = TIERS.reduce((a, t) => a + (counts[t] ?? 0), 0)
  const a = (analytics.data ?? {}) as Overview
  const overdue = cases.data?.filter((c) => c.is_overdue && !['closed', 'dismissed'].includes(c.state)).length

  const students = useMemo(() => new Set(scores.data?.items.map((r) => r.student_id ?? r.student_ref)).size, [scores.data])
  const top = useMemo(() => {
    // highest risk per student (rows arrive sorted by probability)
    const seen = new Set<string>()
    const out = []
    for (const r of scores.data?.items ?? []) {
      const k = r.student_id ?? r.student_ref
      if (seen.has(k)) continue
      seen.add(k)
      out.push(r)
      if (out.length >= 8) break
    }
    return out
  }, [scores.data])

  const trend = useMemo(
    () => [...(runs.data?.items ?? [])].reverse().map((r) => ({ label: `Day ${r.as_of_day}`, counts: r.tier_counts as Record<string, number> })),
    [runs.data],
  )

  if (runs.isPending) return <LoadingSkeleton rows={4} />
  if (runs.isError) return <ErrorState error={runs.error} onRetry={() => void runs.refetch()} />
  if (!latest)
    return (
      <EmptyState
        title="No risk scores yet"
        message="Import your data, then run the risk model to see who needs support."
        action={
          <div className="flex gap-2">
            <Button onClick={() => onNavigateTab('data-import')}>Import data</Button>
            <Button variant="ghost" onClick={() => onNavigateTab('risk-model')}>Open risk model</Button>
          </div>
        }
      />
    )

  const flagged = (counts.HIGH ?? 0) + (counts.MEDIUM ?? 0)

  return (
    <div className="flex flex-col gap-4 font-sans">
      <EarlyWarningHero />

      <KpiStrip>
        <Kpi label="Students scored" value={scores.data ? students : '…'} hint={`${total} course enrolments`} tip="Each student is scored once per course, every week." />
        <Kpi label="Flagged for support" value={flagged} tone="text-tier-high" hint="High and medium risk" tip="Enrolments where the model is confident enough to suggest action." onClick={() => onNavigateTab('risk-model')} />
        <Kpi label="Open cases" value={a.cases?.open_cases ?? '…'} hint={`${a.cases?.total_cases ?? 0} in total`} tip="Cases a counsellor is still working on." onClick={() => onNavigateTab('case-management')} />
        <Kpi label="Overdue" value={overdue ?? '…'} tone={overdue ? 'text-tier-medium' : 'text-tier-ok'} hint="Past their due date" tip="Open cases whose next action is late." onClick={() => onNavigateTab('case-management')} />
        <Kpi label="Follow-ups done" value={pct(a.followups?.completion_rate)} hint={`${pct(a.followups?.on_time_rate)} on time`} tip="Share of planned follow-ups that were completed." />
      </KpiStrip>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2" title="Risk across campus" tip="Latest weekly scoring. Each enrolment falls into one of four tiers.">
          <div className="flex flex-col items-center gap-4 xl:flex-row">
            <Donut counts={counts} centre={String(total)} sub="enrolments" />
            <div className="w-full space-y-2">
              {TIERS.map((t) => (
                <div key={t} className="flex items-center justify-between gap-2 text-xs" title={TIER_STYLE[t].help}>
                  <span className="flex items-center gap-2 font-semibold text-ink">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: TIER_STYLE[t].color }} />
                    {TIER_STYLE[t].label}
                  </span>
                  <span className="tabular-nums text-ink-2">{counts[t] ?? 0} · {pct((counts[t] ?? 0) / Math.max(1, total))}</span>
                </div>
              ))}
              <p className="pt-1 text-xs text-muted">Day {latest.as_of_day} of the term.</p>
            </div>
          </div>
        </Card>
        <Card className="lg:col-span-3" title="How risk is changing" tip="Tier counts at each weekly scoring run, oldest on the left. More green and less red means things are improving."
          action={<button type="button" onClick={() => onNavigateTab('risk-model')} className="flex items-center text-xs font-semibold text-indigo-600">Risk model <ChevronRight className="h-3 w-3" /></button>}>
          {trend.length < 2 ? <p className="text-xs text-muted">Needs at least two scoring runs.</p> : <TierTrend points={trend} />}
          <div className="mt-2"><ColorLegend /></div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3" title="Students who need attention first" tip="Highest chance of failing or withdrawing, one row per student. Click a row to see why.">
          <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="Nobody flagged" />}>
            {() => (
              <ul className="divide-y divide-line">
                {top.map((r) => {
                  const name = displayName(people, r)
                  return (
                    <li key={r.id}>
                      <button type="button" onClick={() => setOpen({ key: r.student_id ?? r.external_student_ref_hash ?? r.student_ref, name })} className="flex w-full items-center gap-3 py-2.5 text-left text-xs hover:bg-gray-50">
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-bold text-ink">{name} <span className="font-normal text-muted">· {r.course_id}</span></p>
                          {r.reasons?.[0] && <p className="truncate text-xs text-ink-2">{r.reasons[0].text}</p>}
                        </div>
                        <TierBadge tier={r.tier} />
                        <span className="flex w-14 items-center justify-end gap-1 font-bold tabular-nums" style={{ color: TIER_STYLE[r.tier as Tier].color }}>
                          {pct(r.probability)} <Direction d={r.direction} />
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </QueryState>
        </Card>
        <Card className="lg:col-span-2" title="Courses with the most students at risk" tip="Share of active students in the course who are High or Medium risk.">
          <QueryState query={cohorts} isEmpty={(d) => !d.cohorts?.length} empty={<EmptyState title="No course data" />}>
            {(d) => (
              <ul className="space-y-2.5">
                {[...d.cohorts].sort((x, y) => y.at_risk_share - x.at_risk_share).slice(0, 7).map((c) => (
                  <li key={c.course_id} className="flex items-center gap-3 text-xs">
                    <span className="w-14 shrink-0 font-semibold">{c.course_id}</span>
                    <div className="h-2.5 flex-1 rounded-full bg-gray-100"><div className="h-2.5 rounded-full bg-rose-400" style={{ width: `${Math.min(100, c.at_risk_share * 100)}%` }} /></div>
                    <span className="w-10 text-right font-semibold tabular-nums">{pct(c.at_risk_share)}</span>
                  </li>
                ))}
              </ul>
            )}
          </QueryState>
        </Card>
      </div>

      <Card title="Case pipeline" tip="Every flagged student becomes a case. This shows how many sit at each step, from first suggestion to closed." action={<button type="button" onClick={() => onNavigateTab('case-management')} className="flex items-center text-xs font-semibold text-accent">All cases <ChevronRight className="h-3 w-3" /></button>}>
        {a.cases ? <Pipeline cases={a.cases} /> : <LoadingSkeleton rows={1} />}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Open cases by owner" tip="Who is currently responsible. 'Unassigned' cases need an owner.">{a.cases ? <Bars rows={a.cases.open_by_owner} color="bg-accent" /> : <LoadingSkeleton rows={2} />}</Card>
        <Card title="Open cases by age" tip="How long open cases have been waiting.">{a.cases ? <Bars rows={a.cases.open_by_age} color="bg-tier-watch" showEmpty /> : <LoadingSkeleton rows={2} />}</Card>
      </div>
      <p className="text-xs text-muted">Groups smaller than 5 show as “&lt;5” to protect student privacy.</p>

      <StudentInsightDrawer studentKey={open?.key ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}
