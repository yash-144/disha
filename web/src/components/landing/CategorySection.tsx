import React, { useState } from 'react'
import {
  Briefcase,
  Monitor,
  Palette,
  Database,
  Cloud,
  ChevronLeft,
  ChevronRight,
  MousePointer2,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

const CATEGORIES = [
  {
    key: 'business',
    title: 'Business & Entrepreneurship',
    desc: 'Learn to start, run and grow a venture with practical unit economics and scaling.',
    icon: Briefcase,
    iconBg: 'bg-accent',
    count: '14 Courses',
  },
  {
    key: 'web',
    title: 'Computer Science & IT',
    desc: 'Master full-stack programming, React 19, algorithms, and backend architectures.',
    icon: Monitor,
    iconBg: 'bg-brand',
    count: '24 Courses',
  },
  {
    key: 'design',
    title: 'Design & Multimedia',
    desc: 'Create compelling interfaces, design systems in Figma, typography, and motion.',
    icon: Palette,
    iconBg: 'bg-accent',
    count: '18 Courses',
  },
  {
    key: 'data',
    title: 'Data & Cloud Infrastructure',
    desc: 'Architect relational schemas, scale PostgreSQL, AWS clusters, and serverless.',
    icon: Database,
    iconBg: 'bg-brand',
    count: '16 Courses',
  },
]

export function CategorySection() {
  const { navigateTo } = useApp()
  const [active, setActive] = useState(1)

  return (
    <section className="mx-auto max-w-6xl px-6 pt-20">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-brand sm:text-3xl">
          Explore Courses by Popular Categories
        </h2>
        <p className="mt-2 text-xs text-muted sm:text-sm">
          Select a category track to see curated industry bootcamps & live mentor cohort sessions.
        </p>
      </div>

      <div className="mt-10 flex items-center gap-4">
        {/* Previous */}
        <button
          onClick={() => setActive((prev) => (prev + CATEGORIES.length - 1) % CATEGORIES.length)}
          className="hidden h-10 w-10 shrink-0 items-center justify-center border-2 border-ink bg-white text-ink shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100 sm:flex"
          aria-label="Previous category"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>

        {/* Categories Grid */}
        <div className="grid flex-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {CATEGORIES.map((c, i) => {
            const Icon = c.icon
            const isSelected = i === active

            return (
              <button
                key={c.title}
                onClick={() => {
                  setActive(i)
                  navigateTo('courses')
                }}
                className={`relative flex flex-col items-center border-2 border-ink bg-white p-6 text-center transition-all duration-200 ${
                  isSelected
                    ? '-translate-y-2 shadow-[6px_6px_0_#0d1b3e] ring-2 ring-brand'
                    : 'shadow-[3px_3px_0_#0d1b3e] hover:-translate-y-1'
                }`}
              >
                <span
                  className={`flex h-16 w-16 items-center justify-center rounded-xl border-2 border-ink ${c.iconBg} text-white shadow-[2px_2px_0_#0d1b3e]`}
                >
                  <Icon className="h-8 w-8" strokeWidth={1.75} />
                </span>

                <span className="mt-4 text-sm font-bold leading-snug text-ink">{c.title}</span>
                <span className="mt-2 text-xs leading-relaxed text-muted line-clamp-2">{c.desc}</span>

                <span className="mt-4 rounded-full bg-gray-100 px-3 py-0.5 text-xs font-bold text-gray-700">
                  {c.count}
                </span>

                {isSelected && (
                  <MousePointer2 className="absolute -bottom-3 right-1/3 h-6 w-6 fill-brand text-white animate-bounce" />
                )}
              </button>
            )
          })}
        </div>

        {/* Next */}
        <button
          onClick={() => setActive((prev) => (prev + 1) % CATEGORIES.length)}
          className="hidden h-10 w-10 shrink-0 items-center justify-center border-2 border-ink bg-brand text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-brand-dark sm:flex"
          aria-label="Next category"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
    </section>
  )
}
