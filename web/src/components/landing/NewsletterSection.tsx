import React, { useState } from 'react'
import { Mail, CheckCircle2 } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function NewsletterSection() {
  const { addToast } = useApp()
  const [email, setEmail] = useState('')

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    addToast('Subscribed!', `You will now receive weekly tech digests at ${email}.`, 'success')
    setEmail('')
  }

  return (
    <section className="border-t-4 border-ink bg-ink py-14 text-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-6">
        <div className="max-w-md">
          <span className="text-xs font-bold uppercase tracking-wider text-accent">
            Stay ahead of tech curves
          </span>
          <h2 className="mt-1 text-xl font-bold sm:text-2xl">
            Subscribe to the SkillsUp Weekly Dispatch
          </h2>
          <p className="mt-1 text-xs text-gray-300">
            Curated system design breakdowns, new cohort schedules, and SQL puzzles in your inbox.
          </p>
        </div>

        <form onSubmit={handleSubscribe} className="flex w-full max-w-md gap-2">
          <div className="flex flex-1 items-center border-2 border-white bg-white/10 px-3 py-2 text-xs text-white backdrop-blur-xs focus-within:bg-white focus-within:text-ink">
            <Mail className="mr-2 h-4 w-4 shrink-0 text-gray-400" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your work email"
              className="w-full bg-transparent text-xs outline-none placeholder:text-gray-400"
            />
          </div>
          <button
            type="submit"
            className="border-2 border-white bg-accent px-5 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#ffffff] transition hover:bg-accent-dark"
          >
            Subscribe
          </button>
        </form>
      </div>
    </section>
  )
}
