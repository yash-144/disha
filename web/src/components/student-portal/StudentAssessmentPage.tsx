import React, { useState } from 'react'
import {
  Sparkles,
  BookOpen,
  MessageSquare,
  Heart,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Send,
  RotateCcw,
  Award,
  ChevronRight,
  ArrowRight,
  ArrowLeft,
  HelpCircle,
  Play,
  Check,
  AlertCircle,
  Users,
  UserCheck,
  PhoneCall,
  Calendar,
  X,
  FileText,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { useApp } from '../../context/AppContext'
import { friendlyDate } from '../../lib/labels'
import {
  PULSE_QUESTION_BANK,
  INITIAL_PULSE_ASSIGNMENTS,
  DEMO_PEER_MENTOR_POOL,
  evaluateInterventionMatrix,
  PULSE_DEMO_SCENARIOS,
  PulseDemoScenario,
} from './studentPulseData'
import {
  PulseQuestion,
  ObjectiveResult,
  StudentPulseSubmission,
  InterventionAction,
} from '../../types/studentPulse'
import { useSubmitPulse } from '../../lib/api/endpoints/student.hooks'

interface StudentAssessmentPageProps {
  demoMode?: DemoMode
  onRequestSupport?: () => void
  onNavigateToOverview?: () => void
}

export function StudentAssessmentPage({
  demoMode = 'normalStudent',
  onRequestSupport,
  onNavigateToOverview,
}: StudentAssessmentPageProps = {}) {
  const { addToast } = useApp()
  const submitPulseMutation = useSubmitPulse()

  // Selected course pulse assignment (defaults to CS201 Student Pulse #3)
  const [selectedPulseId, setSelectedPulseId] = useState<string>('pulse-cs201-03')
  const currentPulse =
    INITIAL_PULSE_ASSIGNMENTS.find((p) => p.id === selectedPulseId) ||
    INITIAL_PULSE_ASSIGNMENTS[0]

  // Filter questions for the active pulse
  const activeQuestions: PulseQuestion[] = PULSE_QUESTION_BANK.filter((q) =>
    currentPulse.questionIds.includes(q.id)
  )

  // Stepper Stage: 'intro' | 'question' | 'results'
  const [stage, setStage] = useState<'intro' | 'question' | 'results'>('intro')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0)

  // Student Answers State — ALL UNMARKED BY DEFAULT
  const [academicAnswers, setAcademicAnswers] = useState<Record<string, number | string>>({})
  const [feedbackAnswers, setFeedbackAnswers] = useState<Record<string, string | number>>({})
  const [wellbeingAnswers, setWellbeingAnswers] = useState<Record<string, number | string>>({})

  // Category Scores & Evaluation State
  const [feedbackPctScore, setFeedbackPctScore] = useState<number>(75)
  const [wellbeingPctScore, setWellbeingPctScore] = useState<number>(70)
  const [evaluationResult, setEvaluationResult] = useState<{
    academicStatus: 'GOOD' | 'LOW'
    feedbackStatus: 'GOOD' | 'LOW'
    wellbeingStatus: 'GOOD' | 'LOW'
    recommendedActions: InterventionAction[]
  }>({
    academicStatus: 'GOOD',
    feedbackStatus: 'GOOD',
    wellbeingStatus: 'GOOD',
    recommendedActions: [],
  })

  // Support offer states (student response lifecycle)
  const [mentorOfferStatus, setMentorOfferStatus] = useState<'OFFERED' | 'ACCEPTED' | 'DECLINED'>('OFFERED')
  const [counsellorOfferStatus, setCounsellorOfferStatus] = useState<'OFFERED' | 'ACCEPTED' | 'DECLINED'>('OFFERED')

  // Submission results
  const [submissionResult, setSubmissionResult] = useState<StudentPulseSubmission | null>(null)

  // Current question in stepper
  const currentQuestion: PulseQuestion | undefined = activeQuestions[currentQuestionIndex]
  const totalQuestions = activeQuestions.length
  const progressPercent = Math.round(((currentQuestionIndex + 1) / Math.max(totalQuestions, 1)) * 100)

  // Handler: Start Assessment (clears/unmarks all answers and moves to Q1)
  const handleStartAssessment = () => {
    setAcademicAnswers({})
    setFeedbackAnswers({})
    setWellbeingAnswers({})
    setCurrentQuestionIndex(0)
    setStage('question')
    setMentorOfferStatus('OFFERED')
    setCounsellorOfferStatus('OFFERED')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Handler: Next question
  const handleNextQuestion = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Handler: Previous question
  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Handler: Final Submit & Auto-Grading with 3 category scoring and 8-row intervention matrix
  const handleSubmitAssessment = () => {
    const academicQuestions = activeQuestions.filter((q) => q.category === 'ACADEMIC')
    let earnedMarks = 0
    let totalMaxMarks = 0
    const objectiveResults: ObjectiveResult[] = []

    academicQuestions.forEach((q) => {
      totalMaxMarks += q.marks
      const userAns = academicAnswers[q.id]

      if (q.questionType === 'mcq') {
        const isCorrect = userAns !== undefined && Number(userAns) === q.correctOption
        const awarded = isCorrect ? q.marks : 0
        earnedMarks += awarded
        objectiveResults.push({
          questionId: q.id,
          prompt: q.prompt,
          selectedOption: userAns,
          correctOption: q.correctOption,
          isCorrect,
          marksAwarded: awarded,
          maxMarks: q.marks,
          explanation: q.explanation,
        })
      } else {
        const userText = (academicAnswers[q.id] as string) || ''
        const awarded = userText.trim().length > 10 ? q.marks * 0.8 : 0
        earnedMarks += awarded
        objectiveResults.push({
          questionId: q.id,
          prompt: q.prompt,
          selectedOption: userText || '(No answer given)',
          correctOption: undefined,
          isCorrect: userText.trim().length > 10,
          marksAwarded: awarded,
          maxMarks: q.marks,
          explanation:
            'We got your answer. Your teacher will mark it.',
        })
      }
    })

    const acadPct = totalMaxMarks > 0 ? Math.round((earnedMarks / totalMaxMarks) * 100) : 0

    // Calculate feedback score (0-100, excluding descriptive)
    const feedQuestions = activeQuestions.filter((q) => q.category === 'CLASSROOM_FEEDBACK' && q.questionType !== 'descriptive')
    let feedTotal = 0
    let feedCount = 0
    feedQuestions.forEach((q) => {
      const val = feedbackAnswers[q.id]
      if (val !== undefined) {
        feedCount++
        if (typeof val === 'number') {
          feedTotal += Math.min(100, Math.max(0, val * 25))
        } else if (String(val).toLowerCase().includes('just right')) {
          feedTotal += 100
        } else if (String(val).toLowerCase().includes('too fast') || String(val).toLowerCase().includes('too slow')) {
          feedTotal += 40
        } else {
          feedTotal += 60
        }
      }
    })
    const computedFeedbackPct = feedCount > 0 ? Math.round(feedTotal / feedCount) : 75

    // Calculate wellbeing score (0-100, reverse-scoring negative items)
    const wellQuestions = activeQuestions.filter((q) => q.category === 'WELLBEING')
    let wellTotal = 0
    let wellCount = 0
    wellQuestions.forEach((q) => {
      const val = wellbeingAnswers[q.id]
      if (val !== undefined) {
        wellCount++
        const isNegative = q.parameterTag === 'academic_pressure' || q.parameterTag === 'loneliness_frequency'
        let num = 70
        if (typeof val === 'number') {
          num = val * 25
        } else if (String(val).toLowerCase().includes('almost constantly')) {
          num = 15
        } else if (String(val).toLowerCase().includes('rarely') || String(val).toLowerCase().includes('never')) {
          num = 95
        } else {
          num = 60
        }
        if (isNegative && typeof val === 'number') {
          num = 100 - num
        }
        wellTotal += num
      }
    })
    const computedWellbeingPct = wellCount > 0 ? Math.round(wellTotal / wellCount) : 70

    // Evaluate 8-row intervention matrix against 60% operational threshold
    const evalRes = evaluateInterventionMatrix(acadPct, computedFeedbackPct, computedWellbeingPct, 60.0)

    setFeedbackPctScore(computedFeedbackPct)
    setWellbeingPctScore(computedWellbeingPct)
    setEvaluationResult(evalRes)
    setMentorOfferStatus('OFFERED')
    setCounsellorOfferStatus('OFFERED')

    const result: StudentPulseSubmission = {
      submissionId: `sub-${currentPulse.id}-${Date.now().toString().slice(-4)}`,
      pulseId: currentPulse.id,
      studentId: 'student-asha',
      studentName: 'Asha Verma',
      academicScore: Math.round(earnedMarks * 10) / 10,
      academicMaxMarks: totalMaxMarks,
      percentage: acadPct,
      submittedAt: new Date().toISOString(),
      isAnonymous: true,
      objectiveResults,
    }

    // Submit wellbeing responses to live backend
    const responsesMap: Record<string, number> = {}
    Object.entries(wellbeingAnswers).forEach(([k, v]) => {
      const numVal = typeof v === 'number' ? v : parseInt(String(v), 10)
      if (!isNaN(numVal) && numVal >= 1 && numVal <= 5) {
        responsesMap[k] = numVal
      } else {
        responsesMap[k] = 3
      }
    })
    submitPulseMutation.mutate({
      responses: Object.keys(responsesMap).length > 0 ? responsesMap : { q_stress: 3, q_sleep: 4, q_belonging: 4 },
      reflection: 'Wellbeing check-in',
    })

    setSubmissionResult(result)
    setStage('results')
    window.scrollTo({ top: 0, behavior: 'smooth' })

    addToast(
      'Check-in sent',
      `Your quiz score is ${acadPct}%. Thank you!`,
      'success'
    )
  }

  // Check if current question is answered
  const isCurrentQuestionAnswered = () => {
    if (!currentQuestion) return false
    if (currentQuestion.category === 'ACADEMIC') {
      const ans = academicAnswers[currentQuestion.id]
      return ans !== undefined && ans !== ''
    } else if (currentQuestion.category === 'CLASSROOM_FEEDBACK') {
      const ans = feedbackAnswers[currentQuestion.id]
      return ans !== undefined && ans !== ''
    } else {
      const ans = wellbeingAnswers[currentQuestion.id]
      return ans !== undefined && ans !== ''
    }
  }

  // Get current answer for active question
  const getCurrentAnswerValue = () => {
    if (!currentQuestion) return undefined
    if (currentQuestion.category === 'ACADEMIC') {
      return academicAnswers[currentQuestion.id]
    } else if (currentQuestion.category === 'CLASSROOM_FEEDBACK') {
      return feedbackAnswers[currentQuestion.id]
    } else {
      return wellbeingAnswers[currentQuestion.id]
    }
  }

  // Set answer for active question
  const handleSelectAnswer = (val: number | string) => {
    if (!currentQuestion) return
    if (currentQuestion.category === 'ACADEMIC') {
      setAcademicAnswers((prev) => ({ ...prev, [currentQuestion.id]: val }))
    } else if (currentQuestion.category === 'CLASSROOM_FEEDBACK') {
      setFeedbackAnswers((prev) => ({ ...prev, [currentQuestion.id]: val }))
    } else {
      setWellbeingAnswers((prev) => ({ ...prev, [currentQuestion.id]: val }))
    }
  }

  return (
    <div className="flex-1 flex flex-col gap-5 font-sans select-none pb-12">
      {/* =========================================================================
          STAGE 1: INTRO SCREEN (Questions do not appear until student clicks Start)
         ========================================================================= */}
      {stage === 'intro' && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Main Welcome Hero Banner */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-accent-soft via-[#F3EDFC] to-[#FCEEF5] p-6 sm:p-9 border border-[#DDD6FE]/70 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="max-w-2xl z-10">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/90 border border-purple-200 text-purple-700 text-xs font-bold mb-3 shadow-2xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Wellbeing check-in</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight leading-tight">
                {currentPulse.title}
              </h1>

              <p className="text-xs sm:text-sm text-[#475569] mt-2 leading-relaxed">
                A short check-in on your learning, your classes and how you are feeling. It takes a few minutes.
              </p>

              <div className="flex flex-wrap items-center gap-4 mt-5 text-xs text-gray-600 font-medium">
                <div className="flex items-center gap-1.5 bg-white/80 px-3 py-1.5 rounded-full border border-line">
                  <Clock className="w-3.5 h-3.5 text-purple-600" />
                  <span>Due: {friendlyDate(currentPulse.dueAt)}</span>
                </div>
                <div className="flex items-center gap-1.5 bg-white/80 px-3 py-1.5 rounded-full border border-line">
                  <Award className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{currentPulse.totalMarks} marks for the quiz</span>
                </div>
                <div className="flex items-center gap-1.5 bg-white/80 px-3 py-1.5 rounded-full border border-line">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                  <span>Your feelings and class feedback stay anonymous</span>
                </div>
              </div>

              <div className="mt-6">
                <button
                  type="button"
                  onClick={handleStartAssessment}
                  className="px-6 py-3 rounded-2xl bg-ink hover:bg-ink text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer hover:shadow-lg"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>Start check-in</span>
                </button>
              </div>
            </div>

            {/* Category Structure Preview */}
            <div className="w-full md:w-80 shrink-0 flex flex-col gap-3 z-10">
              <div className="p-3.5 rounded-2xl bg-white/90 border border-purple-100 shadow-2xs flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs shrink-0">
                  5Q
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-900">Part 1: Quick quiz</p>
                  <p className="text-xs text-gray-500">5 questions on what you learned</p>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-white/90 border border-blue-100 shadow-2xs flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                  4Q
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-900">Part 2: Your class</p>
                  <p className="text-xs text-gray-500">4 questions. The last is optional</p>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-white/90 border border-emerald-100 shadow-2xs flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">
                  3Q
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-900">Part 3: How you feel</p>
                  <p className="text-xs text-gray-500">3 questions about support and motivation</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          STAGE 2: QUESTION STEPPER
         ========================================================================= */}
      {stage === 'question' && currentQuestion && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-line shadow-xs flex flex-col gap-5 animate-in fade-in duration-150">
          {/* Question Header & Stepper Status */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    currentQuestion.category === 'ACADEMIC'
                      ? 'bg-purple-100 text-purple-800'
                      : currentQuestion.category === 'CLASSROOM_FEEDBACK'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {currentQuestion.category === 'ACADEMIC' ? 'Quick quiz' : currentQuestion.category === 'CLASSROOM_FEEDBACK' ? 'Your class' : 'How you feel'}
                </span>

                {currentQuestion.difficulty && (
                  <span
                    className={`px-2.5 py-0.5 rounded-md text-xs font-semibold ${
                      currentQuestion.difficulty === 'Easy'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : currentQuestion.difficulty === 'Medium'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}
                  >
                    {currentQuestion.difficulty}
                  </span>
                )}
              </div>

              {/* Marks & Question Index */}
              <div className="flex items-center gap-2">
                {currentQuestion.marks > 0 && (
                  <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200">
                    {currentQuestion.marks} marks
                  </span>
                )}
                <span className="text-xs font-bold text-gray-500">
                  Question {currentQuestionIndex + 1} of {totalQuestions}
                </span>
              </div>
            </div>

            {/* Live Progress Bar */}
            <div className="w-full h-2 rounded-full bg-gray-100 overflow-hidden mt-3">
              <div
                className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Current Question Body */}
          <div className="p-5 sm:p-6 rounded-2xl bg-paper border border-line">
            <h2 className="text-base sm:text-lg font-bold text-gray-900 leading-relaxed mb-4">
              {currentQuestion.prompt}
            </h2>

            {/* MCQ & Single-Choice Options (UNMARKED UNTIL CLICKED) */}
            {currentQuestion.options && currentQuestion.options.length > 0 && (
              <div className="space-y-2.5">
                {currentQuestion.options.map((opt, optIdx) => {
                  const currentAnswer = getCurrentAnswerValue()
                  const isSelected =
                    currentQuestion.questionType === 'mcq'
                      ? currentAnswer === optIdx
                      : currentAnswer === opt || currentAnswer === optIdx + 1

                  return (
                    <button
                      key={optIdx}
                      type="button"
                      onClick={() =>
                        handleSelectAnswer(
                          currentQuestion.questionType === 'mcq' ? optIdx : opt
                        )
                      }
                      className={`w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm font-medium transition-all flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-purple-100/80 border-purple-500 text-purple-950 font-bold shadow-2xs ring-1 ring-purple-400'
                          : 'bg-white border-line text-gray-700 hover:bg-gray-50 hover:border-gray-300'
                      }`}
                    >
                      <span>{opt}</span>
                      <div
                        className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                          isSelected
                            ? 'border-purple-600 bg-purple-600 text-white'
                            : 'border-gray-300'
                        }`}
                      >
                        {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Descriptive Answer Field (UNMARKED UNTIL TYPED) */}
            {currentQuestion.questionType === 'descriptive' && (
              <div className="space-y-2">
                <textarea
                  rows={4}
                  value={(getCurrentAnswerValue() as string) || ''}
                  onChange={(e) => handleSelectAnswer(e.target.value)}
                  placeholder="Type your answer here..."
                  className="w-full p-3.5 rounded-xl border border-gray-300 text-xs sm:text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white font-sans"
                />
                <span className="text-xs text-muted block text-right">
                  Your teacher will read this answer.
                </span>
              </div>
            )}
          </div>

          {/* Stepper Controls: Previous, Next, and Final Submit */}
          <div className="flex items-center justify-between pt-3 border-t border-line">
            <button
              type="button"
              disabled={currentQuestionIndex === 0}
              onClick={handlePreviousQuestion}
              className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                currentQuestionIndex === 0
                  ? 'opacity-40 cursor-not-allowed text-muted'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>

            {currentQuestionIndex < totalQuestions - 1 ? (
              <button
                type="button"
                onClick={handleNextQuestion}
                className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
              >
                <span>Next</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmitAssessment}
                className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
              >
                <Send className="w-4 h-4" />
                <span>Finish check-in</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          STAGE 3: RESULTS SCREEN & INTERVENTION ACTIONS
         ========================================================================= */}
      {stage === 'results' && submissionResult && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Main Hero Results Card */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-ink to-ink p-6 sm:p-9 text-white shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-bold mb-3">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Check-in done</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                Quiz score: {submissionResult.percentage}%
              </h2>

              <p className="text-xs sm:text-sm text-purple-200 mt-1.5 leading-relaxed">
                Your quiz is marked. Your answers about your class and how you feel are kept anonymous.
              </p>

              <div className="mt-5 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleStartAssessment}
                  className="px-5 py-2.5 rounded-full bg-white text-purple-900 hover:bg-purple-50 text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Do it again</span>
                </button>

                {onNavigateToOverview && (
                  <button
                    type="button"
                    onClick={onNavigateToOverview}
                    className="px-5 py-2.5 rounded-full bg-white/20 hover:bg-white/30 text-white text-xs font-bold border border-white/30 transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>Back to home</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* 3 Normalized Scores Display */}
            <div className="grid grid-cols-3 gap-2 w-full md:w-auto shrink-0">
              <div className="bg-white/10 backdrop-blur-xs p-3.5 rounded-2xl border border-white/20 text-center">
                <span className="text-xs text-purple-200 block font-medium">Quiz</span>
                <div className="text-2xl font-extrabold text-white mt-0.5">
                  {submissionResult.percentage}%
                </div>
                <span className={`text-xs font-bold mt-1 block ${submissionResult.percentage >= 60 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {submissionResult.percentage >= 60 ? 'On track' : 'Could use support'}
                </span>
              </div>

              <div className="bg-white/10 backdrop-blur-xs p-3.5 rounded-2xl border border-white/20 text-center">
                <span className="text-xs text-purple-200 block font-medium">Your class</span>
                <div className="text-2xl font-extrabold text-white mt-0.5">
                  {feedbackPctScore}%
                </div>
                <span className={`text-xs font-bold mt-1 block ${feedbackPctScore >= 60 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {feedbackPctScore >= 60 ? 'Going well' : 'Teacher will take a look'}
                </span>
              </div>

              <div className="bg-white/10 backdrop-blur-xs p-3.5 rounded-2xl border border-white/20 text-center">
                <span className="text-xs text-purple-200 block font-medium">Wellbeing</span>
                <div className="text-2xl font-extrabold text-white mt-0.5">
                  {wellbeingPctScore}%
                </div>
                <span className={`text-xs font-bold mt-1 block ${wellbeingPctScore >= 60 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {wellbeingPctScore >= 60 ? 'Doing fine' : 'Support is available'}
                </span>
              </div>
            </div>
          </div>

          {/* =========================================================================
              INTERVENTION OFFERS & ACTIONS (From the 8-Row Matrix)
             ========================================================================= */}


          {/* Action 2: Confidential Counsellor Offer (Triggered when Wellbeing < 60%) */}
          {evaluationResult.recommendedActions.includes('COUNSELLOR_OFFER') && (
            <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="max-w-xl">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-200 text-purple-900 text-xs font-bold uppercase tracking-wide">
                    Private support
                  </span>
                  <span className="text-xs text-purple-700 font-semibold">• Only you and your counsellor</span>
                </div>
                <h3 className="text-base font-bold text-gray-900">
                  Someone is here to talk
                </h3>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                  A counsellor can meet you privately. Teachers, classmates and mentors cannot see your answers.
                </p>
              </div>

              <div className="flex items-center gap-2.5 shrink-0">
                {counsellorOfferStatus === 'OFFERED' ? (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        setCounsellorOfferStatus('ACCEPTED')
                        addToast('Your counsellor knows', 'They will contact you to find a time.', 'success')
                      }}
                      className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
                    >
                      <Heart className="w-3.5 h-3.5 fill-white" />
                      <span>Yes, I would like that</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCounsellorOfferStatus('DECLINED')
                        addToast('No problem', 'Support is there whenever you need it.', 'info')
                      }}
                      className="px-4 py-2 rounded-xl bg-white hover:bg-gray-50 text-gray-700 text-xs font-bold border border-line transition-all cursor-pointer"
                    >
                      <span>Decline</span>
                    </button>
                  </>
                ) : counsellorOfferStatus === 'ACCEPTED' ? (
                  <div className="flex items-center gap-2 text-xs font-bold text-purple-800 bg-white px-4 py-2 rounded-xl border border-purple-200 shadow-2xs">
                    <CheckCircle2 className="w-4 h-4 text-purple-600" />
                    <span>Session scheduled with your counsellor</span>
                  </div>
                ) : (
                  <div className="text-xs font-medium text-gray-500 bg-white px-3 py-1.5 rounded-xl border border-line">
                    You said no thanks. You can ask any time.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action 3: Faculty Review Alert Confirmation */}
          {evaluationResult.recommendedActions.includes('FACULTY_REVIEW') && (
            <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-xs text-blue-900 flex items-center gap-2.5">
              <FileText className="w-5 h-5 text-blue-600 shrink-0" />
              <span>
                <strong>Your teacher will take a look:</strong> Anonymous feedback from the class suggests lessons may need a different pace. Nobody will know it was you.
              </span>
            </div>
          )}

          {/* Privacy Receipt */}
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" />
            <span>
              <strong>Your privacy:</strong> Your answers about your class and how you feel are not linked to your name. They only count in totals for groups of 5 or more.
            </span>
          </div>

          {/* Objective Question Review Section */}
          <div className="bg-white rounded-3xl p-6 border border-line shadow-2xs">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Your quiz answers
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              See what was right and why.
            </p>

            <div className="space-y-4">
              {submissionResult.objectiveResults.map((item, idx) => (
                <div
                  key={item.questionId}
                  className={`p-4 sm:p-5 rounded-2xl border ${
                    item.isCorrect
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : 'bg-rose-50/40 border-rose-200'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                          item.isCorrect ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'
                        }`}
                      >
                        {item.isCorrect ? '✓' : '✗'}
                      </span>
                      <span className="text-xs font-bold text-gray-800">Question {idx + 1}</span>
                    </div>
                    <span className="text-xs font-bold text-gray-700">
                      {item.marksAwarded} of {item.maxMarks} marks
                    </span>
                  </div>

                  <p className="text-sm font-semibold text-gray-900 mb-2">{item.prompt}</p>

                  <div className="text-xs text-gray-700 space-y-1 mb-2">
                    {typeof item.selectedOption === 'number' ? (
                      <p>
                        Your answer: <strong>Option {item.selectedOption + 1}</strong>
                      </p>
                    ) : (
                      <p>
                        Your answer: <strong>"{item.selectedOption}"</strong>
                      </p>
                    )}
                  </div>

                  {item.explanation && (
                    <div className="p-3 rounded-xl bg-white/80 border border-line text-xs text-gray-700 mt-2">
                      <strong>Why:</strong> {item.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
