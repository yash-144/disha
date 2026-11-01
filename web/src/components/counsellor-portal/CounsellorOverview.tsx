import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import {
  useCaseload,
  useCounsellorDashboard,
  useCounsellingSessions,
  useFollowups,
} from '../../lib/api/endpoints/counsellor.hooks'

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-4">
      <p className="text-2xl font-bold text-[#1E2433]">{value}</p>
      <p className="text-xs text-[#717E95]">{label}</p>
    </div>
  )
}

export function CounsellorOverview() {
  const dash = useCounsellorDashboard()
  const caseload = useCaseload()
  const followups = useFollowups()
  const sessions = useCounsellingSessions()
  return (
    <div className="flex flex-col gap-4 font-sans">
      <QueryState query={dash}>
        {(d) => (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            <Stat label="Active cases" value={d.active_cases} />
            <Stat label="Overdue cases" value={d.overdue_cases} />
            <Stat label="Escalated" value={d.escalated_cases} />
            <Stat label="Upcoming sessions" value={d.upcoming_sessions} />
            <Stat label="Overdue follow-ups" value={d.overdue_followups} />
            <Stat label="Unread notifications" value={d.unread_notifications} />
          </div>
        )}
      </QueryState>
      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-3xl border border-gray-100 bg-white p-5">
          <h2 className="text-sm font-bold">My caseload</h2>
          <div className="mt-3">
            <QueryState query={caseload} empty={<EmptyState title="No cases assigned" />}>
              {(rows) => (
                <ul className="space-y-2 text-xs">
                  {rows.map((c) => (
                    <li key={c.case_id} className="flex justify-between gap-2">
                      <span>{c.student_name ?? c.student_ref ?? 'Student'}</span>
                      <span className="text-[#717E95]">
                        {c.state}, {c.priority}{c.is_overdue ? ', overdue' : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </div>
        </section>
        <section className="rounded-3xl border border-gray-100 bg-white p-5">
          <h2 className="text-sm font-bold">Upcoming follow-ups</h2>
          <div className="mt-3">
            <QueryState query={followups} empty={<EmptyState title="No upcoming follow-ups" />}>
              {(rows) => (
                <ul className="space-y-2 text-xs">
                  {rows.map((f) => (
                    <li key={f.id} className="flex justify-between gap-2">
                      <span>{f.title}</span>
                      <span className="text-[#717E95]">{new Date(f.scheduled_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </div>
        </section>
        <section className="rounded-3xl border border-gray-100 bg-white p-5">
          <h2 className="text-sm font-bold">Sessions</h2>
          <div className="mt-3">
            <QueryState query={sessions} empty={<EmptyState title="No sessions scheduled" />}>
              {(rows) => (
                <ul className="space-y-2 text-xs">
                  {rows.map((s) => (
                    <li key={s.id} className="flex justify-between gap-2">
                      <span>{s.student_name ?? 'Student'} ({s.status})</span>
                      <span className="text-[#717E95]">{new Date(s.scheduled_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </div>
        </section>
      </div>
    </div>
  )
}
