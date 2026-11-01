import React, { useMemo, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { QueryState, EmptyState, ErrorState, LoadingSkeleton } from '../common/QueryState'
import { Bars, Button, Card, Direction, TierBadge, TIERS, TIER_STYLE, pct, type Bucket, type Tier } from '../common/ui'
import { courseName, inTen, termWeek } from '../../lib/labels'
import { useAnalyticsOverview, useCohorts, useRuns } from '../../lib/api/endpoints/admin.hooks'
import { buildPeopleIndex, displayName, useAllCases, useAllScores, type ScoreRow } from '../../lib/api/endpoints/risk'
import { EarlyWarningHero } from './EarlyWarning'
import { ProofCards } from './ProofCards'
import { RankedBars, Sparkline, TierDonut, TierRunsChart } from './charts'
import { StudentInsightDrawer } from './StudentInsightDrawer'

const RANK: Record<string, number> = { ON_TRACK: 0, WATCH: 1, MEDIUM: 2, HIGH: 3 }

const STAGES: { label: string; states: string[]; tone: string }[] = [
  { label: 'New', states: ['suggested', 'under_review', 'action_planned'], tone: 'bg-tier-medium' },
  { label: 'Assigned', states: ['assigned', 'accepted'], tone: 'bg-tier-watch' },
  { label: 'In support', states: ['contact_attempted', 'support_in_progress', 'failed_contact', 'service_unavailable', 'reopened'], tone: 'bg-accent' },
  { label: 'Follow-up', states: ['follow_up_due', 'outcome_reviewed'], tone: 'bg-accent-dark' },
  { label: 'Resolved', states: ['closed', 'dismissed'], tone: 'bg-tier-ok' },
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
          <p className="text-sm font-semibold text-ink-2">{v.label}</p>
          <p className="mt-1 font-display text-4xl leading-none">{v.n === 0 && v.suppressed ? '<5' : v.n}</p>
          <div className="mt-3 h-2 rounded-full bg-sunken"><div className={`h-2 rounded-full ${v.tone}`} style={{ width: `${(v.n / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

interface Overview {
  cases?: { total_cases: number; open_cases: number; by_state: Bucket[]; open_by_age: Bucket[]; open_by_owner: Bucket[] }
  followups?: { completion_rate: number | null; on_time_rate: number | null; by_status: Bucket[] }
}

function Section({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-ink">{title}</h2>
        {sub && <p className="text-sm text-ink-2">{sub}</p>}
      </div>
      {children}
    </section>
  )
}

function delta(now: number, prev: number | undefined, lowerIsBetter = true): { text: string; good: boolean | null } | undefined {
  if (prev == null) return undefined
  const d = now - prev
  if (d === 0) return { text: 'No change since last week', good: null }
  return { text: `${d > 0 ? '+' : ''}${d} since last week`, good: lowerIsBetter ? d < 0 : d > 0 }
}

export function AdminOverviewPage({ onNavigateTab }: { onNavigateTab: (tab: string) => void }) {
  const analytics = useAnalyticsOverview()
  const runs = useRuns()
  const scores = useAllScores()
  const cases = useAllCases()
  const cohorts = useCohorts()
  const [open, setOpen] = useState<{ key: string; name: string } | null>(null)

  const people = useMemo(() => buildPeopleIndex(cases.data), [cases.data])
  const items = runs.data?.items ?? []
  const latest = items[0]
  const previous = items[1]
  const counts = (latest?.tier_counts ?? {}) as Record<string, number>
  const total = TIERS.reduce((a, t) => a + (counts[t] ?? 0), 0)
  const a = (analytics.data ?? {}) as Overview
  const overdue = cases.data?.filter((c) => c.is_overdue && !['closed', 'dismissed'].includes(c.state)).length
  const flaggedOf = (c?: Record<string, number>) => (c?.HIGH ?? 0) + (c?.MEDIUM ?? 0)
  const flagged = flaggedOf(counts)
  const chrono = [...items].reverse()

  const studentCount = useMemo(() => new Set(scores.data?.items.map((r) => r.student_id ?? r.student_ref)).size, [scores.data])
  const top = useMemo(() => {
    const seen = new Set<string>()
    const out: ScoreRow[] = []
    for (const r of scores.data?.items ?? []) {
      const k = r.student_id ?? r.student_ref
      if (seen.has(k)) continue
      seen.add(k)
      out.push(r)
      if (out.length >= 7) break
    }
    return out
  }, [scores.data])
  const moved = useMemo(() => {
    const m = (scores.data?.items ?? []).filter((r) => r.previous_tier && r.previous_tier !== r.tier)
    return {
      worse: m.filter((r) => RANK[r.tier] > RANK[r.previous_tier!]).sort((x, y) => y.probability - x.probability).slice(0, 4),
      better: m.filter((r) => RANK[r.tier] < RANK[r.previous_tier!]).sort((x, y) => y.probability - x.probability).slice(0, 4),
      nWorse: m.filter((r) => RANK[r.tier] > RANK[r.previous_tier!]).length,
      nBetter: m.filter((r) => RANK[r.tier] < RANK[r.previous_tier!]).length,
    }
  }, [scores.data])
  const openRow = (r: ScoreRow) => setOpen({ key: r.student_id ?? r.external_student_ref_hash ?? r.student_ref, name: displayName(people, r) })

  if (runs.isPending) return <LoadingSkeleton rows={4} />
  if (runs.isError) return <ErrorState error={runs.error} onRetry={() => void runs.refetch()} />
  if (!latest)
    return (
      <EmptyState title="No results yet" message="Import your student data, then run the weekly check to see who needs support." action={<div className="flex gap-2"><Button onClick={() => onNavigateTab('data-import')}>Import data</Button><Button variant="ghost" onClick={() => onNavigateTab('risk-model')}>Run weekly check</Button></div>} />
    )

  const Move = ({ r }: { r: ScoreRow }) => (
    <li>
      <button type="button" onClick={() => openRow(r)} className="flex w-full items-center justify-between gap-3 rounded-md px-2 py-2 text-left text-sm hover:bg-sunken/60">
        <span className="min-w-0 truncate font-semibold">{displayName(people, r)} <span className="font-normal text-muted">{courseName(r.course_id)}</span></span>
        <span className="flex shrink-0 items-center gap-1.5 text-xs font-semibold"><TierBadge tier={r.previous_tier} /> <span aria-hidden="true">to</span> <TierBadge tier={r.tier} /></span>
      </button>
    </li>
  )

  return (
    <div className="flex flex-col gap-10 font-sans">
      <ProofCards />

      <Section title={`${flagged} of ${total} student-courses need attention this week`} sub={`${termWeek(latest.as_of_day)}. Click a student to see why.`}>
        <div className="grid gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-2" title="How students are doing this week" tip="Each student in each course lands in one of four groups. The top two groups are flagged for support.">
            <TierDonut counts={counts} />
          </Card>
          <Card className="lg:col-span-3" title="Who needs help most" tip="One row per student, with their biggest worry. Click for the reasons.">
            <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="Nobody flagged" />}>
              {() => (
                <ul className="divide-y divide-line">
                  {top.map((r) => (
                    <li key={r.id}>
                      <button type="button" onClick={() => openRow(r)} className="flex w-full items-center gap-3 py-3 text-left hover:bg-sunken/50">
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-bold text-ink">{displayName(people, r)} <span className="font-medium text-muted">{courseName(r.course_id)}</span></p>
                          {r.reasons?.[0] && <p className="truncate text-sm text-ink-2">{r.reasons[0].text}</p>}
                        </div>
                        <TierBadge tier={r.tier} />
                        <span className="flex w-24 items-center justify-end gap-1 text-sm font-bold tabular-nums" style={{ color: TIER_STYLE[r.tier as Tier].color }}>{inTen(r.probability)} <Direction d={r.direction} /></span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
            <p className="mt-2 border-t border-line pt-3 text-sm text-ink-2">“8 in 10” means a high chance this student struggles, fails or drops out.</p>
          </Card>
        </div>
      </Section>

      <Section title="How early we catch them" sub="Warning time is what makes support possible.">
        <EarlyWarningHero />
      </Section>

      <Section title="Where the risk sits" sub="Which courses and which direction the numbers are moving.">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Where students struggle most" tip="Share of students in each course who need help now or a closer look.">
            <QueryState query={cohorts} isEmpty={(d) => !d.cohorts?.length} empty={<EmptyState title="No course data yet" />}>
              {(d) => {
                const sorted = [...d.cohorts].sort((x, y) => y.at_risk_share - x.at_risk_share)
                return (
                  <>
                    <RankedBars rows={sorted.slice(0, 8).map((c) => ({ label: c.course_id, value: c.at_risk_share, sub: `${c.n_active} active students` }))} />
                    <p className="mt-1 border-t border-line pt-3 text-sm text-ink-2">{courseName(sorted[0].course_id)} has the most students who need help ({pct(sorted[0].at_risk_share)}).</p>
                  </>
                )
              }}
            </QueryState>
          </Card>
          <Card title="How the picture changed week by week" tip="Each bar is one weekly check of every student. Red and orange shrinking means support is working.">
            {chrono.length < 2 ? <p className="text-sm text-muted">Needs at least two weekly checks.</p> : <TierRunsChart runs={chrono.map((r) => ({ label: `Week ${Math.max(1, Math.round(r.as_of_day / 7))}`, counts: r.tier_counts as Record<string, number> }))} />}
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm">{TIERS.map((t) => <span key={t} className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-sm" style={{ background: TIER_STYLE[t].color }} />{TIER_STYLE[t].label}</span>)}</div>
            <p className="mt-3 border-t border-line pt-3 text-sm text-ink-2">{chrono.length >= 2 ? `On track grew from ${chrono[0].tier_counts.ON_TRACK ?? 0} to ${chrono[chrono.length - 1].tier_counts.ON_TRACK ?? 0} student-courses.` : ''}</p>
          </Card>
        </div>
        <Card title="Who moved up or down a level since last week" tip="Compared with the previous weekly check. Click a name to see why.">
          <div className="mb-3 flex flex-wrap gap-3 text-sm font-semibold">
            <span className="rounded bg-rose-50 px-3 py-1 text-tier-high">{moved.nWorse} got worse</span>
            <span className="rounded bg-emerald-50 px-3 py-1 text-tier-ok">{moved.nBetter} improved</span>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div><p className="mb-1 text-sm font-bold">Getting worse</p><ul>{moved.worse.map((r) => <Move key={r.id} r={r} />)}{moved.worse.length === 0 && <li className="px-2 text-sm text-muted">None this week.</li>}</ul></div>
            <div><p className="mb-1 text-sm font-bold">Recovering</p><ul>{moved.better.map((r) => <Move key={r.id} r={r} />)}{moved.better.length === 0 && <li className="px-2 text-sm text-muted">None this week.</li>}</ul></div>
          </div>
        </Card>
      </Section>

      <Section title="Is it working?" sub="Every flag should become a case with an owner and an outcome.">
        <Card title="Where each case stands" tip="Every flagged student becomes a case. Counts show how many sit at each step." action={<button type="button" onClick={() => onNavigateTab('case-management')} className="flex items-center text-sm font-semibold text-accent">All cases <ChevronRight className="h-4 w-4" /></button>}>
          {a.cases ? <Pipeline cases={a.cases} /> : <LoadingSkeleton rows={1} />}
        </Card>
        <div className="grid gap-4 lg:grid-cols-3">
          <Card title="Who is handling open cases" tip="Cases with no owner yet need someone to take them.">{a.cases ? <Bars rows={a.cases.open_by_owner} color="bg-accent" labelWidth="w-28" /> : <LoadingSkeleton rows={2} />}</Card>
          <Card title="How long open cases have waited" tip="Older cases need attention first.">{a.cases ? <Bars rows={a.cases.open_by_age} color="bg-tier-watch" showEmpty labelWidth="w-28" /> : <LoadingSkeleton rows={2} />}</Card>
          <Card title="Follow-up check-ins" tip="Planned check-ins and whether they happened.">{a.followups ? <Bars rows={a.followups.by_status} color="bg-tier-ok" showEmpty labelWidth="w-28" /> : <LoadingSkeleton rows={2} />}</Card>
        </div>
        <p className="text-sm text-muted">Groups smaller than 5 show as “&lt;5” to protect student privacy.</p>
      </Section>

      <StudentInsightDrawer studentKey={open?.key ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}
