import React, { useState } from 'react'
import { CheckCircle2, ArrowRight } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function SolutionsSection() {
  const { navigateTo } = useApp()
  const [activeDial] = useState(100)

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
              Early warning that works
            </span>{' '}
            for everyone on campus
          </h2>
          <p className="mt-3.5 text-xs sm:text-sm md:text-base text-slate-500 font-normal leading-relaxed max-w-2xl mx-auto">
            For students who want to stay on track, counsellors who help them, and leaders who want more students to finish.
          </p>
        </div>

        {/* 3 Solutions Cards with Center Gauge (Clean & Responsive) */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.25fr_1fr] gap-6 sm:gap-8 items-center">

          {/* Card 1: Student Cockpit */}
          <div className="rounded-3xl bg-paper border border-slate-200/90 p-8 sm:p-10 shadow-sm transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
              For students
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-500 leading-relaxed font-normal">
              Clear goals and no surprises before the exams.
            </p>
            <ul className="mt-6 space-y-3.5 text-xs sm:text-sm text-slate-600">
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Attendance tracked against the 75% minimum</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Your own grades and exam goals</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Ask for a peer tutor or mentor in one click</span>
              </li>
            </ul>
            <button
              onClick={() => navigateTo('login')}
              className="mt-8 flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-blue-600 hover:text-blue-700 transition cursor-pointer"
            >
              <span>See the student view</span>
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
                <span className="text-4xl sm:text-5xl font-bold tracking-tight text-white">Weekly</span>
                <span className="text-xs font-semibold text-blue-200 mt-1">
                  check of every student
                </span>
                <span className="text-xs text-emerald-300 font-medium mt-1">
                  With reasons in plain words
                </span>
              </div>
            </div>

            <h4 className="mt-4 text-xl font-semibold text-white tracking-tight">
              Warnings you can trust
            </h4>
            <p className="mt-2 text-xs sm:text-sm text-blue-100/90 font-light max-w-xs leading-relaxed">
              <strong className="font-semibold text-white">Every warning gets a follow-up.</strong>
            </p>
          </div>

          {/* Card 3: Faculty & Counsellor Portal */}
          <div className="rounded-3xl bg-paper border border-slate-200/90 p-8 sm:p-10 shadow-sm transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
              For teachers and counsellors
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-500 leading-relaxed font-normal">
              Fewer, clearer alerts. Each one has an owner and a due date.
            </p>
            <ul className="mt-6 space-y-3.5 text-xs sm:text-sm text-slate-600">
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Cases go to the right person automatically</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>What worked before, shared without student names</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>A clear record of what was done and how it went</span>
              </li>
            </ul>
            <button
              onClick={() => navigateTo('login')}
              className="mt-8 flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition cursor-pointer"
            >
              <span>See the teacher and counsellor view</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

        </div>
      </div>
    </section>
  )
}
