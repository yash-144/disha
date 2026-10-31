import React, { useState, useMemo } from 'react'
import {
  Search,
  ChevronDown,
  GraduationCap,
  Star,
  Globe,
  User,
  ArrowRight,
  Sparkles,
  BookOpen,
  Code2,
  CheckCircle,
  ExternalLink,
  Laptop,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

const HERO_IMG = 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=700&q=80'

const POPULAR_SEARCH_TAGS = ['React 19', 'SQL Indexing', 'AWS Cloud', 'Figma Tokens', 'Go Microservices']

export function HeroSection() {
  const {
    searchQuery,
    setSearchQuery,
    navigateTo,
    courses,
    setActiveCourseDetail,
    addToast,
  } = useApp()

  const [selectedCategory, setSelectedCategory] = useState('All')
  const [showDropdown, setShowDropdown] = useState(false)
  const [isSearchFocused, setIsSearchFocused] = useState(false)

  // Real-time suggestions based on user input
  const suggestions = useMemo(() => {
    if (!searchQuery.trim()) return []
    return courses
      .filter(
        (c) =>
          c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.categoryLabel.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .slice(0, 4)
  }, [searchQuery, courses])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigateTo('courses')
  }

  const handleTagClick = (tag: string) => {
    setSearchQuery(tag)
    navigateTo('courses')
  }

  return (
    <section className="relative overflow-hidden border-b-4 border-ink pb-16 text-ink font-mono">
      {/* Grid Blueprint Background Pattern */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.07] bg-grid-pattern" />

      <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 pt-10 sm:px-6 lg:grid-cols-[1.15fr_1fr]">
        {/* Left Column */}
        <div>
          {/* Trust Badge */}
          <div className="inline-flex items-center gap-2 border-2 border-ink bg-white px-3 py-1 text-xs font-bold shadow-[2.5px_2.5px_0_#0d1b3e] mb-4">
            <span className="flex h-2 w-2 rounded-full bg-[#0f9d58] animate-ping" />
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span>Over 7,000+ engineers enrolled worldwide</span>
          </div>

          <h1 className="text-[32px] font-bold leading-tight tracking-tight text-brand sm:text-[46px]">
            Unlock your potential with{' '}
            <span className="block text-ink">SkillsUp's skills development courses.</span>
          </h1>

          <p className="mt-5 max-w-lg text-xs leading-relaxed text-muted sm:text-sm">
            We offer a rich tapestry of skills development courses and live instructor cohorts.
            Hone your abilities, sketch architectures on live interactive whiteboards, and accelerate
            your engineering career.
          </p>

          {/* Interactive Search Box with Real-Time Dropdown Suggestions */}
          <div className="relative mt-7 max-w-xl">
            <form
              onSubmit={handleSearchSubmit}
              className="relative z-20 flex flex-wrap items-center gap-2 border-2 border-ink bg-white p-1.5 text-sm shadow-[4px_4px_0_#0d1b3e] sm:flex-nowrap"
            >
              <div className="flex min-w-0 flex-1 items-center gap-2 pl-3">
                <Search className="h-4 w-4 shrink-0 text-gray-500" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setIsSearchFocused(true)}
                  placeholder="Search React, SQL, Cloud, UI Design..."
                  className="w-full min-w-0 bg-transparent py-2 text-xs font-bold text-ink outline-none placeholder:text-gray-400 placeholder:font-normal"
                />
              </div>

              {/* Category Dropdown */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="hidden items-center gap-1 border-l-2 border-ink/20 px-3 text-xs font-bold text-ink sm:flex"
                >
                  {selectedCategory} <ChevronDown className="h-3 w-3" />
                </button>
                {showDropdown && (
                  <div className="absolute right-0 top-full z-30 mt-2 w-48 border-2 border-ink bg-white p-1 shadow-[4px_4px_0_#0d1b3e]">
                    {['All', 'Web Dev', 'Database', 'Design', 'Cloud'].map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => {
                          setSelectedCategory(cat)
                          setShowDropdown(false)
                        }}
                        className="w-full text-left px-2.5 py-1.5 text-xs font-bold hover:bg-gray-100"
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="border-2 border-ink bg-[#0f9d58] px-7 py-2.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-[#0b7a43] hover:-translate-x-0.5 hover:-translate-y-0.5"
              >
                Search
              </button>
            </form>

            {/* Instant Suggestions Dropdown Menu */}
            {isSearchFocused && suggestions.length > 0 && (
              <div
                onMouseLeave={() => setIsSearchFocused(false)}
                className="absolute left-0 right-0 top-full z-30 mt-1 border-2 border-ink bg-white shadow-[6px_6px_0_#0d1b3e] divide-y divide-ink/10 animate-in fade-in"
              >
                <div className="bg-[#f5f7fc] px-3 py-1.5 text-[10px] font-bold text-gray-500 uppercase flex justify-between">
                  <span>Matching Bootcamps &amp; Syllabi</span>
                  <span>{suggestions.length} Found</span>
                </div>
                {suggestions.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => {
                      setActiveCourseDetail(c)
                      setIsSearchFocused(false)
                    }}
                    className="flex cursor-pointer items-center justify-between p-3 hover:bg-blue-50/60 transition"
                  >
                    <div>
                      <p className="text-xs font-bold text-ink">{c.title}</p>
                      <span className="text-[10px] text-brand font-bold">{c.categoryLabel}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-ink">{c.price}</span>
                      <span className="block text-[10px] text-amber-500 font-bold">★ {c.rating}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Search Tag Pills */}
          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[11px]">
            <span className="text-muted font-bold">Trending:</span>
            {POPULAR_SEARCH_TAGS.map((tag) => (
              <button
                key={tag}
                onClick={() => handleTagClick(tag)}
                className="border border-ink bg-white px-2 py-0.5 text-[10px] font-bold text-ink shadow-[1px_1px_0_#0d1b3e] transition hover:bg-brand hover:text-white"
              >
                {tag}
              </button>
            ))}
          </div>

          {/* Direct LMS Feature Links */}
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigateTo('dashboard', 'overview')}
              className="flex items-center gap-2 border-2 border-ink bg-white px-4 py-2 text-xs font-bold text-ink shadow-[2.5px_2.5px_0_#0d1b3e] hover:bg-gray-100 transition"
            >
              <Laptop className="h-4 w-4 text-brand" /> Launch LMS Workspace
            </button>
            <button
              onClick={() => navigateTo('live-classes')}
              className="flex items-center gap-2 border-2 border-ink bg-brand px-4 py-2 text-xs font-bold text-white shadow-[2.5px_2.5px_0_#0d1b3e] hover:bg-brand-dark transition"
            >
              <span className="h-2 w-2 rounded-full bg-red-400 animate-ping" />
              Join Live Classes
            </button>
          </div>

          {/* Key Metric Stats */}
          <div className="mt-9 flex gap-8 sm:gap-12 pl-2">
            <div className="flex flex-col items-center text-center">
              <GraduationCap className="h-7 w-7 text-[#0f9d58]" />
              <span className="mt-1.5 text-base font-bold leading-none">30K+</span>
              <span className="mt-1 text-[11px] text-muted font-bold">Graduates</span>
            </div>
            <div className="flex flex-col items-center text-center">
              <Star className="h-6 w-6 fill-[#0f9d58] text-[#0f9d58]" />
              <span className="mt-1.5 text-base font-bold leading-none">4.9/5</span>
              <span className="mt-1 text-[11px] text-muted font-bold">Avg. Rating</span>
            </div>
            <div className="flex flex-col items-center text-center">
              <Globe className="h-6 w-6 text-brand" />
              <span className="mt-1.5 text-base font-bold leading-none">27+</span>
              <span className="mt-1 text-[11px] text-muted font-bold">Countries</span>
            </div>
          </div>
        </div>

        {/* Right Column: Hero Graphic with Neo-Brutal Stacks */}
        <div className="relative mx-auto aspect-square w-full max-w-[420px]">
          <div className="absolute inset-2 translate-x-3 translate-y-3 rounded-2xl bg-[#0f9d58] border-2 border-ink" />
          <div className="absolute inset-2 overflow-hidden rounded-2xl border-4 border-ink bg-white shadow-xl">
            <img
              src={HERO_IMG}
              alt="Students collaborating"
              className="h-full w-full object-cover object-top"
            />
          </div>

          {/* Floating Course Count Badge */}
          <div className="absolute -right-2 top-[18%] flex items-center gap-2 border-2 border-ink bg-[#0f9d58] px-3.5 py-2 text-white shadow-[4px_4px_0_#0d1b3e]">
            <span className="text-xl font-bold">{courses.length}+</span>
            <span className="text-[10px] leading-tight font-bold">
              Industry
              <br />
              Bootcamps
            </span>
          </div>

          {/* Floating Tag */}
          <div className="absolute left-[6%] top-[6%] flex h-11 w-11 items-center justify-center border-2 border-ink bg-brand text-xs font-bold text-white shadow-[3px_3px_0_#0d1b3e]">
            AI
          </div>

          {/* Floating Happy Learners Badge */}
          <div className="absolute -left-3 bottom-[10%] flex items-center gap-3 border-2 border-ink bg-white px-4 py-2.5 text-ink shadow-[5px_5px_0_#0d1b3e]">
            <span className="flex h-9 w-9 items-center justify-center border-2 border-ink bg-brand text-white shadow-[1px_1px_0_#0d1b3e]">
              <User className="h-4 w-4" />
            </span>
            <div>
              <p className="text-lg font-bold leading-none">7,000+</p>
              <p className="text-[10px] text-muted font-bold">Active Cohort Learners</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
