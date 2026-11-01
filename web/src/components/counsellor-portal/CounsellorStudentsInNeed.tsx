import React, { useMemo, useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { Direction, SearchInput, TierBadge, TIER_STYLE, pct, type Tier } from '../common/ui'
import { buildPeopleIndex, displayName, useAllCases, useAllScores } from '../../lib/api/endpoints/risk'
import { StudentInsightDrawer } from '../admin-portal/StudentInsightDrawer'

const TIERS: Tier[] = ['HIGH', 'MEDIUM', 'WATCH']

/** Everyone the risk model flags, with the reasons. Click a row for the full explanation. */
export function CounsellorStudentsInNeed() {
  const [tier, setTier] = useState<Tier>('HIGH')
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState<{ key: string; name: string } | null>(null)
  const scores = useAllScores()
  const cases = useAllCases()
  const people = useMemo(() => buildPeopleIndex(cases.data), [cases.data])
  const counts = useMemo(() => Object.fromEntries(TIERS.map((t) => [t, scores.data?.items.filter((r) => r.tier === t).length ?? 0])), [scores.data])

  return (
    <div className="flex flex-col gap-3 font-sans">
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex gap-0.5 rounded-md bg-sunken p-1 text-xs" role="tablist">
          {TIERS.map((t) => (
            <button key={t} role="tab" aria-selected={tier === t} type="button" onClick={() => setTier(t)} className={`rounded px-3.5 py-1.5 font-semibold ${tier === t ? 'bg-panel shadow-sm' : 'text-muted hover:text-ink'}`}>
              {TIER_STYLE[t].label} <span className="tabular-nums text-muted">{counts[t]}</span>
            </button>
          ))}
        </div>
        <SearchInput value={search} onChange={setSearch} placeholder="Search name, ID or course" />
      </div>
      <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="No risk scores yet" message="An administrator needs to import data and run scoring first." />}>
        {(d) => {
          const rows = d.items.filter((r) => r.tier === tier && (!search || `${displayName(people, r)} ${r.student_ref} ${r.course_id}`.toLowerCase().includes(search.toLowerCase())))
          if (!rows.length) return <EmptyState title="No students match" />
          return (
            <div className="overflow-x-auto rounded-lg border border-line bg-panel">
              <table className="w-full min-w-[620px] text-left text-xs">
                <thead><tr className="border-b border-line text-[11px] text-muted"><th className="p-3 font-semibold">Student</th><th className="p-3 font-semibold">Course</th><th className="p-3 font-semibold">Risk</th><th className="p-3 font-semibold">Main reason</th></tr></thead>
                <tbody>
                  {rows.slice(0, 100).map((r) => {
                    const name = displayName(people, r)
                    return (
                      <tr key={r.id} tabIndex={0} onClick={() => setOpen({ key: r.student_id ?? r.external_student_ref_hash ?? r.student_ref, name })} onKeyDown={(e) => e.key === 'Enter' && setOpen({ key: r.student_id ?? r.student_ref, name })} className="cursor-pointer border-b border-line/60 hover:bg-sunken/60 focus:bg-sunken/60 focus:outline-none">
                        <td className="p-3 font-semibold">{name}</td>
                        <td className="p-3 text-ink-2">{r.course_id}</td>
                        <td className="p-3"><span className="flex items-center gap-2"><TierBadge tier={r.tier} /><span className="font-semibold tabular-nums">{pct(r.probability)}</span><Direction d={r.direction} /></span></td>
                        <td className="max-w-[320px] truncate p-3 text-ink-2">{r.reasons?.[0]?.text ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              {rows.length > 100 && <p className="p-3 text-center text-[11px] text-muted">Showing the first 100 of {rows.length}. Search to narrow down.</p>}
            </div>
          )
        }}
      </QueryState>
      <StudentInsightDrawer studentKey={open?.key ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}
