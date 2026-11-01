import React from 'react'
import { Play, Radio, Clock, Users, ArrowRight, Video, Calendar, Sparkles } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { LIVE_SESSIONS_DATA } from '../../mockData'

const LIVE_IMG = 'https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=800&q=80'

export function LiveClassesSection() {
  const { setActiveLiveModal, addToast } = useApp()
  const activeSession = LIVE_SESSIONS_DATA[0]

  return (
    <section className="border-y-4 border-ink bg-white font-mono py-20">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-[1.3fr_1fr] lg:items-center">
        {/* Stream Banner */}
        <div className="relative">
          <div className="absolute inset-0 translate-x-3 translate-y-3 bg-brand border-2 border-ink" />
          <div className="relative overflow-hidden border-4 border-ink bg-black shadow-xl">
            <img
              src={LIVE_IMG}
              alt="Live interactive cohort"
              className="aspect-video w-full object-cover opacity-90"
            />

            {/* Live badge */}
            <span className="absolute left-4 top-4 flex items-center gap-2 border-2 border-ink bg-[#0f9d58] px-3 py-1 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] animate-pulse">
              <Radio className="h-3.5 w-3.5" /> LIVE
            </span>

            {/* Play Button Trigger */}
            <button
              onClick={() => setActiveLiveModal(activeSession)}
              aria-label="Join live class"
              className="group absolute left-1/2 top-1/2 flex h-20 w-20 -translate-x-1/2 -translate-y-1/2 items-center justify-center border-4 border-ink bg-white text-brand shadow-[4px_4px_0_#0d1b3e] transition hover:scale-105 hover:bg-gray-50"
            >
              <Play className="h-8 w-8 fill-brand pl-1 transition-transform group-hover:scale-110" />
            </button>

            <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-xs text-white bg-black/75 px-3 py-2 border-2 border-white/20 backdrop-blur-xs">
              <span className="font-bold truncate">{activeSession.instructor}: {activeSession.title}</span>
              <span className="hidden sm:inline font-mono font-bold text-emerald-400">Click to Join Studio</span>
            </div>
          </div>
        </div>

        {/* Content & Schedule List */}
        <div>
          <span className="inline-block border-2 border-ink bg-[#0f9d58] px-2.5 py-0.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] mb-3">
            REAL-TIME COLLABORATION
          </span>
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[32px]">
            Join live classes, <span className="text-ink">verify your skills in real time.</span>
          </h2>
          <p className="mt-4 text-xs leading-relaxed text-muted sm:text-sm">
            Build alongside senior mentors every week. Ask questions, annotate on the shared
            vector canvas, ship projects, and get code reviews before the session ends.
          </p>

          <ul className="mt-7 divide-y-2 divide-ink border-2 border-ink bg-[#f5f5f5] shadow-[4px_4px_0_#0d1b3e]">
            {LIVE_SESSIONS_DATA.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between gap-4 p-3.5 transition hover:bg-white"
              >
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-ink sm:text-sm">{s.title}</p>
                  <p className="mt-0.5 flex items-center gap-2 text-[11px] text-muted">
                    <span className="font-bold text-ink">{s.instructor}</span>
                    <span>·</span>
                    <span className="flex items-center gap-1 font-mono text-brand font-bold">
                      <Clock className="h-3 w-3" /> {s.timeString}
                    </span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {s.isLiveNow ? (
                    <button
                      onClick={() => setActiveLiveModal(s)}
                      className="border-2 border-ink bg-[#0f9d58] px-3.5 py-1.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
                    >
                      Join Live
                    </button>
                  ) : (
                    <button
                      onClick={() => addToast('Reminder Set', `We will notify you before "${s.title}" starts!`, 'info')}
                      className="border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100"
                    >
                      Remind Me
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
