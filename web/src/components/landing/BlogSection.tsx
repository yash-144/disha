import React from 'react'
import { ArrowRight, Clock, User } from 'lucide-react'
import { BLOG_POSTS } from '../../mockData'
import { useApp } from '../../context/AppContext'

export function BlogSection() {
  const { setActiveBlogPost, navigateTo } = useApp()

  return (
    <section className="border-t-4 border-ink bg-[#f5f5f5]">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-brand">
              Knowledge Hub
            </span>
            <h2 className="mt-1 text-2xl font-bold leading-snug text-brand sm:text-[32px]">
              Insights &amp; ideas <span className="text-ink">from the SkillsUp blog.</span>
            </h2>
          </div>
          <button
            onClick={() => navigateTo('blogs')}
            className="text-xs font-bold text-brand underline underline-offset-4 hover:text-brand-dark"
          >
            All publications ({BLOG_POSTS.length})
          </button>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {BLOG_POSTS.map((p) => (
            <article
              key={p.id}
              onClick={() => setActiveBlogPost(p)}
              className="group flex cursor-pointer flex-col border-2 border-ink bg-white shadow-[4px_4px_0_#0d1b3e] transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
            >
              <div className="relative overflow-hidden border-b-2 border-ink">
                <img
                  src={p.img}
                  alt={p.title}
                  className="aspect-[16/10] w-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                <span
                  className={`absolute left-3 top-3 px-2 py-0.5 text-[10px] font-bold text-white shadow-xs ${p.tagBg}`}
                >
                  {p.tag}
                </span>
              </div>

              <div className="flex flex-1 flex-col p-5">
                <p className="flex items-center gap-3 text-[11px] text-muted">
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3" /> {p.author}
                  </span>
                  <span>·</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {p.readTime}
                  </span>
                </p>

                <h3 className="mt-2 text-sm font-bold leading-snug text-ink group-hover:text-brand">
                  {p.title}
                </h3>

                <p className="mt-2 text-xs leading-relaxed text-muted line-clamp-3">{p.excerpt}</p>

                <div className="mt-auto flex items-center gap-1.5 pt-5 text-xs font-bold text-brand">
                  <span>Read article</span>
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
