import React from 'react'
import { Header } from '../common/Header'
import { HeroSection } from './HeroSection'
import { WhyDishaSection } from './WhyDishaSection'
import { SolutionsSection } from './SolutionsSection'
import { FaqSection } from './FaqSection'
import { CourseCatalog } from './CourseCatalog'
import { LiveClassesSection } from './LiveClassesSection'
import { BlogSection } from './BlogSection'
import { ContactSection } from './ContactSection'
import { Footer } from '../common/Footer'
import { useApp } from '../../context/AppContext'

export function LandingView() {
  const { currentView } = useApp()

  if (currentView === 'courses') {
    return (
      <div className="min-h-screen bg-white text-slate-900 font-sans">
        <Header />
        <CourseCatalog isFullPage={true} />
        <Footer />
      </div>
    )
  }

  if (currentView === 'live-classes') {
    return (
      <div className="min-h-screen bg-white text-slate-900 font-sans">
        <Header />
        <LiveClassesSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'blogs') {
    return (
      <div className="min-h-screen bg-white text-slate-900 font-sans">
        <Header />
        <BlogSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'about') {
    return (
      <div className="min-h-screen bg-white text-slate-900 font-sans">
        <Header />
        <WhyDishaSection />
        <SolutionsSection />
        <Footer />
      </div>
    )
  }

  if (currentView === 'contact') {
    return (
      <div className="min-h-screen bg-white text-slate-900 font-sans">
        <Header />
        <ContactSection />
        <Footer />
      </div>
    )
  }

  // Default Minimalist Landing Page (following reference architecture)
  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-white text-slate-900 font-sans relative">
      {/* 1. Cinematic Hero Section with video background & top floating frosted glass navbar */}
      <HeroSection />

      {/* 2. Signature Section 1: /WHY DISHA */}
      <div id="why-disha">
        <WhyDishaSection />
      </div>

      {/* 3. Signature Section 2: /SOLUTIONS */}
      <div id="solutions">
        <SolutionsSection />
      </div>

      {/* 4. Minimalist FAQs Section */}
      <div id="faqs">
        <FaqSection />
      </div>

      {/* 5. Minimalist Aesthetic Footer with Giant DISHA Wordmark */}
      <Footer />
    </div>
  )
}
