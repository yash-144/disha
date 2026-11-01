import React from 'react'

const TOPICS = [
  'Full-Stack Web Dev',
  'React 19 & Next.js',
  'PostgreSQL & Database Design',
  'Figma UI/UX Systems',
  'AWS Certified Solutions',
  'Interactive Canvas & 2D Context',
  'TypeScript Architecture',
  'Docker & Microservices',
  'System Design & Scalability',
]

export function MarqueeBanner() {
  return (
    <div className="relative overflow-hidden border-b-4 border-ink bg-accent py-3 text-white">
      <div className="animate-marquee flex items-center gap-8 whitespace-nowrap text-xs font-bold uppercase tracking-wider">
        {[...TOPICS, ...TOPICS, ...TOPICS].map((topic, i) => (
          <span key={i} className="flex items-center gap-8">
            <span>{topic}</span>
            <span className="h-1.5 w-1.5 rounded-full bg-white opacity-60" />
          </span>
        ))}
      </div>
    </div>
  )
}
