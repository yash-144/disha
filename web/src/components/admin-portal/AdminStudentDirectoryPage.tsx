import React, { useMemo, useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useInvitations, useInvite, useMemberships } from '../../lib/api/endpoints/admin.hooks'
import { buildPeopleIndex, displayName, useAllCases, useAllScores, type ScoreRow } from '../../lib/api/endpoints/risk'
import { Button, Card, Direction, SearchInput, Tabs, TierBadge, TIERS, TIER_STYLE, pct, pretty, fmtDate, type Tier } from '../common/ui'
import { StudentInsightDrawer } from './StudentInsightDrawer'
import { roleLabel } from '../../lib/auth/portals'

const RANK: Record<string, number> = { ON_TRACK: 0, WATCH: 1, MEDIUM: 2, HIGH: 3 }

interface StudentRow {
  key: string
  id: string
  ref: string
  name: string
  hasName: boolean
  department: string | null
  courses: ScoreRow[]
  worst: ScoreRow
}

function Students() {
  const scores = useAllScores()
  const cases = useAllCases()
  const [search, setSearch] = useState('')
  const [tier, setTier] = useState<'ALL' | Tier>('ALL')
  const [open, setOpen] = useState<StudentRow | null>(null)
  const people = useMemo(() => buildPeopleIndex(cases.data), [cases.data])

  const rows = useMemo<StudentRow[]>(() => {
    const by = new Map<string, ScoreRow[]>()
    for (const r of scores.data?.items ?? []) {
      const k = r.student_id ?? r.student_ref
      by.set(k, [...(by.get(k) ?? []), r])
    }
    return [...by.entries()].map(([k, list]) => {
      const worst = [...list].sort((a, b) => b.probability - a.probability)[0]
      const nm = displayName(people, worst)
      return { key: k, id: worst.student_id ?? worst.external_student_ref_hash ?? worst.student_ref, ref: worst.student_ref, name: nm, hasName: nm !== worst.student_ref, department: people.get(k)?.department ?? null, courses: list, worst }
    })
  }, [scores.data, people])

  const filtered = rows.filter((r) => (tier === 'ALL' || r.worst.tier === tier) && (!search || `${r.name} ${r.ref} ${r.department ?? ''} ${r.courses.map((c) => c.course_id).join(' ')}`.toLowerCase().includes(search.toLowerCase())))
  const tierCounts = Object.fromEntries(TIERS.map((t) => [t, rows.filter((r) => r.worst.tier === t).length])) as Record<Tier, number>

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Search name, ID or course" />
        <div className="flex flex-wrap gap-1.5 text-xs">
          <button type="button" onClick={() => setTier('ALL')} className={`rounded-full border px-3 py-1.5 font-semibold ${tier === 'ALL' ? 'border-ink bg-ink text-white' : 'border-line bg-white text-ink-2'}`}>All {rows.length}</button>
          {TIERS.map((t) => (
            <button key={t} type="button" onClick={() => setTier(t)} className={`rounded-full border px-3 py-1.5 font-semibold ${tier === t ? 'border-ink bg-ink text-white' : `${TIER_STYLE[t].chip}`}`}>{TIER_STYLE[t].label} {tierCounts[t]}</button>
          ))}
        </div>
      </div>
      <QueryState query={scores} isEmpty={(d) => !d.items.length} empty={<EmptyState title="No students scored yet" message="Import data and run the risk model first." />}>
        {() => (
          <div className="overflow-x-auto rounded-2xl border border-line bg-white">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead>
                <tr className="border-b border-line text-[10px] uppercase tracking-wider text-muted">
                  <th className="p-3 font-bold">Student</th>
                  <th className="p-3 font-bold">Department</th>
                  <th className="p-3 font-bold">Courses</th>
                  <th className="p-3 font-bold">Highest risk</th>
                  <th className="p-3 font-bold">Main reason</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 100).map((r) => (
                  <tr key={r.key} tabIndex={0} onClick={() => setOpen(r)} onKeyDown={(e) => e.key === 'Enter' && setOpen(r)} className="cursor-pointer border-b border-gray-50 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none">
                    <td className="p-3"><p className="font-bold text-ink">{r.name}</p>{r.hasName && <p className="text-[10px] text-muted">{r.ref}</p>}</td>
                    <td className="p-3 text-ink-2">{r.department ?? '—'}</td>
                    <td className="p-3 text-ink-2">{r.courses.length}</td>
                    <td className="p-3"><span className="flex items-center gap-2"><TierBadge tier={r.worst.tier} /><span className="font-bold tabular-nums">{pct(r.worst.probability)}</span><Direction d={r.worst.direction} /></span></td>
                    <td className="max-w-[260px] truncate p-3 text-ink-2">{r.worst.reasons?.[0]?.text ?? 'No concerns'}</td>
                  </tr>
                ))}
                {filtered.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-muted">No students match.</td></tr>}
              </tbody>
            </table>
            {filtered.length > 100 && <p className="p-3 text-center text-[11px] text-muted">Showing the first 100 of {filtered.length}. Search to narrow down.</p>}
          </div>
        )}
      </QueryState>
      <StudentInsightDrawer studentKey={open?.id ?? null} name={open?.name} onClose={() => setOpen(null)} />
    </div>
  )
}

