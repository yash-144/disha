import React, { useState } from 'react'
import {
  BarChart3,
  TrendingUp,
  Download,
  Filter,
  ShieldAlert,
  Info,
  Calendar,
  Layers,
  CheckCircle2,
  PieChart,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function AdminAnalyticsPage() {
  const { addToast } = useApp()
  const [selectedCohort, setSelectedCohort] = useState('all')
  const [isSuppressionActive, setIsSuppressionActive] = useState(true)

  const handleExportReport = () => {
    addToast('Report Generated', 'Apex University Term 1 Analytics Report exported as PDF.', 'success')
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. ANALYTICS WORKSPACE HEADER */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Institutional Analytics &amp; Outcomes Reporting
            </h2>
            <p className="text-xs text-[#717E95]">
              Computed cohort metrics with small-cell privacy suppression (FR-ANA-01, FR-ANA-02)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Small-cell suppression toggle */}
          <button
            type="button"
            onClick={() => {
              setIsSuppressionActive(!isSuppressionActive)
              addToast('Privacy Rule Toggled', `Small-cell suppression: ${!isSuppressionActive ? 'Active' : 'Disabled (Internal)'}`, 'info')
            }}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition cursor-pointer flex items-center gap-1.5 ${
              isSuppressionActive
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-gray-100 text-gray-700 border-gray-200'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Cell Suppression (N &lt; 5): {isSuppressionActive ? 'ON' : 'OFF'}</span>
          </button>

          <button
            type="button"
            onClick={handleExportReport}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Report</span>
          </button>
        </div>
      </section>

      {/* 2. THREE KEY METRIC CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="bg-white rounded-3xl border border-gray-100 p-5 shadow-2xs flex flex-col justify-between">
          <span className="text-xs font-semibold text-gray-500">Overall Campus Wellbeing Index</span>
          <div className="my-3">
            <span className="text-3xl font-black text-[#1E2433]">76.4</span>
            <span className="text-xs font-bold text-emerald-600 ml-2">↑ +4.2 vs Midterm</span>
          </div>
          <span className="text-[11px] text-gray-400">Computed from 892 verified pulses</span>
        </div>

        <div className="bg-white rounded-3xl border border-gray-100 p-5 shadow-2xs flex flex-col justify-between">
          <span className="text-xs font-semibold text-gray-500">Intervention Success (Helped)</span>
          <div className="my-3">
            <span className="text-3xl font-black text-[#1E2433]">82.1%</span>
            <span className="text-xs font-bold text-blue-600 ml-2">Resolved Positive</span>
          </div>
          <span className="text-[11px] text-gray-400">Documented staff &amp; student attestations</span>
        </div>

        <div className="bg-white rounded-3xl border border-gray-100 p-5 shadow-2xs flex flex-col justify-between">
          <span className="text-xs font-semibold text-gray-500">Early Warning Signal-to-Case Ratio</span>
          <div className="my-3">
            <span className="text-3xl font-black text-[#1E2433]">1 : 1</span>
            <span className="text-xs font-bold text-purple-600 ml-2">100% Accountable</span>
          </div>
          <span className="text-[11px] text-gray-400">Zero unattended alert backlogs</span>
        </div>
      </div>

      {/* 3. COHORT DIMENSIONS & OUTCOME BREAKDOWNS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Wellbeing Dimensions Matrix (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-gray-100 shadow-2xs p-5 md:p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <div>
              <h3 className="text-sm font-bold text-[#1E2433]">Wellbeing Pulse Dimensions (1-100 Normalized)</h3>
              <p className="text-xs text-[#717E95]">6 Core Dimensions per DISHA Blueprint §10</p>
            </div>
            <span className="text-[11px] text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full font-bold">
              Band: Positive (65-80)
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {[
              { dim: 'Emotional Wellbeing', score: 72, change: '+2.1', width: '72%' },
              { dim: 'Belonging & Community', score: 78, change: '+5.0', width: '78%' },
              { dim: 'Academic Experience', score: 68, change: '+1.4', width: '68%' },
              { dim: 'Support & Trust', score: 84, change: '+6.2', width: '84%' },
              { dim: 'Safety & Respect', score: 88, change: '+3.1', width: '88%' },
              { dim: 'Growth & Confidence', score: 75, change: '+4.0', width: '75%' },
            ].map((d) => (
              <div key={d.dim} className="flex flex-col gap-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-800">{d.dim}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#1E2433]">{d.score} / 100</span>
                    <span className="text-[10px] text-emerald-600 font-semibold">{d.change}</span>
                  </div>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full" style={{ width: d.width }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Case Outcomes Breakdown (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-gray-100 shadow-2xs p-5 md:p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <div>
              <h3 className="text-sm font-bold text-[#1E2433]">Recorded Case Outcomes (FR-CASE-05)</h3>
              <p className="text-xs text-[#717E95]">Mandatory human outcome evaluations</p>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            {[
              { label: 'Helped (Effective Outcome)', count: 32, percent: '76.2%', color: 'bg-emerald-500' },
              { label: 'Mixed (Partial Progress)', count: 6, percent: '14.3%', color: 'bg-blue-500' },
              { label: 'Not Helped (Re-evaluating)', count: 2, percent: '4.8%', color: 'bg-rose-500' },
              { label: 'Unknown (In Denominator)', count: 2, percent: '4.8%', color: 'bg-gray-400' },
            ].map((out) => (
              <div key={out.label} className="p-3 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className={`w-3 h-3 rounded-full ${out.color}`} />
                  <span className="font-semibold text-gray-800">{out.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#1E2433]">{out.count}</span>
                  <span className="text-[11px] text-gray-400">({out.percent})</span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-2xl bg-blue-50 border border-blue-100 text-[11px] text-blue-900 leading-relaxed">
            Per requirement <strong>FR-CASE-05</strong>, &apos;unknown&apos; outcomes remain in reporting denominators to prevent false-positive inflation.
          </div>
        </div>
      </div>
    </div>
  )
}

