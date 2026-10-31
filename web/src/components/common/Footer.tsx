import React from 'react'
import { GraduationCap, ArrowUp } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function Footer() {
  const { navigateTo } = useApp()

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <footer className="border-t-4 border-ink bg-white py-12 text-ink">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-10 sm:grid-cols-2 md:grid-cols-5">
          {/* Brand Info */}
          <div className="md:col-span-2">
            <span className="text-2xl font-bold tracking-tight">
              <span className="text-[#0f9d58]">Skills</span>
              <span className="text-brand">U</span>
              <span className="text-[#0f9d58]">P</span>
            </span>
            <p className="mt-3 max-w-sm text-xs leading-relaxed text-muted">
              Next-generation hands-on learning platform for software engineers, data architects, and
              digital product designers. Live interactive cohorts &amp; self-paced masterclasses.
            </p>
            <div className="mt-4 flex items-center gap-3 text-xs text-muted">
              <span>© 2025 SkillsUp Academy Inc. All rights reserved.</span>
            </div>
          </div>

          {/* Quick Nav */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink">Explore</h4>
            <ul className="mt-3 space-y-2 text-xs font-medium text-muted">
              <li>
                <button onClick={() => navigateTo('courses')} className="hover:text-brand">
                  Course Catalog
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('live-classes')} className="hover:text-brand">
                  Live Stream Schedule
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('dashboard', 'overview')} className="hover:text-brand">
                  LMS Dashboard
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('dashboard', 'quizzes')} className="hover:text-brand">
                  Interactive Quizzes
                </button>
              </li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink">Tracks</h4>
            <ul className="mt-3 space-y-2 text-xs font-medium text-muted">
              <li>
                <button onClick={() => navigateTo('courses')} className="hover:text-brand">
                  Full-Stack Web Dev
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('courses')} className="hover:text-brand">
                  Database &amp; SQL
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('courses')} className="hover:text-brand">
                  Cloud Infrastructure
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('courses')} className="hover:text-brand">
                  UI/UX Design Systems
                </button>
              </li>
            </ul>
          </div>

          {/* Company & Support */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink">Support</h4>
            <ul className="mt-3 space-y-2 text-xs font-medium text-muted">
              <li>
                <button onClick={() => navigateTo('about')} className="hover:text-brand">
                  About Us &amp; Team
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('blogs')} className="hover:text-brand">
                  Community Blog
                </button>
              </li>
              <li>
                <button onClick={() => navigateTo('contact')} className="hover:text-brand">
                  Contact Advisors
                </button>
              </li>
              <li>
                <button onClick={scrollToTop} className="flex items-center gap-1 text-brand font-bold">
                  Back to top <ArrowUp className="h-3 w-3" />
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  )
}
