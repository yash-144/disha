import React from 'react'
import { ArrowRight } from 'lucide-react'

export function Blog() {
  return (
    <section className="border-t-4 border-ink bg-[#f5f5f5]">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
            Insights &amp; ideas <span className="text-ink">from the blog.</span>
          </h2>
          <a className="text-sm font-bold text-brand underline underline-offset-4">All posts</a>
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {POSTS.map((p) => (
            <article key={p.title} className="flex flex-col border-2 border-ink bg-white">
              <img src={p.img} alt="" className="aspect-[16/10] w-full border-b-2 border-ink object-cover" />
              <div className="flex flex-1 flex-col p-5">
                <p className="flex items-center gap-2 text-[11px] text-muted">
                  <span className={`px-1.5 py-0.5 font-bold text-white ${p.tagBg}`}>{p.tag}</span>
                  {p.date}
                </p>
                <h3 className="mt-3 text-base font-bold leading-snug">{p.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-muted">{p.excerpt}</p>
                <a className="mt-auto flex items-center gap-1.5 pt-5 text-xs font-bold text-brand">
                  Read more <ArrowRight className="h-3.5 w-3.5" />
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

const POSTS = [
  {
    title: 'How to build a portfolio recruiters actually open',
    excerpt: 'Three projects, one README template, and the order to show them in.',
    tag: 'Careers',
    tagBg: 'bg-[#0f9d58]',
    date: 'Apr 18, 2025',
    img: 'https://cdn.magicpatterns.com/patterns/generated-images/be9bdacf-427e-4b86-9abc-87796d55dec3.jpg',
  },
  {
    title: 'Learning SQL in 30 days: a practical schedule',
    excerpt: 'Daily 40-minute sessions that take you from SELECT to window functions.',
    tag: 'Data',
    tagBg: 'bg-brand',
    date: 'Apr 09, 2025',
    img: 'https://cdn.magicpatterns.com/patterns/generated-images/9d356a42-5f62-4613-aa3b-347f8bacf20a.jpg',
  },
  {
    title: 'Why study groups beat solo learning for coding',
    excerpt: 'What we learned from 7,000 learners about accountability and pace.',
    tag: 'Community',
    tagBg: 'bg-[#0f9d58]',
    date: 'Mar 27, 2025',
    img: 'https://cdn.magicpatterns.com/patterns/generated-images/dd28eb3d-4a3b-45ec-8c7f-a2ce15ed9e01.jpg',
  },
]
