import React, { useState, useMemo } from 'react'
import {
  Code2,
  Database,
  Puzzle,
  Cloud,
  Briefcase,
  Lock,
  Star,
  CheckCircle,
  Eye,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { Course } from '../../types'

const ICON_MAP: Record<string, React.ElementType> = {
  Code2,
  Database,
  Palette: Puzzle,
  Cloud,
  Briefcase,
  Lock,
}

export function CourseCatalog({ isFullPage = false }: { isFullPage?: boolean }) {
  const {
    courses,
    searchQuery,
    setSearchQuery,
    setActiveCourseDetail,
    enrollInCourse,
    enrolledCourseIds,
    navigateTo,
  } = useApp()

  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedLevel, setSelectedLevel] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'rating' | 'price-asc' | 'reviews'>('rating')

  const filteredCourses = useMemo(() => {
    return courses
      .filter((c) => {
        const matchesQuery =
          !searchQuery.trim() ||
          c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.instructorName.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesCategory = selectedCategory === 'all' || c.category === selectedCategory
        const matchesLevel = selectedLevel === 'all' || c.level === selectedLevel
        return matchesQuery && matchesCategory && matchesLevel
      })
      .sort((a, b) => {
        if (sortBy === 'rating') return b.rating - a.rating
        if (sortBy === 'price-asc') {
          const pA = parseInt(a.price.replace(/[^\d]/g, '')) || 0
          const pB = parseInt(b.price.replace(/[^\d]/g, '')) || 0
          return pA - pB
        }
        return parseInt(b.reviewsCount.replace(/[^\d]/g, '')) - parseInt(a.reviewsCount.replace(/[^\d]/g, ''))
      })
  }, [courses, searchQuery, selectedCategory, selectedLevel, sortBy])

  const visibleCourses = isFullPage ? filteredCourses : filteredCourses.slice(0, 4)

  return (
    <section className="mx-auto max-w-6xl px-4 py-24 sm:px-8 font-sans bg-white">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            / CURATED BOOTCAMPS & SYLLABI
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-normal tracking-tight text-slate-900 leading-[1.3]">
            <span className="font-semibold text-slate-950">Master production skills</span> with verified mentor guidance.
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-500 font-normal max-w-xl">
            Zero fluff. Interactive whiteboard cohorts, real code reviews, and smart contract verifiable capstones.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-full bg-slate-100 p-1 text-xs">
            {['all', 'web', 'cloud', 'data'].map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-full px-4 py-1.5 font-medium transition ${
                  selectedCategory === cat
                    ? 'bg-white text-slate-900 shadow-sm font-semibold'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {cat === 'all' ? 'All Tracks' : cat.toUpperCase()}
              </button>
            ))}
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 outline-none shadow-xs"
          >
            <option value="rating">Top Rated (4.8+)</option>
            <option value="reviews">Most Popular</option>
            <option value="price-asc">Price: Low to High</option>
          </select>
        </div>
      </div>

      {/* Courses Cards Grid (Minimalist Aesthetic) */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {visibleCourses.map((c) => {
          const Icon = ICON_MAP[c.iconName] || Code2
          const isEnrolled = enrolledCourseIds.includes(c.id)

          return (
            <article
              key={c.id}
              className="group flex flex-col justify-between rounded-3xl bg-slate-50/60 border border-slate-100 overflow-hidden transition-all duration-300 hover:bg-white hover:shadow-xl hover:shadow-slate-100 hover:-translate-y-1.5"
            >
              {/* Card Banner */}
              <div className="relative aspect-[16/10] overflow-hidden bg-gradient-to-br from-slate-800 to-slate-950 flex items-center justify-center p-6">
                <span className="absolute left-3.5 top-3.5 rounded-full bg-white/20 border border-white/25 backdrop-blur-md px-2.5 py-0.5 text-[10px] font-medium text-white">
                  {c.badge || 'Certificate'}
                </span>
                <span className="absolute right-3.5 top-3.5 text-[10px] font-medium text-white/70">
                  {c.duration}
                </span>
                <Icon className="h-12 w-12 text-white/90 group-hover:scale-110 transition-transform duration-300" strokeWidth={1.5} />
              </div>

              {/* Card Content */}
              <div className="flex flex-1 flex-col p-5">
                <div className="flex items-center justify-between text-[11px] mb-2">
                  <span className="font-semibold text-blue-600">{c.categoryLabel}</span>
                  <span className="text-slate-400 font-medium">{c.level}</span>
                </div>

                <h3 className="text-sm font-semibold leading-snug text-slate-900 group-hover:text-blue-600 transition-colors">
                  {c.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-500 line-clamp-2 font-normal">
                  {c.desc}
                </p>

                {/* Rating & Instructor */}
                <div className="mt-4 flex items-center justify-between text-xs border-t border-slate-100 pt-3">
                  <div className="flex items-center gap-1">
                    <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    <span className="font-semibold text-slate-900">{c.rating}</span>
                    <span className="text-[10px] text-slate-400">({c.reviewsCount})</span>
                  </div>
                  <span className="text-[11px] text-slate-500">{c.instructorName.split(' ')[0]}</span>
                </div>

                {/* Price and Actions */}
                <div className="mt-4 pt-2 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-bold text-slate-900">{c.price}</span>
                    <span className="ml-1 text-[11px] text-slate-400 line-through">{c.originalPrice}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveCourseDetail(c)}
                      title="View Details"
                      className="rounded-full p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition"
                    >
                      <Eye className="h-4 w-4" />
                    </button>

                    {isEnrolled ? (
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700">
                        Enrolled
                      </span>
                    ) : (
                      <button
                        onClick={() => enrollInCourse(c.id)}
                        className="rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition"
                      >
                        Enroll
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </article>
          )
        })}
      </div>

      {!isFullPage && (
        <div className="text-center mt-12">
          <button
            onClick={() => navigateTo('courses')}
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-xs font-semibold text-slate-900 shadow-sm hover:bg-slate-50 hover:shadow transition"
          >
            <span>View All 60+ Industry Courses & Syllabi</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </section>
  )
}
