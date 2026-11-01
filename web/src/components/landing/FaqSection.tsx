import React, { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

const FAQS = [
  {
    q: 'What is DISHA’s core operating principle?',
    a: 'DISHA operates on "No Alert Without Action." Unlike passive analytics dashboards, every warning signal generates an immutable SHA-256 evidence packet, assigns a single accountable owner, sets a binding SLA deadline, and records an auditable human outcome.',
  },
  {
    q: 'How does the Calibrated Early-Warning ML model work?',
    a: 'Models evaluate student indicators strictly at chronological checkpoints (cp0 at admission, cp1 after Sem 1, cp2 after Sem 2) using only academic and engagement data. Protected demographic features are never used in scoring. Cutoffs guarantee ≥85% precision with a 15% cohort capacity cap to avoid advisor alert fatigue.',
  },
  {
    q: 'How does Meko by YugabyteDB handle universal context memory?',
    a: 'Meko provides an agent-native universal context engine over standard Model Context Protocol (MCP). It synchronizes longitudinal student case notes, intervention histories, and peer notes across multiple campuses in real-time on a distributed YugabyteDB PostgreSQL-compatible backbone.',
  },
  {
    q: 'Is DISHA compliant with data privacy regulations like DPDP Act 2023?',
    a: 'Yes. DISHA is built from the ground up to comply with India’s Digital Personal Data Protection (DPDP) Act 2023 and FERPA guidelines. It enforces tenant row-level security (RLS), field-level consent controls, automated data retention purges, and cryptographic document verification on Base Sepolia.',
  },
  {
    q: 'How does DISHA solve the problem of advisor alert fatigue?',
    a: 'Traditional dashboards inundate faculty with thousands of unprioritized, passive alerts. DISHA solves this by capping cohort signals to an advisor capacity limit (default 15%), requiring high-precision cutoffs (≥85%), and enforcing strict ownership and binding SLA deadlines for every accepted signal.',
  },
  {
    q: 'What makes DISHA different from traditional campus ERP or LMS analytics?',
    a: 'Traditional campus systems are retrospective, highlighting failure only after exams or dropouts occur. DISHA operates proactively across three chronological checkpoints (cp0 at admission, cp1 mid-year, cp2 end-of-year) using pure academic indicators, backed by Meko universal context memory and auditable intervention tracking.',
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
            / FAQS &amp; ARCHITECTURE
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-normal tracking-tight text-slate-900 leading-[1.25]">
            <span className="font-semibold text-slate-950">Frequently asked</span> questions
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-500 font-normal">
            Everything you need to know about DISHA early-warning signals, SLA tracking, and universal context memory.
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
