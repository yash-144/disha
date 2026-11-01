import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { Bars, Card, Kpi, KpiStrip, fmtCount, pct, pretty, type Bucket } from '../common/ui'
import { useAnalyticsOverview } from '../../lib/api/endpoints/admin.hooks'

interface Overview {
  cases?: { total_cases: number; open_cases: number; by_state: Bucket[]; open_by_age: Bucket[]; open_by_owner: Bucket[] }
  interventions?: {
    interventions_total: number
    outcomes_recorded: number
    by_completion_status: Bucket[]
    by_intervention: { intervention: string; total: number | null; suppressed?: boolean; outcomes: Bucket[] }[]
  }
  followups?: { completion_rate: number | null; on_time_rate: number | null; by_status: Bucket[] }
  time_to_first_contact?: { median_hours: number | null; p90_hours: number | null; suppressed?: boolean }
}

/** Case, intervention and follow-up analytics (shared by the admin and counsellor portals). Counts under 5 show as "<5". */
export function AdminAnalyticsPage() {
  const q = useAnalyticsOverview()
  return (
    <QueryState query={q} isEmpty={(d) => !d || Object.keys(d).length === 0} empty={<EmptyState title="No analytics yet" message="Numbers appear once cases exist." />}>
      {(raw) => {
        const d = raw as Overview
        const c = d.cases
        const f = d.followups
        const iv = d.interventions
        const ttc = d.time_to_first_contact
        return (
          <div className="flex flex-col gap-4 font-sans">
            <KpiStrip cols="lg:grid-cols-5">
              <Kpi label="Cases" value={c?.total_cases ?? '—'} hint={`${c?.open_cases ?? 0} still open`} tip="All cases created from flags and requests." />
              <Kpi label="Interventions" value={iv?.interventions_total ?? '—'} hint={`${iv?.outcomes_recorded ?? 0} with an outcome`} tip="Actions taken to help a student, such as a counselling session." />
              <Kpi label="Follow-ups done" value={pct(f?.completion_rate)} hint={`${pct(f?.on_time_rate)} on time`} tip="Share of planned follow-ups completed." />
              <Kpi label="Median time to contact" value={ttc?.suppressed || ttc?.median_hours == null ? '<5' : `${Math.round(ttc.median_hours)}h`} hint="From case created to first contact" tip="Hidden when fewer than 5 cases have a contact, to protect privacy." />
              <Kpi label="Improved" value={fmtCount(iv?.by_completion_status.find((b) => b.label === 'improved')?.count, iv?.by_completion_status.find((b) => b.label === 'improved')?.suppressed)} hint="of recorded outcomes" tone="text-tier-ok" />
            </KpiStrip>
            <div className="grid gap-4 lg:grid-cols-3">
              <Card title="Cases by stage" tip="Where each case is in the support workflow.">{c ? <Bars rows={c.by_state} /> : null}</Card>
              <Card title="Open cases by owner" tip="Who is responsible. 'Unassigned' needs an owner.">{c ? <Bars rows={c.open_by_owner} color="bg-accent" /> : null}</Card>
              <Card title="Open cases by age" tip="How long open cases have waited.">{c ? <Bars rows={c.open_by_age} color="bg-tier-watch" showEmpty /> : null}</Card>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card title="Follow-ups" tip="Planned check-ins and whether they happened.">{f ? <Bars rows={f.by_status} color="bg-tier-ok" showEmpty /> : null}</Card>
              <Card title="Outcomes of support" tip="How students were doing after an intervention finished.">{iv ? <Bars rows={iv.by_completion_status} color="bg-tier-ok" showEmpty /> : null}</Card>
            </div>
            {iv && iv.by_intervention.some((x) => !x.suppressed) && (
              <Card title="What was used" tip="Interventions with at least 5 uses.">
                <ul className="divide-y divide-line text-xs">
                  {iv.by_intervention.filter((x) => !x.suppressed).map((x) => (
                    <li key={x.intervention} className="flex items-center justify-between py-2"><span className="font-semibold">{pretty(x.intervention)}</span><span className="tabular-nums text-muted">{x.total} used</span></li>
                  ))}
                </ul>
              </Card>
            )}
            <p className="text-xs text-muted">Groups smaller than 5 show as “&lt;5” to protect student privacy.</p>
          </div>
        )
      }}
    </QueryState>
  )
}
