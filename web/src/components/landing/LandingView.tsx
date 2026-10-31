import React, { useState, useEffect } from 'react'
import { Header } from '../common/Header'
import { HeroSection } from './HeroSection'
import { MarqueeBanner } from './MarqueeBanner'
import { CategorySection } from './CategorySection'
import { BenefitsSection } from './BenefitsSection'
import { CourseCatalog } from './CourseCatalog'
import { LiveClassesSection } from './LiveClassesSection'
import { LmsPreviewSection } from './LmsPreviewSection'
import { TestimonialsSection } from './TestimonialsSection'
import { FaqSection } from './FaqSection'
import { TeamSection } from './TeamSection'
import { BlogSection } from './BlogSection'
import { NewsletterSection } from './NewsletterSection'
import { ContactSection } from './ContactSection'
import { Footer } from '../common/Footer'
import { useApp } from '../../context/AppContext'
import { ArrowUp } from 'lucide-react'

export function LandingView() {
  const { currentView, navigateTo } = useApp()
  const [showScrollTop, setShowScrollTop] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (currentView === 'courses') {
    return (
      <div className="min-h-screen bg-[#f5f5f5] text-ink font-mono">
        <Header />
        <CourseCatalog isFullPage={true} />
        <Footer />
      </div>
    )
  }

  if (currentView === 'live-classes') {
    return (
      <div className="min-h-screen bg-[#f5f5f5] text-ink font-mono">
        <Header />
        <LiveClassesSection />
        <LmsPreviewSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'blogs') {
    return (
      <div className="min-h-screen bg-[#f5f5f5] text-ink font-mono">
        <Header />
        <BlogSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'about') {
    return (
      <div className="min-h-screen bg-[#f5f5f5] text-ink font-mono">
        <Header />
        <TeamSection />
        <BenefitsSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'contact') {
    return (
      <div className="min-h-screen bg-[#f5f5f5] text-ink font-mono">
        <Header />
        <ContactSection />
        <Footer />
      </div>
    )
  }

  // Default Landing Page ('landing')
  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-[#f5f5f5] text-ink font-mono relative">
      <Header />
      <HeroSection />
      <MarqueeBanner />
      <CategorySection />
      <BenefitsSection />
      <CourseCatalog />
      <div className="text-center pb-12">
        <button
          onClick={() => navigateTo('courses')}
          className="border-2 border-ink bg-white px-5 py-2 text-xs font-bold text-brand shadow-[3px_3px_0_#0d1b3e] hover:bg-gray-50 transition"
        >
          View all 60+ industry courses &amp; syllabi →
        </button>
      </div>

      {/* Real-time cohort video & schedule */}
      <LiveClassesSection />

      {/* Interactive LMS Canvas & Assessment Test Drive */}
      <LmsPreviewSection />

      {/* Social Proof */}
      <TestimonialsSection />

      {/* Instructors & Mentors */}
      <TeamSection />

      {/* Interactive FAQ */}
      <FaqSection />

      {/* Technical Blog */}
      <BlogSection />

      {/* Newsletter */}
      <NewsletterSection />

      {/* Contact */}
      <ContactSection />

      {/* Footer */}
      <Footer />

      {/* Floating Scroll-to-Top Button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          aria-label="Scroll to top"
          className="fixed bottom-6 right-6 z-40 flex h-10 w-10 items-center justify-center border-2 border-ink bg-[#0f9d58] text-white shadow-[3px_3px_0_#0d1b3e] transition hover:-translate-y-1 hover:bg-[#0b7a43]"
        >
          <ArrowUp className="h-5 w-5" />
        </button>
      )}
    </div>
  )
}
