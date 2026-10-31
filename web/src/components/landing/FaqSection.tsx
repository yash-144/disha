import React, { useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle, CheckCircle2 } from 'lucide-react'

const FAQS = [
  {
    q: 'How does the LMS Interactive Whiteboard work during cohort classes?',
    a: 'Every enrolled student and instructor has access to a synchronous HTML5 vector whiteboard. Instructors can draw system architecture diagrams, highlight code snippets, and save snapshot diagrams that learners can download immediately after class.',
  },
  {
    q: 'Can I test both Instructor and Student workflows in SkillsUp?',
    a: 'Yes! SkillsUp features a dynamic Role Switcher in both the public header and the LMS cockpit. You can toggle between 👨‍🏫 Live Instructor mode (to draw on canvas, publish courses, and manage gradebooks) and 🎓 Enrolled Student mode with one click.',
  },
  {
    q: 'Are the certifications verifiable by top tech companies?',
    a: 'Yes, upon passing module assessments with 80%+ and shipping capstone repositories, students receive an immutable certificate ID that can be linked on LinkedIn, GitHub, and resumes.',
  },
  {
    q: 'What happens if I miss a scheduled live cohort session?',
    a: 'All live streams are automatically recorded in high-definition and archived inside your LMS Dashboard under "Courses & Syllabi" within 2 hours of stream completion.',
  },
  {
    q: 'How does the dashboard screen-wrap responsive frame work?',
    a: 'The LMS dashboard features a responsive, dynamic blue border cockpit that dynamically fits full-screen viewports, supports collapsible sidebar navigation, and allows quick toggling between viewport-fit and expanded modes.',
  },
]

export function FaqSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(0)

  const toggle = (i: number) => {
    setOpenIdx(openIdx === i ? null : i)
  }

  return (
    <section className="border-t-4 border-ink bg-white py-20 font-mono text-ink">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="text-center">
          <span className="inline-block border-2 border-ink bg-[#0f9d58] px-3 py-0.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e]">
            LEARNER FAQ
          </span>
          <h2 className="mt-3 text-2xl font-bold text-brand sm:text-3xl">
            Frequently Asked Questions
          </h2>
          <p className="mt-2 text-xs text-muted sm:text-sm">
            Everything you need to know about SkillsUp courses, live canvas, and certifications.
          </p>
        </div>

        <div className="mt-10 space-y-3">
          {FAQS.map((faq, idx) => {
            const isOpen = openIdx === idx
            return (
              <div
                key={idx}
                className="border-2 border-ink bg-white shadow-[3px_3px_0_#0d1b3e] transition-all"
              >
                <button
                  onClick={() => toggle(idx)}
                  className="flex w-full items-center justify-between p-4 text-left text-xs sm:text-sm font-bold text-ink hover:bg-gray-50"
                >
                  <span className="flex items-center gap-2.5">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center border border-ink bg-brand text-white text-[10px]">
                      ?
                    </span>
                    <span>{faq.q}</span>
                  </span>
                  {isOpen ? (
                    <ChevronUp className="h-4 w-4 shrink-0 text-brand" />
                  ) : (
                    <ChevronDown className="h-4 w-4 shrink-0 text-gray-500" />
                  )}
                </button>

                {isOpen && (
                  <div className="border-t-2 border-ink/10 bg-[#f8fafd] p-4 text-xs leading-relaxed text-gray-700 animate-in fade-in">
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
