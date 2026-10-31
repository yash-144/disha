import React, { useMemo, useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { useFacultySections, useSectionStudents, useTierByStudent } from '../../lib/api/endpoints/faculty.hooks'
import type { SectionStudent } from '../../lib/api/endpoints/faculty'

function Directory({ sectionIds }: { sectionIds: string[] }) {
  const results = useSectionStudents(sectionIds)
  const tiers = useTierByStudent()
  const [q, setQ] = useState('')
  const students = useMemo(() => {
    const seen = new Map<string, SectionStudent>()
    results.forEach((r) => r.data?.forEach((s) => seen.set(s.id, s)))
    return [...seen.values()].filter((s) => s.full_name.toLowerCase().includes(q.toLowerCase()))
  }, [results, q])
  if (results.some((r) => r.isPending)) return <p className="text-xs">Loading...</p>
  const failed = results.find((r) => r.isError)
  if (failed) return <p role="alert" className="text-xs text-red-600">Could not load students.</p>
  return (
    <div className="flex flex-col gap-3">
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search students" className="w-64 rounded-lg border border-gray-200 px-3 py-1.5 text-xs" />
      {students.length === 0 ? (
        <EmptyState title="No students found" />
      ) : (
        <table className="w-full rounded-2xl bg-white text-left text-xs">
          <thead><tr className="text-[#717E95]"><th className="p-2">Name</th><th>Department</th><th>Attendance</th><th>Risk tier</th></tr></thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id} className="border-t border-gray-100">
                <td className="p-2">{s.full_name}</td>
                <td>{s.department ?? ''}</td>
                <td>{s.attendance_rate != null ? `${Math.round(s.attendance_rate)}%` : ''}</td>
                <td>{tiers.data?.[s.id] ?? 'Not scored'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export function StudentDirectoryPage() {
  const sections = useFacultySections()
  return (
    <main className="flex-1 p-4 font-sans">
      <h1 className="mb-3 text-lg font-bold text-[#1E2433]">Student Directory</h1>
      <QueryState query={sections} empty={<EmptyState title="No sections assigned" />}>
        {(rows) => <Directory sectionIds={rows.map((s) => s.id)} />}
      </QueryState>
    </main>
  )
}
