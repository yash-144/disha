import React from 'react'

export function Marquee() {
  const row = [...ITEMS, ...ITEMS]
  return (
    <div className="overflow-hidden border-b-4 border-ink bg-brand py-4 text-white">
      <div className="flex w-max motion-safe:animate-[marquee_28s_linear_infinite]">
        {row.map((item, i) => (
          <span key={i} className="flex items-center gap-6 whitespace-nowrap pr-6 text-lg font-bold sm:text-xl">
            {item}
            <span className="h-3 w-3 bg-[#0f9d58]" aria-hidden />
          </span>
        ))}
      </div>
    </div>
  )
}

const ITEMS = ['20+ Instructors', '500+ Online Courses', '24h Mentor Support', 'Verified Certificates', 'Live Cohorts Weekly']
