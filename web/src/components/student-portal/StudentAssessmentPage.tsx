import React, { useState } from 'react'
import {
  Smile,
  BookOpen,
  Users,
  Moon,
  Clock,
  Sparkles,
  CheckCircle2,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  HeartHandshake,
  ShieldCheck,
  Calendar,
  Award,
  HelpCircle,
  Play,
  Check,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { StudentPulseTakingView } from './StudentPulseTakingView'

interface StudentAssessmentPageProps {
  demoMode: DemoMode
  onRequestSupport?: () => void
  onNavigateToOverview?: () => void
}

interface Question {
  id: number
  category: 'emotional' | 'academic' | 'social' | 'lifestyle'
  categoryLabel: string
  text: string
  hint?: string
}

const ASSESSMENT_QUESTIONS: Question[] = [
  // Emotional Wellbeing
  {
    id: 1,
    category: 'emotional',
    categoryLabel: 'Emotional Wellbeing',
    text: 'Over the past two weeks, how often have you felt able to manage everyday stress effectively?',
    hint: 'Think about day-to-day challenges and your ability to bounce back.',
  },
  {
    id: 2,
    category: 'emotional',
    categoryLabel: 'Emotional Wellbeing',
    text: 'How frequently have you felt calm, relaxed, or centered in your daily routine?',
    hint: 'Consider moments when you felt at peace versus tense or overwhelmed.',
  },
  {
    id: 3,
    category: 'emotional',
    categoryLabel: 'Emotional Wellbeing',
    text: 'How often do you feel comfortable expressing your emotions to someone you trust?',
    hint: 'Whether with a mentor, peer, counsellor, or family member.',
  },

  // Academic Balance
  {
    id: 4,
    category: 'academic',
    categoryLabel: 'Academic Balance',
    text: 'How confident do you feel in balancing assignment deadlines and study requirements?',
    hint: 'Consider current course workloads, lab submissions, and exams.',
  },
  {
    id: 5,
    category: 'academic',
    categoryLabel: 'Academic Balance',
    text: 'How often are you able to take restful breaks without feeling guilty about coursework?',
    hint: 'True mental rest is essential for academic endurance.',
  },
  {
    id: 6,
    category: 'academic',
    categoryLabel: 'Academic Balance',
    text: 'When faced with difficult course concepts, how easily can you access academic help?',
    hint: 'Such as faculty office hours, peer study groups, or tutoring.',
  },

  // Social Connection
  {
    id: 7,
    category: 'social',
    categoryLabel: 'Social Connection',
    text: 'How often do you feel a genuine sense of belonging and community at university?',
    hint: 'Feeling valued as a part of your batch, campus clubs, or study cohorts.',
  },
  {
    id: 8,
    category: 'social',
    categoryLabel: 'Social Connection',
    text: 'If you needed emotional or practical help, how confident are you that someone would support you?',
    hint: 'Having at least one reliable person you can reach out to.',
  },
  {
    id: 9,
    category: 'social',
    categoryLabel: 'Social Connection',
    text: 'How frequently do you engage in meaningful social conversations with friends or peers?',
    hint: 'Beyond quick transactional messages about homework.',
  },

  // Sleep & Lifestyle
  {
    id: 10,
    category: 'lifestyle',
    categoryLabel: 'Sleep & Lifestyle',
    text: 'How satisfied are you with the quality and consistency of your sleep over the past week?',
    hint: 'Waking up feeling refreshed vs exhausted or having irregular hours.',
  },
  {
    id: 11,
    category: 'lifestyle',
    categoryLabel: 'Sleep & Lifestyle',
    text: 'How often do you incorporate physical movement, stretching, or outdoor walks into your week?',
    hint: 'Any gentle movement that gives your body a break from screens.',
  },
  {
    id: 12,
    category: 'lifestyle',
    categoryLabel: 'Sleep & Lifestyle',
    text: 'How nourished and hydrated do you feel throughout your typical study days?',
    hint: 'Regular meals, water intake, and mindful eating habits.',
  },
]

const SCALE_OPTIONS = [
  { value: 1, label: 'Rarely', description: 'Hardly ever in the past two weeks' },
  { value: 2, label: 'Sometimes', description: 'A few days over the last two weeks' },
  { value: 3, label: 'Often', description: 'About half the time' },
  { value: 4, label: 'Most of the time', description: 'Majority of days' },
  { value: 5, label: 'Almost Always', description: 'Nearly every day consistently' },
]

interface PastAssessment {
  id: string
  date: string
  title: string
  overallStatus: string
  scoreSummary: string
  highlight: string
}

const PAST_ASSESSMENTS: PastAssessment[] = [
  {
    id: 'pa-1',
    date: '09 Oct 2026',
    title: 'Mid-Semester Wellbeing Pulse',
    overallStatus: 'Balanced & Steady',
    scoreSummary: 'Overall Wellbeing Index: 78/100',
    highlight: 'Strong social connection and good recovery habits identified.',
  },
  {
    id: 'pa-2',
    date: '18 Sep 2026',
    title: 'Term Initial Self-Check',
    overallStatus: 'Moderate Academic Load',
    scoreSummary: 'Overall Wellbeing Index: 72/100',
    highlight: 'Sleep consistency suggested as primary focus area during exam prep.',
  },
  {
    id: 'pa-3',
    date: '28 Aug 2026',
    title: 'Orientation Baseline Check',
    overallStatus: 'Positive Orientation',
    scoreSummary: 'Overall Wellbeing Index: 82/100',
    highlight: 'High motivation and enthusiasm entering the 3rd year.',
  },
]

export function StudentAssessmentPage({
  demoMode,
  onRequestSupport,
  onNavigateToOverview,
}: StudentAssessmentPageProps) {
  // Primary Module Switcher: 'pulse' (Academic & Feedback) | 'wellbeing' (Reflection)
  const [moduleTab, setModuleTab] = useState<'pulse' | 'wellbeing'>('pulse')

  // Stepper State: 'landing' | 'in-progress' | 'review' | 'results'
  const [stage, setStage] = useState<'landing' | 'in-progress' | 'review' | 'results'>('landing')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({
    1: 4,
    2: 3,
    3: 4,
    4: 3,
    5: 2,
    6: 4,
    7: 4,
    8: 4,
    9: 3,
    10: 3,
    11: 3,
    12: 4,
  })

  // Start guided assessment
  const handleStartAssessment = (filterCategory?: string) => {
    if (filterCategory) {
      const idx = ASSESSMENT_QUESTIONS.findIndex((q) => q.category === filterCategory)
      setCurrentQuestionIndex(idx >= 0 ? idx : 0)
    } else {
      setCurrentQuestionIndex(0)
    }
    setStage('in-progress')
  }

  const handleSelectOption = (value: number) => {
    setAnswers((prev) => ({
      ...prev,
      [ASSESSMENT_QUESTIONS[currentQuestionIndex].id]: value,
    }))
  }

  const handleNext = () => {
    if (currentQuestionIndex < ASSESSMENT_QUESTIONS.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
    } else {
      setStage('review')
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1)
    }
  }

  const handleSubmitAssessment = () => {
    setStage('results')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const currentQ = ASSESSMENT_QUESTIONS[currentQuestionIndex]
  const currentAnswer = answers[currentQ?.id]
  const totalQuestions = ASSESSMENT_QUESTIONS.length
  const progressPercent = Math.round(((currentQuestionIndex + 1) / totalQuestions) * 100)

  return (
    <div className="flex-1 flex flex-col gap-5 font-sans select-none pb-8">
      {/* Top Module Navigation Bar */}
      <div className="bg-white rounded-2xl p-2 border border-purple-100 shadow-2xs flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setModuleTab('pulse')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              moduleTab === 'pulse'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Student Pulse Assessments
          </button>
          <button
            type="button"
            onClick={() => setModuleTab('wellbeing')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              moduleTab === 'wellbeing'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <HeartHandshake className="w-4 h-4" />
            Weekly Wellbeing Reflection
          </button>
        </div>

        <span className="hidden sm:inline-block text-[11px] text-gray-400 font-medium pr-3">
          {moduleTab === 'pulse' ? 'Academic & Anonymized Feedback' : 'Confidential Check-in'}
        </span>
      </div>

      {moduleTab === 'pulse' ? (
        <StudentPulseTakingView onBackToOverview={onNavigateToOverview} />
      ) : (
        <>
      {/* 1. INTRO / LANDING VIEW */}
      {stage === 'landing' && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Welcome Banner Card */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#EDE8FB] via-[#F3EDFC] to-[#FCEEF5] p-6 sm:p-8 border border-[#DDD6FE]/70 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="max-w-xl z-10">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-purple-200 text-purple-700 text-[11px] font-bold mb-3 shadow-2xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Confidential Self-Reflection</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1E2433]">
                Your wellbeing matters.
              </h2>
              <p className="text-xs sm:text-sm text-[#475569] font-medium mt-2 leading-relaxed">
                A few thoughtful questions can help you understand your current wellbeing, celebrate your strengths, and identify areas where you may want additional support.
              </p>

              {/* Badges & Action */}
              <div className="flex flex-wrap items-center gap-4 mt-5">
                <div className="flex items-center gap-1.5 text-xs text-[#64748B] font-semibold bg-white/70 px-3 py-1.5 rounded-full border border-purple-100">
                  <Clock className="w-4 h-4 text-purple-600" />
                  <span>5–7 minutes</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[#64748B] font-semibold bg-white/70 px-3 py-1.5 rounded-full border border-purple-100">
                  <HelpCircle className="w-4 h-4 text-purple-600" />
                  <span>12 guided questions</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[#64748B] font-semibold bg-white/70 px-3 py-1.5 rounded-full border border-purple-100">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>100% Private & Non-diagnostic</span>
                </div>
              </div>

              <div className="mt-6 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleStartAssessment()}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs sm:text-sm font-bold shadow-xs hover:shadow-sm transition transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Assessment</span>
                </button>
              </div>
            </div>

            {/* Peaceful Lotus / Mindful Sun Illustration */}
            <div className="w-48 h-48 sm:w-56 sm:h-56 shrink-0 relative flex items-center justify-center">
              <svg viewBox="0 0 160 160" className="w-full h-full overflow-visible" fill="none">
                <circle cx="80" cy="80" r="60" fill="#E9D5FF" opacity="0.45" />
                <circle cx="95" cy="70" r="50" fill="#FCE7F3" opacity="0.5" />
                <circle cx="65" cy="90" r="45" fill="#DBEAFE" opacity="0.4" />
                {/* Lotus Petals */}
                <path d="M80 35 C70 55 70 85 80 95 C90 85 90 55 80 35 Z" fill="#A855F7" opacity="0.8" />
                <path d="M55 50 C55 70 65 90 80 95 C70 80 60 65 55 50 Z" fill="#C084FC" opacity="0.75" />
                <path d="M105 50 C105 70 95 90 80 95 C90 80 100 65 105 50 Z" fill="#C084FC" opacity="0.75" />
                <path d="M40 70 C45 88 60 98 80 95 C62 90 50 78 40 70 Z" fill="#E879F9" opacity="0.7" />
                <path d="M120 70 C115 88 100 98 80 95 C98 90 110 78 120 70 Z" fill="#E879F9" opacity="0.7" />
                {/* Calm Base Ripple */}
                <ellipse cx="80" cy="115" rx="45" ry="10" fill="#DDD6FE" opacity="0.6" />
                <ellipse cx="80" cy="122" rx="30" ry="6" fill="#EDE9FE" opacity="0.8" />
              </svg>
            </div>
          </div>

          {/* 2. Assessment Categories Section */}
          <div>
            <div className="flex items-center justify-between mb-3.5">
              <div>
                <h3 className="text-base font-bold text-[#1E2433]">Assessment Categories</h3>
                <p className="text-xs text-[#717E95] font-medium">
                  Reflect across four holistic dimensions of student life.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Category 1: Emotional Wellbeing */}
              <div className="bg-white rounded-2xl p-5 border border-purple-100 shadow-2xs flex flex-col justify-between hover:border-purple-300 transition">
                <div>
                  <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-3.5">
                    <Smile className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#1E2433]">Emotional Wellbeing</h4>
                  <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed font-medium">
                    Stress regulation, daily emotional balance, and personal resilience.
                  </p>
                </div>
                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                    3 Questions
                  </span>
                  <button
                    type="button"
                    onClick={() => handleStartAssessment('emotional')}
                    className="text-xs font-bold text-purple-700 hover:text-purple-900 inline-flex items-center gap-1"
                  >
                    <span>Start</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Category 2: Academic Balance */}
              <div className="bg-white rounded-2xl p-5 border border-blue-100 shadow-2xs flex flex-col justify-between hover:border-blue-300 transition">
                <div>
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3.5">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#1E2433]">Academic Balance</h4>
                  <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed font-medium">
                    Study workload, deadline pacing, and confidence accessing course support.
                  </p>
                </div>
                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                    3 Questions
                  </span>
                  <button
                    type="button"
                    onClick={() => handleStartAssessment('academic')}
                    className="text-xs font-bold text-blue-700 hover:text-blue-900 inline-flex items-center gap-1"
                  >
                    <span>Start</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Category 3: Social Connection */}
              <div className="bg-white rounded-2xl p-5 border border-amber-100 shadow-2xs flex flex-col justify-between hover:border-amber-300 transition">
                <div>
                  <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3.5">
                    <Users className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#1E2433]">Social Connection</h4>
                  <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed font-medium">
                    Peer belonging, campus relationships, and trusted support networks.
                  </p>
                </div>
                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100">
                    3 Questions
                  </span>
                  <button
                    type="button"
                    onClick={() => handleStartAssessment('social')}
                    className="text-xs font-bold text-amber-700 hover:text-amber-900 inline-flex items-center gap-1"
                  >
                    <span>Start</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Category 4: Sleep & Lifestyle */}
              <div className="bg-white rounded-2xl p-5 border border-emerald-100 shadow-2xs flex flex-col justify-between hover:border-emerald-300 transition">
                <div>
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3.5">
                    <Moon className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#1E2433]">Sleep & Lifestyle</h4>
                  <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed font-medium">
                    Restorative sleep, hydration, movement, and daily health rhythms.
                  </p>
                </div>
                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                    3 Questions
                  </span>
                  <button
                    type="button"
                    onClick={() => handleStartAssessment('lifestyle')}
                    className="text-xs font-bold text-emerald-700 hover:text-emerald-900 inline-flex items-center gap-1"
                  >
                    <span>Start</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Previous Assessments Section */}
          <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-2xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-[#1E2433]">Previous Assessments</h3>
                <p className="text-xs text-[#717E95] font-medium">
                  Review your longitudinal wellbeing trends and milestone reflections.
                </p>
              </div>
              <span className="text-xs text-purple-700 font-bold bg-purple-50 px-3 py-1 rounded-full">
                3 Records
              </span>
            </div>

            <div className="flex flex-col gap-3">
              {PAST_ASSESSMENTS.map((item) => (
                <div
                  key={item.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/20 transition gap-3"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#1E2433]">{item.title}</span>
                        <span className="text-[10px] text-gray-400 font-medium">• {item.date}</span>
                      </div>
                      <p className="text-xs text-[#64748B] mt-0.5">{item.highlight}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    <span className="text-xs font-bold text-gray-700 bg-gray-50 border border-gray-200 px-2.5 py-1 rounded-full">
                      {item.overallStatus}
                    </span>
                    <button
                      type="button"
                      onClick={() => setStage('results')}
                      className="text-xs font-bold text-purple-700 hover:text-purple-900 inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>View</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 2. GUIDED IN-PROGRESS ASSESSMENT STEPPER */}
      {stage === 'in-progress' && (
        <div className="max-w-2xl mx-auto w-full flex flex-col gap-5 animate-in fade-in duration-200">
          {/* Top Back & Progress Bar */}
          <div className="flex items-center justify-between text-xs font-semibold text-[#64748B]">
            <button
              type="button"
              onClick={() => setStage('landing')}
              className="inline-flex items-center gap-1 text-gray-600 hover:text-black transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </button>
            <span>
              Question {currentQuestionIndex + 1} of {totalQuestions} ({progressPercent}%)
            </span>
          </div>

          {/* Progress bar line */}
          <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Question Card Surface */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm flex flex-col gap-6">
            {/* Category Tag */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 border border-purple-200 px-3 py-1 rounded-full">
                {currentQ.categoryLabel}
              </span>

              <h3 className="text-lg sm:text-xl font-bold text-[#1E2433] mt-3 leading-snug">
                {currentQ.text}
              </h3>

              {currentQ.hint && (
                <p className="text-xs text-[#717E95] mt-1.5 font-medium leading-relaxed">
                  💡 {currentQ.hint}
                </p>
              )}
            </div>

            {/* Scale Options */}
            <div className="flex flex-col gap-2.5 mt-2">
              {SCALE_OPTIONS.map((opt) => {
                const isSelected = currentAnswer === opt.value

                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleSelectOption(opt.value)}
                    className={`w-full flex items-center justify-between p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-purple-50/80 border-purple-400 text-purple-950 shadow-2xs ring-1 ring-purple-300'
                        : 'border-gray-200/90 hover:border-gray-300 hover:bg-gray-50/60 text-[#1E2433]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                          isSelected
                            ? 'border-purple-600 bg-purple-600 text-white'
                            : 'border-gray-300 bg-white'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                      <div>
                        <span className="text-xs font-bold block">{opt.label}</span>
                        <span className="text-[11px] text-[#64748B] font-medium">
                          {opt.description}
                        </span>
                      </div>
                    </div>
                    <span className="text-xs font-mono font-bold text-gray-400">
                      {opt.value} / 5
                    </span>
                  </button>
                )
              })}
            </div>

            {/* Stepper Footer Controls */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100 mt-2">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold transition ${
                  currentQuestionIndex === 0
                    ? 'text-gray-300 cursor-not-allowed'
                    : 'text-gray-700 hover:bg-gray-100 cursor-pointer'
                }`}
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold shadow-xs hover:shadow-sm transition cursor-pointer"
              >
                <span>
                  {currentQuestionIndex === totalQuestions - 1 ? 'Review Answers' : 'Next Question'}
                </span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. REVIEW STEP BEFORE SUBMISSION */}
      {stage === 'review' && (
        <div className="max-w-2xl mx-auto w-full flex flex-col gap-5 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm flex flex-col gap-5">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 border border-purple-200 px-3 py-1 rounded-full">
                Review Your Responses
              </span>
              <h3 className="text-xl font-bold text-[#1E2433] mt-2.5">
                Ready to submit your wellbeing pulse?
              </h3>
              <p className="text-xs text-[#64748B] mt-1">
                You can review or change any answer before saving your self-reflection.
              </p>
            </div>

            {/* Responses List Summary */}
            <div className="flex flex-col gap-2.5 max-h-[380px] overflow-y-auto pr-1">
              {ASSESSMENT_QUESTIONS.map((q) => {
                const ansVal = answers[q.id] || 3
                const scaleObj = SCALE_OPTIONS.find((s) => s.value === ansVal)

                return (
                  <div
                    key={q.id}
                    className="flex items-center justify-between p-3 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-white transition"
                  >
                    <div className="max-w-[70%]">
                      <span className="text-[10px] font-bold text-purple-700 uppercase">
                        Q{q.id} • {q.categoryLabel}
                      </span>
                      <p className="text-xs font-medium text-[#1E2433] truncate mt-0.5">{q.text}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-800 bg-white border border-gray-200 px-2 py-0.5 rounded-lg shadow-2xs">
                        {scaleObj?.label}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setCurrentQuestionIndex(q.id - 1)
                          setStage('in-progress')
                        }}
                        className="text-xs font-semibold text-purple-600 hover:text-purple-800 underline"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setStage('in-progress')}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold text-gray-600 hover:bg-gray-100"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Questions</span>
              </button>

              <button
                type="button"
                onClick={handleSubmitAssessment}
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold shadow-xs hover:shadow-sm transition"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Submit & View Results</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. RESULTS VIEW */}
      {stage === 'results' && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Result Highlight Card */}
          <div className="rounded-3xl bg-gradient-to-br from-[#EAF7EE] via-[#F1FAF3] to-[#EEF2FF] p-6 sm:p-8 border border-emerald-200 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold mb-2.5 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Assessment Completed Successfully</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#1E2433] tracking-tight">
                Reflective Summary for Asha
              </h2>
              <p className="text-xs sm:text-sm text-[#334155] font-medium mt-1.5 leading-relaxed">
                Thank you for completing this self-check. Based on your responses, your emotional resilience and peer connectivity show consistent healthy strength, while study pacing could benefit from structured daily breaks.
              </p>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-1 text-xs font-bold text-emerald-800 bg-white/80 px-3 py-1.5 rounded-full border border-emerald-200">
                  <Award className="w-4 h-4 text-emerald-600" />
                  <span>Overall State: Balanced & Self-Aware</span>
                </div>
                <div className="flex items-center gap-1 text-xs font-semibold text-gray-600 bg-white/80 px-3 py-1.5 rounded-full border border-gray-200">
                  <Calendar className="w-4 h-4 text-purple-600" />
                  <span>Logged Today</span>
                </div>
              </div>
            </div>

            {/* Quick Score Dial / Icon */}
            <div className="w-36 h-36 rounded-full bg-white shadow-md border-4 border-emerald-300 flex flex-col items-center justify-center shrink-0">
              <span className="text-3xl font-black text-[#1E2433]">78</span>
              <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider">
                Index / 100
              </span>
              <span className="text-[10px] font-bold text-emerald-600 mt-0.5">Healthy Band</span>
            </div>
          </div>

          {/* Observations & Strengths Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Strengths Card */}
            <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Areas of Strength</h3>
                </div>

                <ul className="space-y-2.5 text-xs text-[#334155] font-medium">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      <strong>Supportive Network:</strong> You feel comfortable reaching out to trusted peers and faculty mentors when facing challenges.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      <strong>Emotional Awareness:</strong> High clarity on noticing when stress levels elevate, allowing for early self-regulation.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      <strong>Physical Movement:</strong> Routine engagement in gentle walks and physical recharge between long study stretches.
                    </span>
                  </li>
                </ul>
              </div>

              <div className="mt-5 pt-4 border-t border-gray-100 text-[11px] text-gray-500">
                Identified based on your responses in Social Connection & Emotional Wellbeing.
              </div>
            </div>

            {/* Suggested Self-Care Next Steps */}
            <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                    <Smile className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Suggested Self-Care Activities</h3>
                </div>

                <ul className="space-y-2.5 text-xs text-[#334155] font-medium">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                    <span>
                      <strong>5-Min Box Breathing:</strong> Take short 4-4-4 resets before initiating heavy coding or lab assignments.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                    <span>
                      <strong>Paced Study Sprints:</strong> Try 30-minute focused blocks followed by 5 minutes away from screens.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                    <span>
                      <strong>Sleep Consistency:</strong> Wind down without bright blue light 30 minutes before sleep for better morning energy.
                    </span>
                  </li>
                </ul>
              </div>

              {/* Action Button: Request Support */}
              <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                <span className="text-xs text-gray-500">Need confidential guidance?</span>
                {onRequestSupport && (
                  <button
                    type="button"
                    onClick={onRequestSupport}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-purple-700 hover:text-purple-900 bg-purple-50 hover:bg-purple-100 px-3.5 py-1.5 rounded-full border border-purple-200 transition"
                  >
                    <HeartHandshake className="w-3.5 h-3.5" />
                    <span>Request Mentor Support</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Bottom Controls */}
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => handleStartAssessment()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white border border-gray-200 text-gray-700 text-xs font-bold hover:bg-gray-50 transition shadow-2xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retake Assessment</span>
            </button>

            {onNavigateToOverview && (
              <button
                type="button"
                onClick={onNavigateToOverview}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition shadow-xs"
              >
                <span>Return to Overview</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}
        </>
      )}
    </div>
  )
}

