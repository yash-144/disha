import React from 'react'
import { ArrowUpRight, HelpCircle } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function Footer() {
  const { navigateTo } = useApp()

  const handleFaqClick = (e: React.MouseEvent) => {
    e.preventDefault()
    const faqElement = document.getElementById('faqs')
    if (faqElement) {
      faqElement.scrollIntoView({ behavior: 'smooth' })
    } else {
      navigateTo('landing')
      setTimeout(() => {
        document.getElementById('faqs')?.scrollIntoView({ behavior: 'smooth' })
      }, 200)
    }
  }

  return (
    <footer className="w-full bg-slate-50 border-t border-slate-200/70 pt-16 sm:pt-24 pb-0 font-sans select-none overflow-hidden relative">
      {/* Full-Width Inner Container */}
      <div className="w-full px-6 sm:px-12 md:px-16 lg:px-24 flex flex-col justify-between">

        {/* Top Information & Actions Row (Clean, Only FAQs & Register as requested) */}
        <div className="relative z-10 w-full max-w-[1600px] mx-auto flex flex-col lg:flex-row lg:items-start justify-between gap-10">

          {/* Left Column: Brand (DISHA in bold capital) & Mission Statement */}
          <div className="max-w-xl">
            <div className="mb-4">
              <span className="text-3xl sm:text-4xl font-black tracking-widest text-slate-900 uppercase">
                DISHA
              </span>
            </div>
            <p className="text-sm sm:text-base md:text-lg font-normal text-slate-600 leading-relaxed max-w-lg">
              Enterprise multi-campus student early-warning &amp; accountable intervention platform.
              Operating under the unyielding principle of{' '}
              <strong className="font-semibold text-slate-900">"No Alert Without Action."</strong>
            </p>
          </div>

          {/* Right Column: Only FAQs & Register as requested */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 sm:gap-8">
            {/* FAQs Link */}
            <a
              href="#faqs"
              onClick={handleFaqClick}
              className="group flex items-center gap-2 text-sm sm:text-base font-semibold text-slate-600 hover:text-slate-900 transition"
            >
              <HelpCircle className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
              <span>Read FAQs</span>
              <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </a>

            {/* Register CTA Pill */}
            <button
              onClick={() => navigateTo('login')}
              className="group flex items-center gap-3.5 rounded-full bg-slate-900 px-7 py-3.5 text-xs sm:text-sm font-semibold text-white shadow-lg hover:bg-slate-800 transition hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <span>Register for DISHA</span>
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 text-white group-hover:rotate-45 transition-transform duration-200">
                <ArrowUpRight className="h-3.5 w-3.5" />
              </div>
            </button>
          </div>

        </div>

        {/* Center / Bottom: Full Size Edge-to-Edge DISHA Wordmark with Vertical Gradient */}
        <div className="relative w-full mt-16 sm:mt-24 flex flex-col items-center justify-end pointer-events-none">
          {/* Subtle Ambient Glow */}
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-full max-w-[1200px] h-64 bg-gradient-to-b from-blue-500/10 via-indigo-500/5 to-transparent blur-3xl pointer-events-none" />

          {/* Massive Edge-to-Edge Wordmark Halfway into Bottom */}
          <div className="w-full text-center overflow-hidden leading-none select-none">
            <h1
              className="text-[26vw] font-black tracking-[-0.07em] uppercase whitespace-nowrap leading-[0.68] translate-y-[28%] bg-gradient-to-b from-slate-950 via-slate-900/90 to-transparent bg-clip-text text-transparent"
              style={{
                WebkitMaskImage: 'linear-gradient(to top, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.7) 40%, rgba(0,0,0,1) 100%)',
                maskImage: 'linear-gradient(to top, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.7) 40%, rgba(0,0,0,1) 100%)',
              }}
            >
              DISHA
            </h1>
          </div>
        </div>

      </div>
    </footer>
  )
}
