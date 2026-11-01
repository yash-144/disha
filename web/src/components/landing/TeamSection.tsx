import React from 'react'
import { Award, BookOpen, ExternalLink } from 'lucide-react'
import { MENTORS_DATA } from '../../mockData'
import { useApp } from '../../context/AppContext'

export function TeamSection() {
  const { navigateTo } = useApp()

  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="text-center">
        <span className="text-xs font-bold uppercase tracking-wider text-accent">
          World-Class Faculty
        </span>
        <h2 className="mt-1 text-2xl font-bold text-brand sm:text-3xl">
          Learn directly from senior industry leaders
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-xs text-muted sm:text-sm">
          Our mentors are architects and senior practitioners with direct experience building and
          scaling mission-critical production systems.
        </p>
      </div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {MENTORS_DATA.map((m) => (
          <div
            key={m.name}
            className="group flex flex-col border-2 border-ink bg-white p-5 shadow-[4px_4px_0_#0d1b3e] transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
          >
            <div className="relative overflow-hidden border-2 border-ink">
              <img
                src={m.avatar}
                alt={m.name}
                className="aspect-square w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <span className="absolute bottom-2 right-2 rounded bg-black/70 px-2 py-0.5 text-xs font-bold text-white backdrop-blur-xs">
                {m.coursesCount} Courses
              </span>
            </div>

            <div className="mt-4 flex flex-1 flex-col">
              <h3 className="text-sm font-bold text-ink">{m.name}</h3>
              <p className="text-xs font-medium text-brand">{m.role}</p>
              <p className="mt-0.5 text-xs text-muted">{m.company}</p>

              <div className="mt-3 rounded border border-gray-100 bg-paper p-2 text-xs font-medium text-gray-700">
                <span className="font-bold text-gray-900">Focus: </span>
                {m.specialty}
              </div>

              <button
                onClick={() => navigateTo('courses')}
                className="mt-4 flex items-center justify-center gap-1 border border-ink bg-gray-50 py-1.5 text-xs font-bold text-ink transition hover:bg-brand hover:text-white"
              >
                View Courses <ExternalLink className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
