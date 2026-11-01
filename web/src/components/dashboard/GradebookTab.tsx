import React from 'react'
import {
  TrendingUp,
  Award,
  Users,
  Download,
  BarChart3,
  CheckCircle,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function GradebookTab() {
  const { students, addToast } = useApp()

  const averageScore = Math.round(
    students.reduce((acc, curr) => acc + curr.quizScore, 0) / (students.length || 1)
  )

  const gradeDistribution = [
    { grade: 'A+ (90-100%)', count: 3, percentage: '50%', color: 'bg-[#0f9d58]' },
    { grade: 'A (80-89%)', count: 2, percentage: '33%', color: 'bg-brand' },
    { grade: 'B (70-79%)', count: 1, percentage: '17%', color: 'bg-amber-500' },
    { grade: 'Needs Review', count: 0, percentage: '0%', color: 'bg-red-400' },
  ]

  const downloadReport = () => {
    addToast('Report Exported', 'Official cohort performance ledger downloaded.', 'success')
  }

  return (
    <div className="space-y-6 font-mono">
      <div className="flex flex-wrap items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              ASSESSMENT ANALYTICS
            </span>
            <span className="text-xs text-muted">(Term July-Aug)</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Gradebook &amp; Performance Ledger</h2>
        </div>

        <button
          onClick={downloadReport}
          className="flex items-center gap-1.5 border-2 border-ink bg-[#0f9d58] px-4 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
        >
          <Download className="h-4 w-4" /> Export Analytics CSV
        </button>
      </div>

      {/* Top Analytics Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-muted">Cohort Average Score</p>
          <p className="mt-1 text-2xl font-bold text-brand">{averageScore}%</p>
          <span className="mt-1 inline-flex items-center gap-1 text-[10px] text-[#0f9d58] font-bold">
            <TrendingUp className="h-3 w-3" /> +4.2% vs last term
          </span>
        </div>

        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-muted">Assessment Pass Rate</p>
          <p className="mt-1 text-2xl font-bold text-[#0f9d58]">96.8%</p>
          <span className="mt-1 text-[10px] text-gray-500 font-bold">6 Milestones evaluated</span>
        </div>

        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-muted">PRs &amp; Labs Graded</p>
          <p className="mt-1 text-2xl font-bold text-ink">142</p>
          <span className="mt-1 text-[10px] text-[#0f9d58] font-bold">All cohorts updated</span>
        </div>

        <div className="border-2 border-ink bg-white p-4 shadow-[3px_3px_0_#0d1b3e]">
          <p className="text-[11px] font-bold text-muted">Top Cohort Performer</p>
          <p className="mt-1 text-base font-bold text-ink truncate">Tanvi Verma</p>
          <span className="mt-1 inline-block border border-ink bg-[#0f9d58]/20 px-1 text-[9px] text-emerald-800 font-bold">
            98% Avg GPA
          </span>
        </div>
      </div>

      {/* Visual Grade Distribution Bar Charts */}
      <div className="border-2 border-ink bg-white p-5 shadow-[4px_4px_0_#0d1b3e]">
        <h3 className="text-sm font-bold text-ink flex items-center gap-2 border-b-2 border-ink/10 pb-3">
          <BarChart3 className="h-4 w-4 text-brand" /> Benchmark Grade Distribution
        </h3>

        <div className="mt-4 space-y-3.5">
          {gradeDistribution.map((d) => (
            <div key={d.grade} className="space-y-1">
              <div className="flex justify-between text-xs font-bold text-ink">
                <span>{d.grade}</span>
                <span>
                  {d.count} learners ({d.percentage})
                </span>
              </div>
              <div className="h-3 w-full border border-ink bg-gray-100 overflow-hidden">
                <div
                  className={`h-full ${d.color} transition-all duration-500`}
                  style={{ width: d.percentage }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Individual Student Scores Table */}
      <div className="border-2 border-ink bg-white shadow-[4px_4px_0_#0d1b3e] overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b-2 border-ink bg-[#f5f7fc] text-[11px] text-ink uppercase">
            <tr>
              <th className="p-3 font-bold">Learner Name</th>
              <th className="p-3 font-bold">Attendance</th>
              <th className="p-3 font-bold">Quiz Score</th>
              <th className="p-3 font-bold">Capstones</th>
              <th className="p-3 font-bold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/10">
            {students.map((s) => (
              <tr key={s.id} className="hover:bg-blue-50/40">
                <td className="p-3 font-bold text-ink">{s.name}</td>
                <td className="p-3 font-bold text-brand">{s.attendanceRate}%</td>
                <td className="p-3 font-bold text-[#0f9d58]">{s.quizScore}%</td>
                <td className="p-3 text-gray-600 font-bold">3 of 3 Passed</td>
                <td className="p-3">
                  <span className="border border-ink bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                    CERTIFIED
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