function Team() {
  const members = useMemberships()
  const invites = useInvitations()
  const invite = useInvite()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('student')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const send = () => {
    setMsg(null)
    invite.mutate({ email, role, expires_in_days: 14 }, {
      onSuccess: () => { setMsg({ ok: true, text: `Invitation created for ${email}.` }); setEmail('') },
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  return (
    <div className="flex flex-col gap-4 text-xs">
      <Card title="Invite someone" tip="They get access with this role the first time they sign in with Google using this email.">
        <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 font-semibold text-ink-2">Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required className="w-64 rounded-lg border border-line px-3 py-2 font-normal outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100" />
          </label>
          <label className="flex flex-col gap-1 font-semibold text-ink-2">Role
            <select value={role} onChange={(e) => setRole(e.target.value)} className="rounded-lg border border-line px-3 py-2 font-normal">
              {['student', 'faculty', 'mentor', 'counsellor', 'hod', 'institution_admin'].map((r) => <option key={r} value={r}>{roleLabel(r)}</option>)}
            </select>
          </label>
          <Button type="submit" disabled={!email || invite.isPending}>{invite.isPending ? 'Sending…' : 'Invite'}</Button>
          {msg && <p role={msg.ok ? 'status' : 'alert'} className={msg.ok ? 'text-emerald-700' : 'text-rose-600'}>{msg.text}</p>}
        </form>
      </Card>
      <Card title="People with access">
        <QueryState query={members} empty={<EmptyState title="No members" />}>
          {(rows) => (
            <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left">
              <thead><tr className="text-[10px] uppercase tracking-wider text-muted"><th className="p-2">Name</th><th>Email</th><th>Role</th><th>Department</th><th>Status</th></tr></thead>
              <tbody>
                {rows.map((m) => (
                  <tr key={m.membership_id} className="border-t border-line"><td className="p-2 font-semibold">{m.full_name}</td><td>{m.email}</td><td>{roleLabel(m.role)}</td><td>{m.department ?? '—'}</td><td>{m.is_active ? 'Active' : 'Inactive'}</td></tr>
                ))}
              </tbody>
            </table></div>
          )}
        </QueryState>
      </Card>
      <Card title="Invitations">
        <QueryState query={invites} empty={<EmptyState title="No invitations yet" />}>
          {(rows) => (
            <ul className="divide-y divide-line">
              {rows.map((i) => <li key={i.id} className="flex justify-between gap-2 py-2"><span>{i.email} <span className="text-muted">({roleLabel(i.role)})</span></span><span className="text-muted">{pretty(String(i.status))}</span></li>)}
            </ul>
          )}
        </QueryState>
      </Card>
    </div>
  )
}

export function AdminStudentDirectoryPage() {
  const [tab, setTab] = useState<'students' | 'team'>('students')
  return (
    <div className="flex flex-col gap-4 font-sans">
      <Tabs value={tab} onChange={setTab} items={[{ id: 'students', label: 'Students' }, { id: 'team', label: 'Staff & access' }]} />
      {tab === 'students' ? <Students /> : <Team />}
    </div>
  )
}
