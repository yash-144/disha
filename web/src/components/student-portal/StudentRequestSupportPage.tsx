import React, { useState } from 'react'
import {
  GraduationCap,
  Smile,
  Users,
  Leaf,
  ChevronRight,
  Calendar,
  Lock,
  Check,
  X,
  Sparkles,
  ShieldCheck,
  Clock,
  Video,
  MapPin,
  MessageSquare,
  ArrowRight,
  HelpCircle,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { useApp } from '../../context/AppContext'

interface StudentRequestSupportPageProps {
  demoMode: DemoMode
  onNavigateToCases?: () => void
}

export type SupportCategoryId =
  | 'academic-stress'
  | 'emotional-wellbeing'
  | 'adjustment-belonging'
  | 'personal-concerns'

interface CategoryItem {
  id: SupportCategoryId
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  iconColor: string
  iconBg: string
  accentBorder: string
}

const CATEGORIES: CategoryItem[] = [
  {
    id: 'academic-stress',
    title: 'Academic Stress',
    description: 'Feeling overwhelmed with studies, workload or exams',
    icon: GraduationCap,
    iconColor: 'text-[#7C3AED]',
    iconBg: 'bg-[#F3E8FF]',
    accentBorder: 'hover:border-[#DDD6FE]',
  },
  {
    id: 'emotional-wellbeing',
    title: 'Emotional Wellbeing',
    description: 'Feeling low, anxious, stressed or unmotivated',
    icon: Smile,
    iconColor: 'text-[#CA8A04]',
    iconBg: 'bg-[#FEF9C3]',
    accentBorder: 'hover:border-[#FEF08A]',
  },
  {
    id: 'adjustment-belonging',
    title: 'Adjustment & Belonging',
    description: 'Facing challenges in adjusting or feeling isolated',
    icon: Users,
    iconColor: 'text-[#2563EB]',
    iconBg: 'bg-[#DBEAFE]',
    accentBorder: 'hover:border-[#BFDBFE]',
  },
  {
    id: 'personal-concerns',
    title: 'Personal Concerns',
    description: 'Any other issue you\'d like to discuss in a safe space',
    icon: Leaf,
    iconColor: 'text-[#16A34A]',
    iconBg: 'bg-[#DCFCE7]',
    accentBorder: 'hover:border-[#BBF7D0]',
  },
]

export function StudentRequestSupportPage({
  demoMode,
  onNavigateToCases,
}: StudentRequestSupportPageProps) {
  const { addToast } = useApp()

  // Modal states
  const [selectedCategory, setSelectedCategory] = useState<SupportCategoryId | null>(null)
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false)
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false)

  // Form states
  const [description, setDescription] = useState('')
  const [preferredSupport, setPreferredSupport] = useState('counsellor')
  const [contactMode, setContactMode] = useState<'video' | 'in-person' | 'message'>('video')
  const [timeWindow, setTimeWindow] = useState('asap')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [submittedRef, setSubmittedRef] = useState('')

  // Booking form states
  const [selectedCounsellor, setSelectedCounsellor] = useState('Prof. Sharma (Faculty Mentor)')
  const [selectedDate, setSelectedDate] = useState('Tomorrow, 14 Oct')
  const [selectedSlot, setSelectedSlot] = useState('17:30')
  const [bookingConfirmed, setBookingConfirmed] = useState(false)

  // Demo Mode status adjustments
  const currentStep =
    demoMode === 'activeSupport'
      ? 3
      : demoMode === 'needsAttention'
      ? 2
      : isSubmitted
      ? 2
      : 1

  const handleOpenCategory = (catId: SupportCategoryId) => {
    setSelectedCategory(catId)
    setIsSubmitted(false)
    setDescription('')
    setIsRequestModalOpen(true)
  }

  const handleSubmitRequest = (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) {
      addToast('Information Needed', 'Please provide a short description of what you need help with.', 'info')
      return
    }

    const randomRef = `REQ-2025-${Math.floor(100 + Math.random() * 900)}`
    setSubmittedRef(randomRef)
    setIsSubmitted(true)
    addToast('Support Request Sent', `Your request ${randomRef} was submitted confidentially.`, 'success')
  }

  const handleConfirmBooking = () => {
    setBookingConfirmed(true)
    addToast('Session Scheduled', `One-on-one session confirmed for ${selectedDate} at ${selectedSlot}.`, 'success')
    setTimeout(() => {
      setIsBookingModalOpen(false)
      setBookingConfirmed(false)
    }, 1800)
  }

  const activeCategoryObj = CATEGORIES.find((c) => c.id === selectedCategory) || CATEGORIES[0]

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* MAIN TWO-COLUMN WORKSPACE MATCHING VISUAL REFERENCE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* ================= LEFT COLUMN ================= */}
        <div className="lg:col-span-7 xl:col-span-8 flex flex-col gap-4">
          {/* 1. Support Introduction Banner */}
          <section
            aria-label="Support Introduction"
            className="bg-[#EDE8FB] border border-[#DDD6FE]/70 rounded-3xl p-6 sm:p-7 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-2xs overflow-hidden relative"
          >
            {/* Left text block */}
            <div className="flex flex-col z-10 max-w-sm sm:max-w-md">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[#1E2433]">
                Need someone to talk to?
              </h2>
              <p className="text-xs sm:text-sm text-[#475569] font-normal mt-2 leading-relaxed">
                Request support from a counsellor, mentor, or wellbeing team. It&apos;s confidential and supportive.
              </p>
            </div>

            {/* Right illustration: girl with closed peaceful eyes hugging a soft purple heart */}
            <div className="w-36 h-36 sm:w-44 sm:h-44 shrink-0 relative flex items-center justify-center z-10">
              <svg viewBox="0 0 160 160" className="w-full h-full drop-shadow-xs" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Soft pastel halo in background */}
                <circle cx="80" cy="80" r="70" fill="#E4DCFA" />

                {/* Soft botanical leaves framing from sides */}
                <path d="M22 65 C16 45 32 35 46 42 C40 56 32 62 22 65 Z" fill="#FDE047" opacity="0.85" />
                <path d="M138 60 C146 42 130 30 116 38 C122 52 130 58 138 60 Z" fill="#6EE7B7" opacity="0.85" />
                <path d="M144 85 C152 70 140 60 128 66 C132 78 138 84 144 85 Z" fill="#FDE047" opacity="0.7" />
                <path d="M18 90 C10 75 22 65 34 72 C30 84 24 88 18 90 Z" fill="#6EE7B7" opacity="0.7" />

                {/* Body / Lilac sweater */}
                <path d="M40 145 C40 120 58 112 80 112 C102 112 120 120 120 145 C120 155 40 155 40 145 Z" fill="#C4B5FD" />

                {/* Neck & Face */}
                <rect x="73" y="98" width="14" height="18" rx="6" fill="#FCD34D" />
                <circle cx="80" cy="82" r="24" fill="#FDE68A" />

                {/* Dark flowing hair */}
                <path d="M58 80 C54 60 62 44 80 44 C98 44 106 60 102 80 C102 96 98 108 94 114 C90 114 86 86 80 86 C74 86 70 114 66 114 C62 108 58 96 58 80 Z" fill="#1E1B4B" />

                {/* Calm closed eyes with soft eyelashes & serene smile */}
                <path d="M70 82 Q75 86 76 82" stroke="#4338CA" strokeWidth="2" strokeLinecap="round" />
                <path d="M84 82 Q85 86 90 82" stroke="#4338CA" strokeWidth="2" strokeLinecap="round" />
                <path d="M76 92 Q80 96 84 92" stroke="#4338CA" strokeWidth="2" strokeLinecap="round" />

                {/* Rosy blush cheeks */}
                <circle cx="68" cy="88" r="3.5" fill="#FCA5A5" opacity="0.6" />
                <circle cx="92" cy="88" r="3.5" fill="#FCA5A5" opacity="0.6" />

                {/* Large soft lavender/purple heart being embraced by arms */}
                <path
                  d="M80 126 C80 126 56 112 56 94 C56 83 65 76 75 80 C80 82 80 84 80 84 C80 84 80 82 85 80 C95 76 104 83 104 94 C104 112 80 126 80 126 Z"
                  fill="#A78BFA"
                />

                {/* Arms gently hugging the heart */}
                <path d="M48 118 C54 104 66 102 76 106" stroke="#FDE68A" strokeWidth="6" strokeLinecap="round" fill="none" />
                <path d="M112 118 C106 104 94 102 84 106" stroke="#FDE68A" strokeWidth="6" strokeLinecap="round" fill="none" />
                <path d="M46 122 C52 108 64 106 74 110" stroke="#C4B5FD" strokeWidth="6" strokeLinecap="round" fill="none" />
                <path d="M114 122 C108 108 96 106 86 110" stroke="#C4B5FD" strokeWidth="6" strokeLinecap="round" fill="none" />
              </svg>
            </div>
          </section>

          {/* 2. Support Category Selection Section */}
          <section aria-label="Support Categories" className="flex flex-col gap-3">
            <div>
              <h3 className="text-base sm:text-lg font-bold text-[#1E2433] tracking-tight">
                What kind of support do you need?
              </h3>
              <p className="text-xs text-[#717E95] font-normal mt-0.5">
                Choose the option that best fits what you&apos;re going through.
              </p>
            </div>

            {/* 2x2 Category Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {CATEGORIES.map((cat) => {
                const IconComponent = cat.icon

                return (
                  <div
                    key={cat.id}
                    onClick={() => handleOpenCategory(cat.id)}
                    className={`bg-white rounded-2xl border border-gray-100/90 shadow-2xs hover:shadow-xs p-4 sm:p-5 flex items-center justify-between gap-3 cursor-pointer transition-all duration-200 group ${cat.accentBorder}`}
                  >
                    {/* Left: Icon container + Title & Description */}
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className={`w-12 h-12 rounded-2xl ${cat.iconBg} ${cat.iconColor} flex items-center justify-center shrink-0 transition-transform group-hover:scale-105`}>
                        <IconComponent className="w-6 h-6" />
                      </div>
                      <div className="flex flex-col min-w-0">
                        <h4 className="text-sm font-bold text-[#1E2433] group-hover:text-[#4338CA] transition-colors truncate">
                          {cat.title}
                        </h4>
                        <p className="text-xs text-[#64748B] font-normal mt-1 leading-snug line-clamp-2">
                          {cat.description}
                        </p>
                      </div>
                    </div>

                    {/* Right: Chevron */}
                    <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-[#6366F1] group-hover:translate-x-0.5 transition-all shrink-0 ml-1" />
                  </div>
                )
              })}
            </div>
          </section>

          {/* 3. Direct Session Booking Banner */}
          <section
            aria-label="Direct Session Booking"
            className="bg-[#F4F0FD] border border-[#E9D5FF]/80 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs mt-1"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#E9D5FF] text-[#7C3AED] flex items-center justify-center shrink-0">
                <Calendar className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <h4 className="text-sm font-bold text-[#1E2433]">
                  Prefer to book a session directly?
                </h4>
                <p className="text-xs text-[#64748B] font-normal mt-0.5">
                  Schedule a one-on-one conversation with a counsellor at a time that works for you.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsBookingModalOpen(true)}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-semibold transition shadow-xs shrink-0 self-start sm:self-center"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Book a Session</span>
              <ChevronRight className="w-3 h-3 text-gray-300" />
            </button>
          </section>
        </div>

        {/* ================= RIGHT COLUMN ================= */}
        <div className="lg:col-span-5 xl:col-span-4 flex flex-col gap-4">
          {/* 1. Support Journey Card */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs p-5 md:p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-[#1E2433] tracking-tight mb-4">
                Your Support Journey
              </h3>

              {/* Vertical Stepper Timeline */}
              <div className="flex flex-col gap-4 pl-1 relative">
                {/* Step 1: Submit a request */}
                <div className="flex items-start gap-3.5 relative">
                  {/* Vertical line down to step 2 */}
                  <div className={`absolute top-6 left-3 w-0.5 h-10 -ml-[1px] ${currentStep >= 2 ? 'bg-[#8B5CF6]' : 'bg-gray-200'}`} />

                  <div className="w-6 h-6 rounded-full bg-[#8B5CF6] text-white flex items-center justify-center shrink-0 shadow-2xs z-10 ring-2 ring-purple-100">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-[#1E2433]">Submit a request</span>
                    <span className="text-[11px] text-[#717E95] mt-0.5">Tell us what you need help with</span>
                  </div>
                </div>

                {/* Step 2: Get matched */}
                <div className="flex items-start gap-3.5 relative">
                  {/* Vertical line down to step 3 */}
                  <div className={`absolute top-6 left-3 w-0.5 h-10 -ml-[1px] ${currentStep >= 3 ? 'bg-[#8B5CF6]' : 'bg-gray-200'}`} />

                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 ${
                    currentStep >= 2
                      ? 'bg-[#8B5CF6] text-white ring-2 ring-purple-100'
                      : 'bg-white border-2 border-gray-300 text-transparent'
                  }`}>
                    {currentStep >= 2 ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />}
                  </div>
                  <div className="flex flex-col">
                    <span className={`text-xs font-bold ${currentStep >= 2 ? 'text-[#1E2433]' : 'text-gray-700'}`}>Get matched</span>
                    <span className="text-[11px] text-[#717E95] mt-0.5">We&apos;ll connect you with the right support person</span>
                  </div>
                </div>

                {/* Step 3: Schedule a session */}
                <div className="flex items-start gap-3.5 relative">
                  {/* Vertical line down to step 4 */}
                  <div className={`absolute top-6 left-3 w-0.5 h-10 -ml-[1px] ${currentStep >= 4 ? 'bg-[#8B5CF6]' : 'bg-gray-200'}`} />

                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 ${
                    currentStep >= 3
                      ? 'bg-[#8B5CF6] text-white ring-2 ring-purple-100'
                      : 'bg-white border-2 border-gray-300 text-transparent'
                  }`}>
                    {currentStep >= 3 ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />}
                  </div>
                  <div className="flex flex-col">
                    <span className={`text-xs font-bold ${currentStep >= 3 ? 'text-[#1E2433]' : 'text-gray-700'}`}>Schedule a session</span>
                    <span className="text-[11px] text-[#717E95] mt-0.5">Choose a convenient time</span>
                  </div>
                </div>

                {/* Step 4: Receive support */}
                <div className="flex items-start gap-3.5 relative">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 ${
                    currentStep >= 4
                      ? 'bg-[#8B5CF6] text-white ring-2 ring-purple-100'
                      : 'bg-white border-2 border-gray-300 text-transparent'
                  }`}>
                    {currentStep >= 4 ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />}
                  </div>
                  <div className="flex flex-col">
                    <span className={`text-xs font-bold ${currentStep >= 4 ? 'text-[#1E2433]' : 'text-gray-700'}`}>Receive support</span>
                    <span className="text-[11px] text-[#717E95] mt-0.5">Talk, get guidance and plan next steps</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Subtle Demo Status Note */}
            {demoMode === 'needsAttention' && (
              <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-amber-700 bg-amber-50/70 p-2.5 rounded-xl border border-amber-200/50">
                Notice: Follow-up check-in matching in progress based on your recent weekly pulse.
              </div>
            )}
            {demoMode === 'activeSupport' && (
              <div className="mt-4 pt-3 border-t border-gray-100 text-[11px] text-indigo-700 bg-indigo-50/70 p-2.5 rounded-xl border border-indigo-200/50">
                Active Mentor: Prof. Sharma is connected with your case. Follow-up scheduled for 14 Oct.
              </div>
            )}
          </div>

          {/* 2. Privacy Card */}
          <div className="bg-[#F0FDF4] border border-[#BBF7D0]/80 rounded-2xl p-4 flex items-center gap-3.5 shadow-2xs">
            <div className="w-10 h-10 rounded-xl bg-white border border-[#86EFAC] text-[#16A34A] flex items-center justify-center shrink-0 shadow-2xs">
              <Lock className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <h4 className="text-xs font-bold text-[#1E2433]">Your privacy matters</h4>
              <p className="text-[11px] text-[#475569] font-normal mt-0.5 leading-relaxed">
                Your request and conversations are confidential and handled with care.
              </p>
            </div>
          </div>

          {/* 3. Encouragement Card with Sprouting Plant */}
          <div className="bg-gradient-to-br from-white to-[#F5F2FE] border border-[#DDD6FE]/70 rounded-2xl p-4 sm:p-4.5 relative overflow-hidden shadow-2xs flex items-center justify-between gap-3">
            <div className="flex flex-col max-w-[210px] z-10">
              <h4 className="text-xs sm:text-sm font-bold text-[#1E2433] leading-snug">
                It&apos;s a brave step to ask for support.
              </h4>
              <p className="text-[11px] text-[#64748B] font-normal mt-1.5 leading-relaxed">
                You&apos;re prioritising your wellbeing — and that matters.
              </p>
            </div>

            {/* Fresh sprout vector illustration growing from soft purple hills */}
            <div className="w-20 h-20 shrink-0 relative flex items-end justify-center z-0">
              <svg viewBox="0 0 100 100" className="w-full h-full" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Purple curved landscape hills */}
                <path d="M0 90 C30 76 60 84 100 80 L100 100 L0 100 Z" fill="#C4B5FD" opacity="0.6" />
                <path d="M15 94 C45 84 75 88 100 86 L100 100 L15 100 Z" fill="#A78BFA" opacity="0.8" />

                {/* Sprout Stem */}
                <path d="M50 86 C50 66 52 50 54 36" stroke="#4ADE80" strokeWidth="4.5" strokeLinecap="round" />

                {/* Left leaf */}
                <path d="M52 56 C38 52 30 38 34 26 C46 28 50 42 52 56 Z" fill="#86EFAC" />

                {/* Right leaf */}
                <path d="M53 44 C66 40 76 28 72 16 C60 18 54 32 53 44 Z" fill="#4ADE80" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* ================= MODAL: SUPPORT REQUEST FORM ================= */}
      {isRequestModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`w-9 h-9 rounded-xl ${activeCategoryObj.iconBg} ${activeCategoryObj.iconColor} flex items-center justify-center`}>
                  {React.createElement(activeCategoryObj.icon, { className: 'w-5 h-5' })}
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-[#1E2433]">
                    {isSubmitted ? 'Request Submitted' : 'Request Support'}
                  </h3>
                  <span className="text-[11px] text-[#717E95]">
                    {isSubmitted ? `Reference ID: ${submittedRef}` : activeCategoryObj.title}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsRequestModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto flex flex-col gap-4">
              {!isSubmitted ? (
                <form id="support-request-form" onSubmit={handleSubmitRequest} className="flex flex-col gap-4">
                  {/* Category Switcher Pills */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1E2433]">Selected Category</label>
                    <div className="grid grid-cols-2 gap-2">
                      {CATEGORIES.map((cat) => (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={() => setSelectedCategory(cat.id)}
                          className={`px-3 py-2 rounded-xl text-xs font-semibold text-left transition flex items-center gap-2 border ${
                            selectedCategory === cat.id
                              ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-2xs'
                              : 'bg-gray-50/70 border-gray-200 text-gray-600 hover:bg-gray-100/60'
                          }`}
                        >
                          <span className={`w-2 h-2 rounded-full ${selectedCategory === cat.id ? 'bg-purple-600' : 'bg-gray-300'}`} />
                          <span className="truncate">{cat.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Description Textarea */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-[#1E2433]">
                        What would you like support with? <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[10px] text-gray-400">Confidential</span>
                    </div>
                    <textarea
                      rows={3}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Feel free to share as much or as little as you're comfortable with. For example, recent coursework pressure, difficulties with sleep, or transition challenges..."
                      className="w-full text-xs p-3 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400 transition resize-none placeholder:text-gray-400 text-gray-800"
                    />
                  </div>

                  {/* Preferred Support Team */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1E2433]">Preferred Support Team</label>
                    <select
                      value={preferredSupport}
                      onChange={(e) => setPreferredSupport(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-xl border border-gray-200 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-200"
                    >
                      <option value="counsellor">Counselling & Emotional Guidance Unit</option>
                      <option value="mentor">Assigned Faculty Mentor (Prof. Sharma)</option>
                      <option value="peer">Peer Mentorship Ambassador</option>
                      <option value="fastest">Whoever is available soonest</option>
                    </select>
                  </div>

                  {/* Preferred Contact Mode */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1E2433]">Preferred Meeting Format</label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setContactMode('video')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition ${
                          contactMode === 'video'
                            ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-2xs'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <Video className="w-4 h-4 text-purple-600" />
                        <span>Virtual Video</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setContactMode('in-person')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition ${
                          contactMode === 'in-person'
                            ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-2xs'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <MapPin className="w-4 h-4 text-blue-600" />
                        <span>In-Person</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setContactMode('message')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition ${
                          contactMode === 'message'
                            ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-2xs'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <MessageSquare className="w-4 h-4 text-emerald-600" />
                        <span>Secure Chat</span>
                      </button>
                    </div>
                  </div>

                  {/* Preferred Urgency */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1E2433]">Timeframe</label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setTimeWindow('asap')}
                        className={`px-3 py-2 rounded-xl text-[11px] font-semibold border transition ${
                          timeWindow === 'asap'
                            ? 'bg-amber-50 border-amber-300 text-amber-900'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        Within 24 hours
                      </button>
                      <button
                        type="button"
                        onClick={() => setTimeWindow('this_week')}
                        className={`px-3 py-2 rounded-xl text-[11px] font-semibold border transition ${
                          timeWindow === 'this_week'
                            ? 'bg-purple-50 border-purple-300 text-purple-900'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        This week
                      </button>
                      <button
                        type="button"
                        onClick={() => setTimeWindow('next_week')}
                        className={`px-3 py-2 rounded-xl text-[11px] font-semibold border transition ${
                          timeWindow === 'next_week'
                            ? 'bg-purple-50 border-purple-300 text-purple-900'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        Next week
                      </button>
                    </div>
                  </div>

                  {/* Confidentiality Notice */}
                  <div className="p-3 bg-[#F0FDF4] border border-[#BBF7D0] rounded-xl flex items-start gap-2.5 text-[11px] text-[#166534]">
                    <ShieldCheck className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
                    <p className="leading-relaxed">
                      Your request is shared exclusively with designated wellbeing personnel according to institutional privacy standards.
                    </p>
                  </div>
                </form>
              ) : (
                /* Success Confirmation View */
                <div className="flex flex-col items-center text-center py-4 gap-3">
                  <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center ring-4 ring-emerald-50">
                    <Check className="w-7 h-7 stroke-[3]" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-[#1E2433]">
                      We&apos;ve received your request!
                    </h4>
                    <p className="text-xs text-[#64748B] mt-1 max-w-sm">
                      A member of the wellbeing guidance team will review your notes and reach out within 24 hours.
                    </p>
                  </div>

                  <div className="w-full bg-[#FAFBFD] border border-gray-200 rounded-2xl p-4 text-left flex flex-col gap-2 mt-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Case Reference:</span>
                      <span className="font-mono font-bold text-[#1E2433]">{submittedRef}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Selected Concern:</span>
                      <span className="font-semibold text-[#1E2433]">{activeCategoryObj.title}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Status:</span>
                      <span className="text-xs bg-purple-100 text-purple-800 font-semibold px-2 py-0.5 rounded-full">
                        Matching Support Person
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-end gap-2">
              {!isSubmitted ? (
                <>
                  <button
                    type="button"
                    onClick={() => setIsRequestModalOpen(false)}
                    className="px-4 py-2 rounded-full text-xs font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    form="support-request-form"
                    className="px-5 py-2 rounded-full text-xs font-bold text-white bg-[#1E2433] hover:bg-[#2C3549] transition shadow-xs flex items-center gap-1.5"
                  >
                    <span>Submit Request</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => setIsRequestModalOpen(false)}
                    className="px-4 py-2 rounded-full text-xs font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                  >
                    Close
                  </button>
                  {onNavigateToCases && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsRequestModalOpen(false)
                        onNavigateToCases()
                      }}
                      className="px-5 py-2 rounded-full text-xs font-bold text-white bg-[#6366F1] hover:bg-[#4F46E5] transition shadow-xs flex items-center gap-1.5"
                    >
                      <span>View in My Cases</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ================= MODAL: DIRECT SESSION BOOKING ================= */}
      {isBookingModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Schedule 1-on-1 Session</h3>
                  <p className="text-[11px] text-[#717E95]">Confidential consultation slot</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsBookingModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4">
              {/* Counsellor Selection */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[#1E2433]">Select Advisor</label>
                <select
                  value={selectedCounsellor}
                  onChange={(e) => setSelectedCounsellor(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-gray-200 bg-white text-gray-800"
                >
                  <option value="Prof. Sharma (Faculty Mentor)">Prof. Sharma (Faculty Mentor)</option>
                  <option value="Dr. Rao (Campus Life Advisor)">Dr. Rao (Campus Life Advisor)</option>
                  <option value="Meera K. (Counselling Specialist)">Meera K. (Counselling Specialist)</option>
                </select>
              </div>

              {/* Date Selection */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[#1E2433]">Available Day</label>
                <div className="grid grid-cols-3 gap-2">
                  {['Tomorrow, 14 Oct', 'Friday, 17 Oct', 'Monday, 20 Oct'].map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setSelectedDate(d)}
                      className={`p-2 rounded-xl text-[11px] font-semibold border text-center transition ${
                        selectedDate === d
                          ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-2xs'
                          : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time Slots */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[#1E2433]">Available Time</label>
                <div className="grid grid-cols-4 gap-2">
                  {['10:00', '14:30', '16:00', '17:30'].map((slot) => (
                    <button
                      key={slot}
                      type="button"
                      onClick={() => setSelectedSlot(slot)}
                      className={`py-2 rounded-xl text-xs font-semibold border text-center transition ${
                        selectedSlot === slot
                          ? 'bg-purple-600 border-purple-600 text-white shadow-2xs'
                          : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {slot}
                    </button>
                  ))}
                </div>
              </div>

              {bookingConfirmed && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs text-emerald-800">
                  <Check className="w-4 h-4 text-emerald-600" />
                  <span>Session confirmed! Added to your upcoming calendar.</span>
                </div>
              )}
            </div>

            <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsBookingModalOpen(false)}
                className="px-4 py-2 rounded-full text-xs font-semibold text-gray-600 hover:bg-gray-200/60 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmBooking}
                disabled={bookingConfirmed}
                className="px-5 py-2 rounded-full text-xs font-bold text-white bg-[#1E2433] hover:bg-[#2C3549] transition shadow-xs flex items-center gap-1.5"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Confirm Session</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

