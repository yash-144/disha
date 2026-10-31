import React from 'react'
import { ArrowRight, CheckCircle2 } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const LAPTOP_IMG = 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80'
const TECH_IMG = 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=600&q=80'

const BENEFITS = [
  ['Expert-Led Learning', 'Gain skills from production engineers and architects ensuring industry standard practices.'],
  ['Diverse Catalog', 'Select from comprehensive paths across Web, SQL, AI, Design, and Cloud DevOps.'],
  ['Practical Real-World Skills', 'Acquire immediately applicable hands-on codebases, not just passive multiple-choice videos.'],
  ['Flexible Interactive Schedule', 'Learn at your own pace with self-paced masterclasses or join weekend live cohort bootcamps.'],
  ['Certifications & Career Growth', 'Showcase accredited SkillsUp badges and capstone links directly on your resume & LinkedIn.'],
]

export function BenefitsSection() {
  const { navigateTo } = useApp()

  return (
    <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 py-20 lg:grid-cols-2">
      {/* Visual Collage */}
      <div className="relative mx-auto w-full max-w-[500px]">
        <div className="absolute -left-6 top-6 grid grid-cols-6 gap-2 opacity-30">
          {Array.from({ length: 36 }).map((_, i) => (
            <span key={i} className="h-1.5 w-1.5 rounded-full bg-brand" />
          ))}
        </div>

        <div className="relative ml-auto w-[80%] border-4 border-ink bg-white shadow-[6px_6px_0_#0d1b3e]">
          <img src={LAPTOP_IMG} alt="Student learning" className="aspect-[4/3] w-full object-cover" />
        </div>

        <div className="relative -mt-16 ml-[10%] w-[65%] overflow-hidden border-4 border-ink bg-white shadow-[6px_6px_0_#0d1b3e]">
          <img src={TECH_IMG} alt="Design and coding tools" className="aspect-video w-full object-cover" />
        </div>

        {/* Floating Callout Card */}
        <div className="absolute left-0 top-[-6%] w-[48%] border-2 border-ink bg-[#0f9d58] p-4 text-white shadow-[4px_4px_0_#0d1b3e]">
          <p className="text-sm font-bold leading-snug sm:text-base">
            Empower Your Future <span className="font-normal block text-xs mt-1">with modern skills development</span>
          </p>
        </div>
      </div>

      {/* Copy & Benefits Checklist */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-[#0f9d58]">
          Why Choose SkillsUp
        </span>
        <h2 className="mt-2 text-2xl font-bold leading-snug text-brand sm:text-[32px]">
          5 key benefits of learning
          <br />
          skill development courses from us
        </h2>

        <ul className="mt-7 space-y-4 text-xs leading-relaxed text-gray-700 sm:text-sm">
          {BENEFITS.map(([title, body]) => (
            <li key={title} className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#0f9d58]" />
              <div>
                <span className="font-bold text-ink">{title}: </span>
                <span className="text-muted">{body}</span>
              </div>
            </li>
          ))}
        </ul>

        <button
          onClick={() => navigateTo('courses')}
          className="mt-8 flex items-center gap-2 border-2 border-ink bg-[#0f9d58] px-7 py-3 text-xs font-bold text-white shadow-[3px_3px_0_#0d1b3e] transition hover:bg-[#0b7a43]"
        >
          Explore All Bootcamps <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </section>
  )
}
