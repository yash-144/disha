import React from 'react'
import { ArrowRight } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const CARD1_IMG = 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=600&q=80'
const CENTER_IMG = 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=900&q=80'
const CARD3_IMG = 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=600&q=80'

export function WhyDishaSection() {
  const { navigateTo } = useApp()

  return (
    <section className="w-full py-24 sm:py-32 px-4 sm:px-8 lg:px-12 xl:px-16 bg-white font-sans">
      <div className="mx-auto w-full max-w-[1600px]">
        {/* Top Header Row (Problem & Solution Oriented) */}
        <div className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-6 items-baseline mb-16">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            / WHY DISHA
          </div>
          <div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-slate-900 leading-[1.25] max-w-5xl">
              <span className="font-semibold text-slate-950">
                The silent dropout crisis ends with timely, accountable intervention.
              </span>{' '}
              <span className="text-slate-500">
                Traditional universities lose up to 32% of at-risk students due to delayed alerts. We build ML early-warning systems that catch slippage and guarantee human action.
              </span>
            </h2>
          </div>
        </div>

        {/* 3-Card Asymmetric Layout (Clean & Responsive) */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.35fr_1fr] gap-6 sm:gap-8 items-stretch">

          {/* Left Card: Lower Monthly Dropouts */}
          <div className="group rounded-3xl bg-paper border border-slate-200/90 p-8 flex flex-col justify-between transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <div className="w-full h-48 rounded-2xl overflow-hidden mb-6 bg-slate-200">
              <img
                src={CARD1_IMG}
                alt="Early warning radar"
                className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
              />
            </div>
            <div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
                Early dropout risk prevention
              </h3>
              <p className="mt-2.5 text-xs sm:text-sm leading-relaxed text-slate-600 font-normal">
                A weekly risk score for every student in every course, with the reasons behind it, so help arrives before exams.
              </p>
              <div
                onClick={() => navigateTo('login')}
                className="mt-6 flex items-center gap-1.5 text-xs font-semibold text-blue-600 group-hover:text-blue-700 cursor-pointer"
              >
                <span>See the risk model</span>
                <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* Center Card: End-to-End Project Management (Featured Blue Card, unwanted shield icon removed) */}
          <div className="group rounded-3xl bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white p-8 sm:p-10 flex flex-col justify-between overflow-hidden relative shadow-xl shadow-blue-500/10 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/20 hover:-translate-y-1">
            <div>
              <h3 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight text-white leading-snug">
                End-to-end accountable intervention management
              </h3>
              <p className="mt-3.5 text-xs sm:text-sm md:text-base text-blue-100/90 leading-relaxed font-light max-w-lg">
                Every alert becomes an owned case with tracked SLA deadlines. Multi-campus context synced seamlessly via Meko on YugabyteDB.
              </p>
            </div>

            {/* Bottom Rounded Photo Preview */}
            <div className="mt-8 w-full h-52 sm:h-56 rounded-2xl overflow-hidden border border-white/20 bg-blue-900/40 relative">
              <img
                src={CENTER_IMG}
                alt="Faculty and student collaboration"
                className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500 opacity-90"
              />
            </div>
          </div>

          {/* Right Card: Increase Student Value */}
          <div className="group rounded-3xl bg-paper border border-slate-200/90 p-8 flex flex-col justify-between transition-all duration-300 hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1">
            <div className="w-full h-48 rounded-2xl overflow-hidden mb-6 bg-slate-200">
              <img
                src={CARD3_IMG}
                alt="Student support"
                className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
              />
            </div>
            <div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
                Students stay in the loop
              </h3>
              <p className="mt-2.5 text-xs sm:text-sm leading-relaxed text-slate-600 font-normal">
                Wellbeing check-ins, support requests and rewards for good habits, all in one place.
              </p>
              <div
                onClick={() => navigateTo('login')}
                className="mt-6 flex items-center gap-1.5 text-xs font-semibold text-blue-600 group-hover:text-blue-700 cursor-pointer"
              >
                <span>Sign in</span>
                <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
