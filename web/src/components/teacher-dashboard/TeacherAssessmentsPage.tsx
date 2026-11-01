import React, { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Plus } from 'lucide-react'
import { api } from '../../lib/api/client'
import { errorMessage } from '../../lib/api/errors'
import { QueryState, EmptyState, LoadingSkeleton } from '../common/QueryState'
import { Button, Card, Tabs } from '../common/ui'
import { useFacultySections, useSectionStudents } from '../../lib/api/endpoints/faculty.hooks'

interface Gradebook {
  section_id: string
  assessments: { id: string; title: string; total_marks: number }[]
  gradebook: { student_id: string; student_name: string; student_uid: string; scores: Record<string, number>; average: number | null }[]
}
type Status = 'Present' | 'Late' | 'Absent'
const STATUSES: Status[] = ['Present', 'Late', 'Absent']
const STATUS_TONE: Record<Status, string> = { Present: 'bg-tier-ok text-white', Late: 'bg-tier-watch text-white', Absent: 'bg-tier-high text-white' }

function Attendance({ sectionId }: { sectionId: string }) {
  const students = useSectionStudents([sectionId])[0]
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [marks, setMarks] = useState<Record<string, Status>>({})
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const save = useMutation({
    mutationFn: async () => {
      const entries = Object.entries(marks)
      for (const [student_id, status] of entries) await api.post('/api/v1/faculty/attendance', { section_id: sectionId, student_id, date, status })
      return entries.length
    },
    onSuccess: (n) => setMsg({ ok: true, text: `Saved attendance for ${n} students.` }),
    onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
  })
  useEffect(() => { setMarks({}); setMsg(null) }, [sectionId, date])
  return (
    <Card title="Mark attendance" action={
      <div className="flex items-center gap-2">
        <input type="date" value={date} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} aria-label="Class date" className="rounded-md border border-line bg-panel px-2 py-1 text-xs" />
        <Button variant="ghost" onClick={() => setMarks(Object.fromEntries((students.data ?? []).map((s) => [s.id, 'Present'])))}>All present</Button>
      </div>
    }>
      <QueryState query={students} empty={<EmptyState title="No students in this section" />}>
        {(rows) => (
          <>
            <ul className="divide-y divide-line">
              {rows.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-xs">
                  <span><span className="font-semibold">{s.full_name}</span> <span className="text-muted">{s.student_uid}</span></span>
                  <span className="flex gap-1" role="group" aria-label={`Attendance for ${s.full_name}`}>
                    {STATUSES.map((st) => (
                      <button key={st} type="button" aria-pressed={marks[s.id] === st} onClick={() => setMarks((m) => ({ ...m, [s.id]: st }))} className={`rounded px-2.5 py-1 font-semibold ${marks[s.id] === st ? STATUS_TONE[st] : 'bg-sunken text-ink-2 hover:bg-line'}`}>{st}</button>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex items-center gap-3">
              <Button onClick={() => { setMsg(null); save.mutate() }} disabled={save.isPending || Object.keys(marks).length === 0}>{save.isPending ? 'Saving…' : `Save ${Object.keys(marks).length || ''} marks`}</Button>
              {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-tier-ok' : 'text-tier-high'}`}>{msg.text}</p>}
            </div>
          </>
        )}
      </QueryState>
    </Card>
  )
}

function ScoreCell({ value, max, onSave }: { value?: number; max: number; onSave: (v: number) => Promise<unknown> }) {
  const [v, setV] = useState(value != null ? String(value) : '')
  const [state, setState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  useEffect(() => setV(value != null ? String(value) : ''), [value])
  const commit = async () => {
    const n = Number(v)
    if (v === '' || Number.isNaN(n) || n === value || n < 0 || n > max) return
    setState('saving')
    try { await onSave(n); setState('saved') } catch { setState('error') }
  }
  return (
    <span className="relative inline-flex items-center">
      <input value={v} onChange={(e) => { setV(e.target.value); setState('idle') }} onBlur={commit} onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()} inputMode="decimal" aria-label="Score" className={`w-14 rounded border bg-panel px-1.5 py-1 text-right text-xs tabular-nums ${state === 'error' ? 'border-tier-high' : 'border-line'}`} />
      {state === 'saved' && <Check className="absolute -right-4 h-3.5 w-3.5 text-tier-ok" />}
    </span>
  )
}

function Gradebook({ sectionId }: { sectionId: string }) {
  const qc = useQueryClient()
  const gb = useQuery({ queryKey: ['faculty', 'gradebook', sectionId], queryFn: ({ signal }) => api.get<Gradebook>(`/api/v1/faculty/gradebook/${sectionId}`, { signal }) })
  const [form, setForm] = useState({ title: '', assessment_type: 'quiz', total_marks: '20' })
  const [err, setErr] = useState<string | null>(null)
  const create = useMutation({
    mutationFn: () => api.post('/api/v1/faculty/assessments', { section_id: sectionId, title: form.title, assessment_type: form.assessment_type, total_marks: Number(form.total_marks) }),
    onSuccess: () => { setForm((f) => ({ ...f, title: '' })); void qc.invalidateQueries({ queryKey: ['faculty', 'gradebook', sectionId] }) },
    onError: (e) => setErr(errorMessage(e)),
  })
  const saveMark = useMutation({
    mutationFn: (v: { assessment_id: string; student_id: string; score: number }) => api.post('/api/v1/faculty/marks', v),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['faculty', 'gradebook', sectionId] }),
  })
  return (
    <div className="flex flex-col gap-4">
      <Card title="New assessment" tip="Creates a column in the gradebook. Then type marks straight into the cells.">
        <form onSubmit={(e) => { e.preventDefault(); setErr(null); create.mutate() }} className="flex flex-wrap items-end gap-3 text-xs">
          <label className="flex flex-col gap-1 font-semibold text-ink-2">Title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-56 rounded-md border border-line bg-panel px-3 py-2 font-normal" /></label>
          <label className="flex flex-col gap-1 font-semibold text-ink-2">Type<select value={form.assessment_type} onChange={(e) => setForm({ ...form, assessment_type: e.target.value })} className="rounded-md border border-line bg-panel px-3 py-2 font-normal">{['quiz', 'assignment', 'midterm', 'final', 'project'].map((t) => <option key={t}>{t}</option>)}</select></label>
          <label className="flex flex-col gap-1 font-semibold text-ink-2">Out of<input required value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: e.target.value.replace(/[^\d.]/g, '') })} className="w-20 rounded-md border border-line bg-panel px-3 py-2 font-normal" /></label>
          <Button type="submit" disabled={create.isPending || !form.title}><Plus className="h-3.5 w-3.5" /> Add</Button>
          {err && <p role="alert" className="text-tier-high">{err}</p>}
        </form>
      </Card>
      <Card title="Gradebook">
        <QueryState query={gb} isEmpty={(d) => !d.gradebook.length} empty={<EmptyState title="No students in this section" />}>
          {(d) => (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-xs">
                <thead><tr className="border-b border-line text-xs text-muted"><th className="p-2 font-semibold">Student</th>{d.assessments.map((a) => <th key={a.id} className="p-2 text-right font-semibold">{a.title.replace(/^[A-Z]{2,3}\d+\s/, '')}<span className="block font-normal">/ {a.total_marks}</span></th>)}<th className="p-2 text-right font-semibold">Average</th></tr></thead>
                <tbody>
                  {d.gradebook.map((r) => (
                    <tr key={r.student_id} className="border-b border-line/60">
                      <td className="p-2"><span className="font-semibold">{r.student_name}</span> <span className="text-muted">{r.student_uid}</span></td>
                      {d.assessments.map((a) => <td key={a.id} className="p-2 text-right"><ScoreCell value={r.scores[a.id]} max={a.total_marks} onSave={(score) => saveMark.mutateAsync({ assessment_id: a.id, student_id: r.student_id, score })} /></td>)}
                      <td className="p-2 text-right font-semibold tabular-nums">{r.average != null ? `${Math.round(r.average)}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </QueryState>
      </Card>
    </div>
  )
}

/** Faculty classroom tools: attendance and marks, against the real faculty endpoints. */
export function TeacherAssessmentsPage() {
  const sections = useFacultySections()
  const [sectionId, setSectionId] = useState<string>('')
  const [tab, setTab] = useState<'attendance' | 'grades'>('grades')
  useEffect(() => { if (!sectionId && sections.data?.length) setSectionId(sections.data[0].id) }, [sections.data, sectionId])
  const current = useMemo(() => sections.data?.find((s) => s.id === sectionId), [sections.data, sectionId])
  return (
    <main className="flex min-w-0 flex-1 flex-col gap-4 p-4 font-sans sm:p-6 lg:px-8 lg:py-6">
      <h1 className="font-display text-[34px] leading-tight tracking-tight">Classroom</h1>
      <QueryState query={sections} empty={<EmptyState title="No sections assigned to you" />} loading={<LoadingSkeleton rows={1} />}>
        {(rows) => (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <select value={sectionId} onChange={(e) => setSectionId(e.target.value)} aria-label="Section" className="rounded-md border border-line bg-panel px-3 py-2 text-xs font-semibold">
                {rows.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              <Tabs value={tab} onChange={setTab} items={[{ id: 'grades', label: 'Marks' }, { id: 'attendance', label: 'Attendance' }]} />
            </div>
            {current && (tab === 'attendance' ? <Attendance sectionId={current.id} /> : <Gradebook sectionId={current.id} />)}
          </>
        )}
      </QueryState>
    </main>
  )
}
