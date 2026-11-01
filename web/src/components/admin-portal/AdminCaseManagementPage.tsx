import React, { useMemo, useState } from 'react'
import { AlertTriangle, ChevronRight } from 'lucide-react'
import { QueryState, EmptyState } from '../common/QueryState'
import { CaseDetailDrawer } from '../common/CaseDetailDrawer'
import { Pill, SearchInput, Tabs, fmtDate } from '../common/ui'
import { priorityLabel, stageLabel, studentName } from '../../lib/labels'
import { useAllCases } from '../../lib/api/endpoints/risk'

const CLOSED = ['closed', 'dismissed']
const PRIORITY: Record<string, string> = { urgent: 'bg-rose-50 text-rose-700', critical: 'bg-rose-50 text-rose-700', high: 'bg-orange-50 text-orange-700', medium: 'bg-amber-50 text-amber-700', low: 'bg-sunken text-ink-2' }
type Filter = 'open' | 'unassigned' | 'overdue' | 'closed' | 'all'
const FILTER_LABEL: Record<Filter, string> = { open: 'Open', unassigned: 'No owner yet', overdue: 'Overdue', closed: 'Resolved', all: 'All' }

export function AdminCaseManagementPage() {
  const q = useAllCases()
  const [selected, setSelected] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('open')
  const [search, setSearch] = useState('')

  const rows = useMemo(() => {
    const list = q.data ?? []
    return list.filter((c) => {
      const open = !CLOSED.includes(c.state)
      const ok = filter === 'all' ? true : filter === 'open' ? open : filter === 'unassigned' ? open && !c.owner_name : filter === 'overdue' ? open && c.is_overdue : !open
      return ok && (!search || `${c.student_name ?? ''} ${c.student_ref ?? ''} ${c.owner_name ?? ''} ${c.department ?? ''}`.toLowerCase().includes(search.toLowerCase()))
    })
  }, [q.data, filter, search])
  const n = (f: Filter) => (q.data ?? []).filter((c) => (f === 'open' ? !CLOSED.includes(c.state) : f === 'unassigned' ? !CLOSED.includes(c.state) && !c.owner_name : f === 'overdue' ? !CLOSED.includes(c.state) && c.is_overdue : f === 'closed' ? CLOSED.includes(c.state) : true)).length

  return (
    <div className="flex flex-col gap-3 font-sans">
      <div className="flex flex-wrap items-center gap-3">
        <Tabs value={filter} onChange={setFilter} items={(['open', 'unassigned', 'overdue', 'closed', 'all'] as Filter[]).map((f) => ({ id: f, label: `${FILTER_LABEL[f]} ${q.data ? n(f) : ''}` }))} />
        <SearchInput value={search} onChange={setSearch} placeholder="Search by student or owner" />
      </div>
      <QueryState query={q} empty={<EmptyState title="No cases yet" message="Cases appear when the weekly check flags a student or a student asks for help." />}>
        {() =>
          rows.length === 0 ? (
            <EmptyState title="No cases match" />
          ) : (
            <div className="overflow-x-auto rounded-lg border border-line bg-panel">
              <table className="w-full min-w-[680px] text-left text-xs">
                <thead><tr className="border-b border-line text-xs text-muted"><th className="p-3 font-semibold">Student</th><th className="p-3 font-semibold">Where it stands</th><th className="p-3 font-semibold">Priority</th><th className="p-3 font-semibold">Owner</th><th className="p-3 font-semibold">Due</th><th /></tr></thead>
                <tbody>
                  {rows.map((c) => (
                    <tr key={c.id} tabIndex={0} onClick={() => setSelected(c.id)} onKeyDown={(e) => e.key === 'Enter' && setSelected(c.id)} className="cursor-pointer border-b border-line/60 hover:bg-sunken/60 focus:bg-sunken/60 focus:outline-none">
                      <td className="p-3"><p className="font-semibold">{studentName(c.student_name, c.student_ref)}</p>{(c.department || (c.student_name && c.student_ref)) && <p className="text-xs text-muted">{[c.student_name && c.student_ref ? `Student ${c.student_ref}` : '', c.department].filter(Boolean).join(' · ')}</p>}</td>
                      <td className="p-3">{stageLabel(c.state)}</td>
                      <td className="p-3"><Pill tone={PRIORITY[c.priority] ?? PRIORITY.low}>{priorityLabel(c.priority)}</Pill></td>
                      <td className="p-3">{c.owner_name ?? <span className="text-tier-medium">No owner yet</span>}</td>
                      <td className="p-3 tabular-nums">{c.is_overdue ? <span className="flex items-center gap-1 font-semibold text-tier-high"><AlertTriangle className="h-3 w-3" /> Overdue</span> : fmtDate(c.due_at)}</td>
                      <td className="p-3 text-right text-accent"><ChevronRight className="inline h-4 w-4" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </QueryState>
      {selected && <CaseDetailDrawer caseId={selected} onClose={() => setSelected(null)} userRole="admin" />}
    </div>
  )
}
