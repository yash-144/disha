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
  Filter,
  SlidersHorizontal,
  Eye,
  X,
  Users,
  Clock,
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
    <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 font-mono">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0f9d58] px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              CURATED BOOTCAMPS
            </span>
            {searchQuery && (
              <span className="flex items-center gap-1 text-xs text-brand font-bold">
                Filtered by "{searchQuery}"
                <button
                  onClick={() => setSearchQuery('')}
                  className="rounded-full bg-gray-200 p-0.5 hover:bg-gray-300"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
          </div>
          <h2 className="mt-1 text-2xl font-bold text-brand sm:text-3xl">
            {isFullPage ? 'Complete Course Catalog & Masterclasses' : 'Explore Top-Rated Courses'}
          </h2>
          <p className="mt-2 text-xs text-muted sm:text-sm">
            Learn from verified production engineers with capstone projects and live whiteboard critiques.
          </p>
        </div>

        {/* Filter controls bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category tabs */}
          <div className="flex flex-wrap gap-1 border-2 border-ink bg-white p-1 shadow-[2px_2px_0_#0d1b3e]">
            {[
              { id: 'all', label: 'All Tracks' },
              { id: 'web', label: 'CS & Web' },
              { id: 'data', label: 'Data & SQL' },
              { id: 'design', label: 'UI/UX Design' },
              { id: 'cloud', label: 'Cloud' },
            ].map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-2.5 py-1 text-xs font-bold transition ${
                  selectedCategory === cat.id
                    ? 'border border-ink bg-brand text-white shadow-xs'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Level Filter */}
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="border-2 border-ink bg-white px-2.5 py-1.5 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] outline-none"
          >
            <option value="all">All Levels</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>

          {/* Sort dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] outline-none"
          >
            <option value="rating">Top Rated (4.8+)</option>
            <option value="reviews">Most Reviewed</option>
            <option value="price-asc">Price: Low to High</option>
          </select>
        </div>
      </div>

      {/* Courses Cards Grid */}
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {visibleCourses.map((c) => {
          const Icon = ICON_MAP[c.iconName] || Code2
          const isEnrolled = enrolledCourseIds.includes(c.id)

          return (
            <article
              key={c.id}
              className="flex flex-col justify-between overflow-hidden border-2 border-ink bg-white shadow-[4px_4px_0_#0d1b3e] transition-all duration-150 hover:-translate-x-0.5 hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
            >
              {/* Card Banner */}
              <div className={`relative flex aspect-[16/9] items-center justify-center border-b-2 border-ink ${c.accentBg}`}>
                <span className="absolute left-3 top-3 flex items-center gap-1 border border-ink bg-white px-2 py-0.5 text-[10px] font-bold text-ink shadow-[1px_1px_0_#0d1b3e]">
                  <Lock className="h-2.5 w-2.5" /> {c.badge || 'Certificate'}
                </span>
                <span className="absolute right-3 top-3 border border-white/40 bg-black/50 px-2 py-0.5 text-[10px] font-mono text-white backdrop-blur-xs">
                  {c.duration}
                </span>
                <Icon className="h-14 w-14 text-white drop-shadow" strokeWidth={1.5} />
              </div>

              {/* Card Content */}
              <div className="flex flex-1 flex-col p-4">
                <div className="flex items-center justify-between text-[10px] font-bold">
                  <span className="uppercase tracking-wider text-brand">{c.categoryLabel}</span>
                  <span className="rounded bg-gray-100 px-1.5 py-0.2 text-gray-700">{c.level}</span>
                </div>

                <h3 className="mt-2 text-sm font-bold leading-snug text-ink">{c.title}</h3>
                <p className="mt-1.5 text-[11px] leading-relaxed text-muted line-clamp-2">{c.desc}</p>

                {/* Rating & Instructor */}
                <div className="mt-3 flex items-center justify-between text-xs border-y border-ink/10 py-1.5">
                  <div className="flex items-center gap-1">
                    <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    <span className="font-bold text-ink">{c.rating}</span>
                    <span className="text-[10px] text-muted font-normal">({c.reviewsCount})</span>
                  </div>
                  <span className="text-[10px] text-gray-600 font-bold">{c.instructorName.split(' ')[0]} (Mentor)</span>
                </div>

                {/* Price and Actions */}
                <div className="mt-auto pt-4 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-bold text-ink">{c.price}</span>
                    <span className="ml-1 text-[11px] text-gray-400 line-through">{c.originalPrice}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setActiveCourseDetail(c)}
                      title="View Syllabus & Details"
                      className="border border-ink bg-[#f5f7fc] p-1.5 text-ink shadow-[1px_1px_0_#0d1b3e] hover:bg-white"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </button>

                    {isEnrolled ? (
                      <span className="flex items-center gap-1 border border-ink bg-emerald-100 px-2 py-1 text-[10px] font-bold text-emerald-900 shadow-xs">
                        <CheckCircle className="h-3 w-3" /> Enrolled
                      </span>
                    ) : (
                      <button
                        onClick={() => enrollInCourse(c.id)}
                        className="border-2 border-ink bg-[#0f9d58] px-3.5 py-1 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
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
    </section>
  )
}
