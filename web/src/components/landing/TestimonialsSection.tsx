import React, { useState } from 'react'
import { Star, ChevronLeft, ChevronRight, Quote } from 'lucide-react'

const REVIEWS = [
  {
    quote:
      'SkillsUp completely transformed my career trajectory. The live React & canvas project was the highlight of my interview portfolio. I landed a senior frontend role at a fintech scaleup in 3 months!',
    name: 'Anika Sharma',
    role: 'Frontend Engineer @ FinTech Scaleup',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
    stars: 5,
    course: 'Full-Stack Web Dev Bootcamp',
  },
  {
    quote:
      'The interactive whiteboard sessions during live classes made learning complex database indexing and SQL query execution plans feel approachable. The mentorship is truly world-class.',
    name: 'Karan Patel',
    role: 'Data Engineer @ DataCloud',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80',
    stars: 5,
    course: 'Advanced Database & SQL',
  },
  {
    quote:
      'I transitioned from graphic design to product UI/UX with the design systems track. The component libraries and token workflows we created in Figma were immediately useful in my daily job.',
    name: 'Elena Rostova',
    role: 'Lead Product Designer',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=200&q=80',
    stars: 5,
    course: 'UI/UX Visual Product Design',
  },
]

export function TestimonialsSection() {
  const [active, setActive] = useState(0)

  return (
    <section className="border-t-4 border-ink bg-paper py-20">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-brand">
              Learner Experiences
            </span>
            <h2 className="mt-1 text-2xl font-bold leading-snug text-ink sm:text-[32px]">
              Trusted by 7,000+ engineers <span className="text-brand">&amp; designers.</span>
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActive((prev) => (prev + REVIEWS.length - 1) % REVIEWS.length)}
              className="flex h-9 w-9 items-center justify-center border-2 border-ink bg-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-gray-100"
              aria-label="Previous review"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setActive((prev) => (prev + 1) % REVIEWS.length)}
              className="flex h-9 w-9 items-center justify-center border-2 border-ink bg-brand text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-brand-dark"
              aria-label="Next review"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Reviews Cards */}
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {REVIEWS.map((r, i) => {
            const isFeatured = i === active
            return (
              <div
                key={r.name}
                className={`relative flex flex-col justify-between border-2 border-ink bg-white p-6 transition-all duration-200 ${
                  isFeatured
                    ? 'shadow-[6px_6px_0_#0d1b3e] ring-2 ring-brand -translate-y-1'
                    : 'shadow-[3px_3px_0_#0d1b3e]'
                }`}
              >
                <div>
                  <div className="flex items-center gap-1 text-amber-400">
                    {Array.from({ length: r.stars }).map((_, s) => (
                      <Star key={s} className="h-4 w-4 fill-amber-400" />
                    ))}
                  </div>

                  <p className="mt-4 text-xs leading-relaxed text-gray-700 italic sm:text-sm">
                    "{r.quote}"
                  </p>
                </div>

                <div className="mt-6 flex items-center gap-3 border-t border-gray-100 pt-4">
                  <img
                    src={r.avatar}
                    alt={r.name}
                    className="h-10 w-10 rounded-full border border-ink object-cover"
                  />
                  <div>
                    <p className="text-xs font-bold text-ink">{r.name}</p>
                    <p className="text-xs text-muted">{r.role}</p>
                    <span className="mt-0.5 inline-block text-xs font-bold text-accent">
                      {r.course}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
