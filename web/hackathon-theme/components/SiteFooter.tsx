import React from 'react'

export function SiteFooter() {
  return (
    <footer className="border-t-4 border-ink bg-ink text-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-14 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <p className="text-2xl font-bold tracking-tight">
            <span className="text-[#34c77b]">Skills</span><span className="text-[#6f9cf0]">UP</span>
          </p>
          <p className="mt-3 max-w-xs text-xs leading-relaxed text-white/70">
            Skills development courses built by practitioners, for people who want to ship.
          </p>
        </div>
        {COLUMNS.map((c) => (
          <div key={c.title}>
            <h3 className="text-xs font-bold text-white">{c.title}</h3>
            <ul className="mt-4 space-y-2.5 text-xs text-white/70">
              {c.links.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="grid h-3 grid-cols-2">
        <span className="bg-[#0f9d58]" />
        <span className="bg-brand" />
      </div>
      <p className="mx-auto max-w-6xl px-6 py-5 text-[11px] text-white/60">© 2025 SkillsUp. All rights reserved.</p>
    </footer>
  )
}

const COLUMNS = [
  { title: 'Courses', links: ['Web Development', 'Data & SQL', 'UI Design', 'Cloud'] },
  { title: 'Company', links: ['About us', 'Mentors', 'Careers', 'Blog'] },
  { title: 'Support', links: ['Help centre', 'Contact', 'Privacy', 'Terms'] },
]
