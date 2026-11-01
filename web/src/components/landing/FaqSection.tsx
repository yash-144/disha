import React, { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

const FAQS = [
  {
    q: 'What does “every warning gets a follow-up” mean?',
    a: 'Every warning becomes a case with one named person and a due date. We then record how it turned out, so nothing gets lost.',
  },
  {
    q: 'How does the early warning work?',
    a: 'Each week, Disha estimates how likely a student is to struggle in a course, using marks, missed work and online activity. It explains every flag in plain words. Only as many students are flagged as your team can realistically help.',
  },
  {
    q: 'Can the team learn from past cases?',
    a: 'Yes. What helped past students is kept without names, so counsellors can see what works for similar students.',
  },
  {
    q: 'Is my data safe?',
    a: 'Yes. Disha follows India’s data protection law (DPDP Act 2023). People only see what their role allows, old data is deleted on schedule, and every access is recorded.',
  },
  {
    q: 'Will teachers be flooded with alerts?',
    a: 'No. The most urgent students come first, and each alert has an owner and a due date.',
  },
  {
    q: 'How is this different from a normal campus system?',
    a: 'Normal systems show problems after the exams are over. Disha checks every week during the term and follows each case to an outcome.',
  },
]

export function FaqSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(0)

  const toggle = (i: number) => {
    setOpenIdx(openIdx === i ? null : i)
  }

  return (
    <section id="faqs" className="py-24 px-4 sm:px-8 bg-white font-sans border-t border-slate-100">
      <div className="mx-auto max-w-4xl">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            / QUESTIONS
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-normal tracking-tight text-slate-900 leading-[1.25]">
            <span className="font-semibold text-slate-950">Frequently asked</span> questions
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-500 font-normal">
            Short answers to common questions.
          </p>
        </div>

        <div className="space-y-3.5">
          {FAQS.map((faq, idx) => {
            const isOpen = openIdx === idx
            return (
              <div
                key={idx}
                className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                  isOpen
                    ? 'border-slate-200 bg-white shadow-sm'
                    : 'border-slate-100 bg-slate-50/50 hover:border-slate-200 hover:bg-slate-50'
                }`}
              >
                <button
                  onClick={() => toggle(idx)}
                  className="flex w-full items-center justify-between p-5 text-left text-xs sm:text-sm font-semibold text-slate-900"
                >
                  <span className="pr-4">{faq.q}</span>
                  <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 transition-transform ${
                    isOpen ? 'bg-slate-900 text-white rotate-180' : 'bg-slate-100 text-slate-500'
                  }`}>
                    <ChevronDown className="h-4 w-4" />
                  </div>
                </button>

                {isOpen && (
                  <div className="px-5 pb-5 pt-1 text-xs sm:text-sm leading-relaxed text-slate-600 font-normal animate-in fade-in duration-200 border-t border-slate-50">
                    <p>{faq.a}</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
