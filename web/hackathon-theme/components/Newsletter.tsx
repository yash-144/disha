import React from 'react'
import { Send } from 'lucide-react'

export function Newsletter() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="relative">
        <div className="absolute inset-0 translate-x-3 translate-y-3 bg-ink" />
        <div className="relative grid gap-8 border-2 border-ink bg-[#0f9d58] p-8 text-white sm:p-12 lg:grid-cols-[1.2fr_1fr] lg:items-center">
          <div>
            <h2 className="text-2xl font-bold leading-snug sm:text-[30px]">Subscribe to the SkillsUp weekly.</h2>
            <p className="mt-3 text-sm leading-relaxed text-white/90">
              New courses, live session dates and one practical tutorial, every Monday. No spam.
            </p>
          </div>
          <form className="flex flex-col gap-3 sm:flex-row" onSubmit={(e) => e.preventDefault()}>
            <input
              type="email"
              placeholder="you@email.com"
              className="min-w-0 flex-1 border-2 border-ink bg-white px-4 py-3 text-sm text-ink outline-none placeholder:text-gray-400"
            />
            <button className="flex items-center justify-center gap-2 whitespace-nowrap border-2 border-ink bg-brand px-6 py-3 text-sm font-bold text-white transition-colors duration-150 hover:bg-brand-dark">
              Subscribe <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}
