import React from 'react'
import { Play, Radio, Clock } from 'lucide-react'

export function LiveClasses() {
  return (
    <section className="border-y-4 border-ink bg-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-[1.3fr_1fr] lg:items-center">
        <div className="relative">
          <div className="absolute inset-0 translate-x-3 translate-y-3 bg-brand" />
          <div className="relative overflow-hidden border-2 border-ink">
            <img src={LIVE_IMG} alt="Learner in a live class" className="aspect-video w-full object-cover" />
            <span className="absolute left-4 top-4 flex items-center gap-2 border-2 border-ink bg-[#0f9d58] px-3 py-1 text-xs font-bold text-white">
              <Radio className="h-3.5 w-3.5" /> LIVE · 12:30 PM
            </span>
            <button
              aria-label="Join live class"
              className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center border-2 border-ink bg-white text-brand transition-colors duration-150 hover:bg-gray-100"
            >
              <Play className="h-6 w-6 fill-brand" />
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
            Join live classes, <span className="text-ink">verify your skills in real time.</span>
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted">
            Build alongside mentors every week. Ask questions, ship projects, and get reviewed before the session ends.
          </p>
          <ul className="mt-7 divide-y-2 divide-ink border-2 border-ink bg-[#f5f5f5]">
            {SESSIONS.map((s) => (
              <li key={s.title} className="flex items-center justify-between gap-4 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold">{s.title}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-[11px] text-muted">
                    <Clock className="h-3 w-3" /> {s.when}
                  </p>
                </div>
                <span className={`shrink-0 px-2 py-1 text-[10px] font-bold text-white ${s.live ? 'bg-[#0f9d58]' : 'bg-brand'}`}>
                  {s.live ? 'Live now' : 'Upcoming'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

const LIVE_IMG = 'https://cdn.magicpatterns.com/patterns/generated-images/4d56ae86-5c0d-4cf8-b413-1a348140f2ea.jpg'

const SESSIONS = [
  { title: 'React Hooks: Build a Live Dashboard', when: 'Today · 12:30 PM IST', live: true },
  { title: 'SQL Joins Without the Headache', when: 'Thu · 6:00 PM IST', live: false },
  { title: 'Figma to Code: Ship a Landing Page', when: 'Sat · 11:00 AM IST', live: false },
]
