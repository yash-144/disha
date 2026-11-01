import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { Card, Kpi, KpiStrip, Pill, fmtDateTime } from '../common/ui'
import { priorityLabel, stageLabel, studentName } from '../../lib/labels'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { useCaseload, useCounsellorDashboard, useCounsellingSessions, useFollowups } from '../../lib/api/endpoints/counsellor.hooks'

const PRIORITY: Record<string, string> = { urgent: 'bg-rose-50 text-rose-700', critical: 'bg-rose-50 text-rose-700', high: 'bg-orange-50 text-orange-700', medium: 'bg-amber-50 text-amber-700', low: 'bg-sunken text-ink-2' }
const ORDER: Record<string, number> = { urgent: 0, critical: 0, high: 1, medium: 2, low: 3 }

export function CounsellorOverview() {
  const dash = useCounsellorDashboard()
  const caseload = useCaseload()
  const followups = useFollowups()
  const sessions = useCounsellingSessions()
  const [openCase, setOpenCase] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-4 font-sans">
      <QueryState query={dash}>
        {(d) => (
          <KpiStrip cols="lg:grid-cols-5">
            <Kpi label="Active cases" value={d.active_cases} tip="Cases assigned to you that are still open." />
            <Kpi label="Overdue follow-ups" value={d.overdue_followups} tone={d.overdue_followups ? 'text-tier-high' : 'text-tier-ok'} tip="Check-ins that were planned but not done yet." />
            <Kpi label="Upcoming sessions" value={d.upcoming_sessions} tip="Counselling sessions still to happen." />
            <Kpi label="Overdue cases" value={d.overdue_cases} tone={d.overdue_cases ? 'text-tier-high' : undefined} tip="Cases past their due date." />
            <Kpi label="Escalated" value={d.escalated_cases} tip="Cases passed up for more help." />
          </KpiStrip>
        )}
      </QueryState>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3" title="My caseload" tip="Highest priority first. Open a case to add notes, support and follow-ups.">
          <QueryState query={caseload} empty={<EmptyState title="No cases assigned to you yet" />}>
            {(rows) => (
              <ul className="divide-y divide-line">
                {[...rows].sort((a, b) => Number(b.is_overdue) - Number(a.is_overdue) || (ORDER[a.priority] ?? 9) - (ORDER[b.priority] ?? 9)).map((c) => (
                  <li key={c.case_id}>
                    <button type="button" onClick={() => setOpenCase(c.case_id)} className="flex w-full items-center justify-between gap-3 py-2.5 text-left text-xs hover:bg-sunken/60">
                      <span className="min-w-0">
                        <span className="block truncate font-semibold text-ink">{studentName(c.student_name, c.student_ref)}</span>
                        <span className="text-xs text-muted">{stageLabel(c.state)}</span>
                      </span>
                      <span className="flex shrink-0 items-center gap-1.5">
                        {c.is_overdue && <Pill tone="bg-rose-50 text-rose-700">Overdue</Pill>}
                        <Pill tone={PRIORITY[c.priority] ?? PRIORITY.low}>{priorityLabel(c.priority)}</Pill>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </QueryState>
        </Card>
        <div className="flex flex-col gap-4 lg:col-span-2">
          <Card title="Follow-ups due" tip="Planned check-ins, soonest first.">
            <QueryState query={followups} empty={<EmptyState title="Nothing due" />}>
              {(rows) => (
                <ul className="divide-y divide-line">
                  {[...rows].sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)).slice(0, 6).map((f) => (
                    <li key={f.id}>
                      <button type="button" onClick={() => setOpenCase(f.case_id)} className="flex w-full items-center justify-between gap-2 py-2 text-left text-xs hover:bg-sunken/60">
                        <span className="truncate font-medium">{f.title}</span>
                        <span className={`shrink-0 tabular-nums ${f.is_overdue ? 'font-semibold text-tier-high' : 'text-muted'}`}>{f.is_overdue ? 'Overdue · ' : ''}{fmtDateTime(f.scheduled_at)}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </Card>
          <Card title="Next sessions" tip="Your upcoming counselling sessions.">
            <QueryState query={sessions} isEmpty={(r) => !r.some((s) => s.status === 'scheduled')} empty={<EmptyState title="No sessions scheduled" />}>
              {(rows) => (
                <ul className="divide-y divide-line">
                  {rows.filter((s) => s.status === 'scheduled').sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)).slice(0, 5).map((s) => (
                    <li key={s.id} className="flex items-center justify-between gap-2 py-2 text-xs">
                      <span className="truncate font-medium">{studentName(s.student_name)}</span>
                      <span className="shrink-0 tabular-nums text-muted">{fmtDateTime(s.scheduled_at)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </Card>
        </div>
      </div>
      {openCase && <CaseDetailDrawer caseId={openCase} onClose={() => setOpenCase(null)} userRole="counsellor" />}
    </div>
  )
}
