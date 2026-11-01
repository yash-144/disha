import React, { useMemo, useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { SearchInput, TierBadge } from '../common/ui'
import { useFacultySections, useSectionStudents } from '../../lib/api/endpoints/faculty.hooks'
import { useAllScores } from '../../lib/api/endpoints/risk'
import type { SectionStudent } from '../../lib/api/endpoints/faculty'

const RANK: Record<string, number> = { HIGH: 3, MEDIUM: 2, WATCH: 1, ON_TRACK: 0 }

function Directory({ sectionIds }: { sectionIds: string[] }) {
  const results = useSectionStudents(sectionIds)
  const scores = useAllScores()
  const [q, setQ] = useState('')
  const tiers = useMemo(() => {
    const m = new Map<string, string>()
    scores.data?.items.forEach((r) => {
      if (r.student_id && (!m.has(r.student_id) || RANK[r.tier] > RANK[m.get(r.student_id)!])) m.set(r.student_id, r.tier)
    })
    return m
  }, [scores.data])
  const students = useMemo(() => {
    const seen = new Map<string, SectionStudent>()
    results.forEach((r) => r.data?.forEach((s) => seen.set(s.id, s)))
    return [...seen.values()]
      .filter((s) => `${s.full_name} ${s.student_uid}`.toLowerCase().includes(q.toLowerCase()))
      .sort((a, b) => (RANK[tiers.get(b.id) ?? ''] ?? -1) - (RANK[tiers.get(a.id) ?? ''] ?? -1) || a.full_name.localeCompare(b.full_name))
  }, [results, q, tiers])
  if (results.some((r) => r.isPending)) return <p className="text-xs text-muted">Loading students…</p>
  if (results.some((r) => r.isError)) return <p role="alert" className="text-xs text-tier-high">Could not load students.</p>
  return (
    <div className="flex flex-col gap-3">
      <SearchInput value={q} onChange={setQ} placeholder="Search name or ID" />
      {students.length === 0 ? (
        <EmptyState title="No students found" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-line bg-panel">
          <table className="w-full min-w-[560px] text-left text-xs">
            <thead><tr className="border-b border-line text-[11px] text-muted"><th className="p-3 font-semibold">Student</th><th className="p-3 font-semibold">Attendance</th><th className="p-3 font-semibold">Quiz average</th><th className="p-3 font-semibold">Risk</th></tr></thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} className="border-b border-line/60">
                  <td className="p-3"><p className="font-semibold">{s.full_name}</p><p className="text-[11px] text-muted">{s.student_uid}{s.department ? ` · ${s.department}` : ''}</p></td>
                  <td className="p-3 tabular-nums">{s.attendance_rate != null ? `${Math.round(s.attendance_rate)}%` : '—'}</td>
                  <td className="p-3 tabular-nums">{s.quiz_score_avg != null ? `${Math.round(s.quiz_score_avg)}%` : '—'}</td>
                  <td className="p-3">{tiers.get(s.id) ? <TierBadge tier={tiers.get(s.id)} /> : <span className="text-muted">Not scored</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export function StudentDirectoryPage() {
  const sections = useFacultySections()
  return (
    <main className="flex min-w-0 flex-1 flex-col gap-4 p-4 font-sans sm:p-6 lg:px-8 lg:py-6">
      <h1 className="font-display text-[34px] leading-tight tracking-tight">Student Directory</h1>
      <QueryState query={sections} empty={<EmptyState title="No sections assigned" />}>
        {(rows) => <Directory sectionIds={rows.map((s) => s.id)} />}
      </QueryState>
    </main>
  )
}
