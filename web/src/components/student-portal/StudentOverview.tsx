import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { usePulseStatus, usePulseTrends, useSupportRequests, useStudentAcademics, useStudentAttendance } from '../../lib/api/endpoints/student.hooks'
import { checkInRanges, wellbeingWord } from '../../lib/labels'
import { CheckCircle2, TrendingUp, BookOpen, Clock, HeartHandshake } from 'lucide-react'

export function StudentOverview({ onCheckIn }: { onCheckIn: () => void }) {
  const status = usePulseStatus()
  const trends = usePulseTrends()
  const academics = useStudentAcademics()
  const attendance = useStudentAttendance()
  const reqs = useSupportRequests()

  return (
    <div className="mt-3 flex flex-col gap-4 font-sans">
      {/* Check-in section */}
      <section className="rounded-3xl border border-line bg-white p-5 text-xs shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HeartHandshake className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-bold text-gray-900">This week's wellbeing check-in</h2>
          </div>
        </div>
        <QueryState query={status} empty={<EmptyState title="No check-in this week" message="Come back when the next one opens." />}>
          {(s) =>
            s.completed ? (
              <div className="mt-3 flex items-center gap-2 text-emerald-700 bg-emerald-50 px-3.5 py-2.5 rounded-xl border border-emerald-100">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span className="font-medium">You have done this week's check-in. Thank you!</span>
              </div>
            ) : (
              <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-purple-50 p-4 rounded-2xl border border-purple-100">
                <div>
                  <p className="font-semibold text-purple-950 text-xs">A new check-in is waiting for you</p>
                  <p className="text-xs text-purple-700 mt-0.5">
                    Takes about 2 minutes. It helps your teachers support you better.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={onCheckIn}
                  className="px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white font-bold rounded-xl shadow-xs transition shrink-0"
                >
                  Start check-in
                </button>
              </div>
            )
          }
        </QueryState>
      </section>

      {/* Wellbeing trend section */}
      <section className="rounded-3xl border border-line bg-white p-5 text-xs shadow-xs">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-4 h-4 text-blue-600" />
          <h2 className="text-sm font-bold text-gray-900">Wellbeing trend</h2>
        </div>
        <QueryState query={trends} empty={<EmptyState title="No check-ins yet" message="Take a check-in to see how you are doing over time." />}>
          {(pts) => {
            const scored = pts.filter((p) => !p.suppressed && p.index_score != null)
            const first = scored[0]?.index_score ?? null
            const last = scored[scored.length - 1]?.index_score ?? null
            const delta = first != null && last != null ? Math.round(last - first) : null
            const verdict =
              last == null ? '' : last >= 75 ? 'You are doing well' : last >= 60 ? 'You are doing fine' : last >= 45 ? 'Things look a bit hard lately' : 'You may need some support'
            const trend = delta == null || Math.abs(delta) < 3 ? 'steady' : delta > 0 ? `up ${delta} points` : `down ${Math.abs(delta)} points`
            const ranges = checkInRanges(pts)
            return (
              <div className="mt-2">
                {last != null && (
                  <p className="text-sm text-gray-800">
                    <span className="font-bold">{verdict}.</span> Your latest score is {Math.round(last)} out of 100 ({wellbeingWord(last).toLowerCase()}), {trend} since your first check-in.
                  </p>
                )}
                <div className="mt-4 flex items-end gap-2 sm:gap-3 h-32" role="img" aria-label="Wellbeing score for each check-in">
                  {pts.map((p) => {
                    const v = p.suppressed || p.index_score == null ? null : Math.round(p.index_score)
                    return (
                      <div key={p.period_id} className="flex-1 flex flex-col items-center justify-end h-full" title={v == null ? 'Not enough answers to show' : `${v} out of 100: ${wellbeingWord(v)}`}>
                        <span className="text-xs font-bold text-gray-800 mb-1">{v ?? '–'}</span>
                        <div
                          className={`w-full rounded-t-md ${v == null ? 'bg-gray-200' : v >= 75 ? 'bg-emerald-500' : v >= 60 ? 'bg-teal-400' : v >= 45 ? 'bg-amber-400' : 'bg-rose-500'}`}
                          style={{ height: `${v == null ? 6 : Math.max(8, v)}%` }}
                        />
                      </div>
                    )
                  })}
                </div>
                <div className="mt-1.5 flex gap-2 sm:gap-3">
                  {pts.map((p, i) => (
                    <div key={p.period_id} className="flex-1 text-center leading-tight">
                      <p className="text-[11px] font-semibold text-gray-700">Check-in {i + 1}</p>
                      <p className="text-[10px] text-gray-500">{ranges[i]}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-gray-600">
                  <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-emerald-500" />75+ Doing well</span>
                  <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-teal-400" />60 to 74 Doing fine</span>
                  <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-amber-400" />45 to 59 Hard lately</span>
                  <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-rose-500" />Under 45 Needs support</span>
                </div>
                <p className="mt-2 text-[11px] text-gray-500">Each bar is one check-in. A higher number is better. Only you can see this.</p>
              </div>
            )
          }}
        </QueryState>
      </section>

      {/* Support Requests & Academic Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 text-xs">
        <section className="rounded-3xl border border-line bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <HeartHandshake className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-gray-900">Your help requests</h2>
          </div>
          <QueryState query={reqs} empty={<EmptyState title="No open requests" message="Use Ask for help if you need anything." />}>
            {(r) => (
              <div>
                <p className="mt-1 text-2xl font-bold text-gray-900">{r.length}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Requests you have made for help.
                </p>
              </div>
            )}
          </QueryState>
        </section>

        <section className="rounded-3xl border border-line bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-gray-900">Grades and attendance</h2>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2.5 bg-gray-50 rounded-xl">
              <span className="text-xs text-gray-500">Grade average</span>
              <QueryState query={academics} empty={<p className="text-sm font-bold text-gray-700 mt-0.5">—</p>}>
                {(a) => <p className="text-sm font-bold text-gray-800 mt-0.5">{a?.cgpa ?? a?.gpa ?? 'Good'}</p>}
              </QueryState>
            </div>
            <div className="p-2.5 bg-gray-50 rounded-xl">
              <span className="text-xs text-gray-500">Attendance</span>
              <QueryState query={attendance} empty={<p className="text-sm font-bold text-gray-700 mt-0.5">—</p>}>
                {(att) => (
                  <p className="text-sm font-bold text-gray-800 mt-0.5">
                    {att?.overall_percentage ? `${Math.round(att.overall_percentage)}%` : 'Regular'}
                  </p>
                )}
              </QueryState>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
