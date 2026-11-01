import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { usePulseStatus, usePulseTrends, useSupportRequests, useStudentAcademics, useStudentAttendance } from '../../lib/api/endpoints/student.hooks'
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
        <QueryState query={status} empty={<EmptyState title="No open check-in" />}>
          {(s) =>
            s.completed ? (
              <div className="mt-3 flex items-center gap-2 text-emerald-700 bg-emerald-50 px-3.5 py-2.5 rounded-xl border border-emerald-100">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span className="font-medium">Check-in recorded for this period. Thank you for sharing!</span>
              </div>
            ) : (
              <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-purple-50 p-4 rounded-2xl border border-purple-100">
                <div>
                  <p className="font-semibold text-purple-950 text-xs">A new pulse check-in is waiting for you</p>
                  <p className="text-xs text-purple-700 mt-0.5">
                    Takes less than 2 minutes and helps your advisors provide tailored academic support.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={onCheckIn}
                  className="px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white font-bold rounded-xl shadow-xs transition shrink-0"
                >
                  Take Check-in
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
        <QueryState query={trends} empty={<EmptyState title="No trend data yet" />}>
          {(pts) => (
            <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
              {pts.map((p) => (
                <div key={p.period_id} className="p-3 bg-gray-50 rounded-xl border border-line">
                  <p className="text-xs text-gray-500 font-medium">{p.label}</p>
                  <p className="text-base font-bold text-gray-800 mt-1">
                    {p.suppressed || p.index_score == null
                      ? 'Aggregated'
                      : `${Math.round(p.index_score)} / 100`}
                  </p>
                </div>
              ))}
            </div>
          )}
        </QueryState>
      </section>

      {/* Support Requests & Academic Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 text-xs">
        <section className="rounded-3xl border border-line bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <HeartHandshake className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-gray-900">Support requests</h2>
          </div>
          <QueryState query={reqs} empty={<EmptyState title="No active support requests" />}>
            {(r) => (
              <div>
                <p className="mt-1 text-2xl font-bold text-gray-900">{r.length}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Active academic & consultation requests with your mentors.
                </p>
              </div>
            )}
          </QueryState>
        </section>

        <section className="rounded-3xl border border-line bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-gray-900">Academic & Attendance</h2>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2.5 bg-gray-50 rounded-xl">
              <span className="text-xs text-gray-500">CGPA / GPA</span>
              <QueryState query={academics} empty={<p className="text-sm font-bold text-gray-700 mt-0.5">—</p>}>
                {(a) => <p className="text-sm font-bold text-gray-800 mt-0.5">{a?.cgpa ?? a?.gpa ?? 'Good standing'}</p>}
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
