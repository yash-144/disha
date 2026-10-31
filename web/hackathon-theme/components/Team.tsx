import React from 'react'

export function Team() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
          Meet the mentors <span className="text-ink">behind every course.</span>
        </h2>
        <p className="max-w-sm text-sm text-muted">Practitioners first. Every mentor still builds for a living.</p>
      </div>
      <div className="mt-10 grid grid-cols-2 gap-5 lg:grid-cols-4">
        {TEAM.map((m, i) => (
          <article key={m.name} className="flex flex-col border-2 border-ink bg-white">
            <div className={`border-b-2 border-ink ${i % 2 === 0 ? 'bg-brand' : 'bg-[#0f9d58]'}`}>
              <img src={m.img} alt={m.name} className="aspect-square w-full object-cover mix-blend-normal" />
            </div>
            <div className="flex flex-1 flex-col p-4">
              <h3 className="text-sm font-bold">{m.name}</h3>
              <p className="mt-0.5 text-[11px] text-muted">{m.role}</p>
              <p className={`mt-auto pt-3 text-[11px] font-bold ${i % 2 === 0 ? 'text-brand' : 'text-[#0f9d58]'}`}>{m.courses}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

const TEAM = [
  { name: 'Priya Raman', role: 'Product Design Lead', courses: '6 courses', img: 'https://cdn.magicpatterns.com/patterns/generated-images/72ab2fae-1b08-4e28-aeec-ceebc55db39a.jpg' },
  { name: 'Daniel Novak', role: 'Full-Stack Engineer', courses: '9 courses', img: 'https://cdn.magicpatterns.com/patterns/generated-images/30ad31ac-b927-45b4-b1e0-c562572c3bb9.jpg' },
  { name: 'Amara Okafor', role: 'Data Science Mentor', courses: '5 courses', img: 'https://cdn.magicpatterns.com/patterns/generated-images/a6c1ea6e-ca3f-4ca0-9f72-6344f82223e8.jpg' },
  { name: 'Kenji Watanabe', role: 'Cloud Architect', courses: '7 courses', img: 'https://cdn.magicpatterns.com/patterns/generated-images/b68d385d-ec84-4708-835a-3c2564f6cb42.jpg' },
]
