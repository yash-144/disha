import React, { useState } from 'react'
import { CheckCircle2, ArrowRight } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function SolutionsSection() {
  const { navigateTo } = useApp()
  const [activeDial] = useState(88)

  return (
    <section className="w-full py-24 sm:py-32 px-4 sm:px-8 lg:px-12 xl:px-16 bg-slate-50/50 font-sans border-t border-slate-100">
      <div className="mx-auto w-full max-w-[1600px]">
        {/* Center Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            / SOLUTIONS
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-slate-900 leading-[1.2]">
            <span className="font-semibold text-slate-950">
              Accountable early-warning designed
            </span>{' '}
            for every campus stakeholder
          </h2>
          <p className="mt-3.5 text-xs sm:text-sm md:text-base text-slate-500 font-normal leading-relaxed max-w-2xl mx-auto">
            Whether you are a student seeking academic resilience, an advisor managing case interventions, or an institutional dean steering student retention.
          </p>
        </div>

        {/* 3 Solutions Cards with Center Gauge (Clean & Responsive) */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.25fr_1fr] gap-6 sm:gap-8 items-center">

          {/* Card 1: Student Cockpit */}
          <div className="rounded-3xl bg-paper border border-slate-200/90 p-8 sm:p-10 shadow-sm transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
              Student Academic Radar
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-500 leading-relaxed font-normal">
              Continuous academic transparency with clear milestones. No surprises before semester finals.
            </p>
            <ul className="mt-6 space-y-3.5 text-xs sm:text-sm text-slate-600">
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Attendance floor tracking (75% UGC benchmark)</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Personalized SGPA &amp; exam performance goals</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Instant 1-click peer tutor &amp; mentor bookings</span>
              </li>
            </ul>
            <button
              onClick={() => navigateTo('login')}
              className="mt-8 flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-blue-600 hover:text-blue-700 transition cursor-pointer"
            >
              <span>Explore Student Portal</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Card 2: Center Featured Circular Blue Gauge Dial */}
          <div className="rounded-3xl bg-gradient-to-b from-blue-600 to-indigo-700 text-white p-8 sm:p-10 shadow-xl shadow-blue-600/10 flex flex-col items-center text-center relative overflow-hidden transition-all duration-300 hover:shadow-2xl hover:shadow-blue-600/20">
            {/* Circular Gauge Graphic */}
            <div className="relative w-52 h-52 sm:w-56 sm:h-56 my-4 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  className="stroke-white/20 fill-none"
                  strokeWidth="7"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  className="stroke-white fill-none"
                  strokeWidth="7"
                  strokeDasharray="264"
                  strokeDashoffset={264 - (264 * activeDial) / 100}
                  strokeLinecap="round"
                />
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl sm:text-5xl font-bold tracking-tight text-white">{activeDial}%</span>
                <span className="text-[10px] uppercase font-semibold text-blue-200 mt-1 tracking-wider">
                  Retention Rate
                </span>
                <span className="text-[10px] text-emerald-300 font-medium mt-1">
                  +14% vs National Avg
                </span>
              </div>
            </div>

            <h4 className="mt-4 text-xl font-semibold text-white tracking-tight">
              Calibrated Early-Warning ML
            </h4>
            <p className="mt-2 text-xs sm:text-sm text-blue-100/90 font-light max-w-xs leading-relaxed">
              Operating on the strict principle: <strong className="font-semibold text-white">"No Alert Without Action"</strong>.
            </p>
          </div>

          {/* Card 3: Faculty & Counsellor Portal */}
          <div className="rounded-3xl bg-paper border border-slate-200/90 p-8 sm:p-10 shadow-sm transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
              Faculty &amp; Counsellor Suite
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-500 leading-relaxed font-normal">
              Eliminate alert fatigue. Every accepted signal has an assigned owner and SLA deadline.
            </p>
            <ul className="mt-6 space-y-3.5 text-xs sm:text-sm text-slate-600">
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Deterministic case routing &amp; escalation jobs</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Meko universal context memory across campuses</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>DPDP Act 2023 auditable outcome records</span>
              </li>
            </ul>
            <button
              onClick={() => navigateTo('login')}
              className="mt-8 flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition cursor-pointer"
            >
              <span>Explore Faculty Suite</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

        </div>
      </div>
    </section>
  )
}
