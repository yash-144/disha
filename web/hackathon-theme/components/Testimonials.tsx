import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, Star, Quote } from 'lucide-react'

export function Testimonials() {
  const [i, setI] = useState(0)
  const t = QUOTES[i]
  return (
    <section className="bg-[#f5f5f5]">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-[1fr_1.6fr] lg:items-center">
        <div>
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
            Real feedback <span className="text-ink">from learners who shipped.</span>
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted">4.5 average across 12,000+ verified course reviews.</p>
          <div className="mt-7 flex gap-3">
            <button
              onClick={() => setI((i + QUOTES.length - 1) % QUOTES.length)}
              aria-label="Previous testimonial"
              className="flex h-10 w-10 items-center justify-center border-2 border-ink bg-white transition-colors duration-150 hover:bg-gray-100"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => setI((i + 1) % QUOTES.length)}
              aria-label="Next testimonial"
              className="flex h-10 w-10 items-center justify-center border-2 border-ink bg-brand text-white transition-colors duration-150 hover:bg-brand-dark"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        <figure className="relative border-2 border-ink bg-white p-6 shadow-[6px_6px_0_#0d1b3e] sm:p-8">
          <Quote className="h-8 w-8 fill-[#0f9d58] text-[#0f9d58]" />
          <blockquote className="mt-4 text-base leading-relaxed sm:text-lg">{t.quote}</blockquote>
          <figcaption className="mt-6 flex items-center gap-4 border-t-2 border-ink pt-5">
            <img src={t.img} alt={t.name} className="h-12 w-12 border-2 border-ink object-cover" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold">{t.name}</p>
              <p className="text-[11px] text-muted">{t.role}</p>
            </div>
            <div className="flex gap-0.5">
              {Array.from({ length: 5 }).map((_, k) => (
                <Star key={k} className="h-3.5 w-3.5 fill-[#0f9d58] text-[#0f9d58]" />
              ))}
            </div>
          </figcaption>
        </figure>
      </div>
    </section>
  )
}

const QUOTES = [
  {
    quote: 'The bootcamp projects were the exact things my interviewer asked about. Three months in, I landed my first frontend role.',
    name: 'Arjun Mehta',
    role: 'Frontend Developer, Razorpay',
    img: 'https://cdn.magicpatterns.com/patterns/generated-images/30ad31ac-b927-45b4-b1e0-c562572c3bb9.jpg',
  },
  {
    quote: 'Live mentor reviews changed how I write SQL. I stopped guessing and started explaining my queries.',
    name: 'Nadia Brooks',
    role: 'Data Analyst, Freshworks',
    img: 'https://cdn.magicpatterns.com/patterns/generated-images/a6c1ea6e-ca3f-4ca0-9f72-6344f82223e8.jpg',
  },
]
