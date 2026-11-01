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
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { useApp } from '../../context/AppContext'
import {
  PULSE_QUESTION_BANK,
  INITIAL_PULSE_ASSIGNMENTS,
} from './studentPulseData'
import {
  PulseQuestion,
  ObjectiveResult,
  StudentPulseSubmission,
} from '../../types/studentPulse'

interface StudentAssessmentPageProps {
  demoMode: DemoMode
  onRequestSupport?: () => void
  onNavigateToOverview?: () => void
}

export function StudentAssessmentPage({
  demoMode,
  onRequestSupport,
  onNavigateToOverview,
}: StudentAssessmentPageProps) {
  const { addToast } = useApp()

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

  // Handler: Final Submit & Auto-Grading
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
        // Descriptive provisional scoring
        const userText = (academicAnswers[q.id] as string) || ''
        const awarded = userText.trim().length > 10 ? q.marks * 0.8 : 0
        earnedMarks += awarded
        objectiveResults.push({
          questionId: q.id,
          prompt: q.prompt,
          selectedOption: userText || '(No answer provided)',
          correctOption: undefined,
          isCorrect: userText.trim().length > 10,
          marksAwarded: awarded,
          maxMarks: q.marks,
          explanation:
            'Descriptive answer received. Provisional marks awarded; subject to final faculty rubric assessment.',
        })
      }
    })

    const pct = totalMaxMarks > 0 ? Math.round((earnedMarks / totalMaxMarks) * 100) : 0
    const result: StudentPulseSubmission = {
      submissionId: `sub-${currentPulse.id}-${Date.now().toString().slice(-4)}`,
      pulseId: currentPulse.id,
      studentId: 'student-asha',
      studentName: 'Asha Verma',
      academicScore: Math.round(earnedMarks * 10) / 10,
      academicMaxMarks: totalMaxMarks,
      percentage: pct,
      submittedAt: new Date().toISOString(),
      isAnonymous: true,
      objectiveResults,
    }

    setSubmissionResult(result)
    setStage('results')
    window.scrollTo({ top: 0, behavior: 'smooth' })

    addToast(
      'Assessment Submitted! 🎉',
      `You scored ${result.academicScore} / ${result.academicMaxMarks} Marks (${pct}%). Feedback submitted anonymously.`,
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
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#EDE8FB] via-[#F3EDFC] to-[#FCEEF5] p-6 sm:p-9 border border-[#DDD6FE]/70 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="max-w-2xl z-10">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/90 border border-purple-200 text-purple-700 text-xs font-bold mb-3 shadow-2xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Student Pulse Assessment</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1E2433]">
                {currentPulse.title}
              </h1>

              <p className="text-xs sm:text-sm text-[#475569] font-medium mt-2 leading-relaxed">
                Course: <strong>{currentPulse.courseName} ({currentPulse.courseId})</strong> • {currentPulse.sectionId}
              </p>

              <p className="text-xs sm:text-sm text-[#64748B] mt-1 leading-relaxed">
                This assessment consists of three unified categories: evaluate your academic knowledge, share anonymous classroom feedback, and check in on your academic workload.
              </p>

              {/* Assessment Chips */}
              <div className="flex flex-wrap items-center gap-3 mt-5">
                <div className="flex items-center gap-1.5 text-xs text-gray-700 font-semibold bg-white/80 px-3.5 py-1.5 rounded-full border border-purple-100 shadow-2xs">
                  <Clock className="w-4 h-4 text-purple-600" />
                  <span>10–12 minutes</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-700 font-semibold bg-white/80 px-3.5 py-1.5 rounded-full border border-purple-100 shadow-2xs">
                  <HelpCircle className="w-4 h-4 text-purple-600" />
                  <span>{totalQuestions} Randomized Questions</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-800 font-semibold bg-white/80 px-3.5 py-1.5 rounded-full border border-emerald-200 shadow-2xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Feedback & Wellbeing 100% Anonymous</span>
                </div>
              </div>

              {/* START ASSESSMENT BUTTON */}
              <div className="mt-7 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleStartAssessment}
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-purple-600 hover:bg-purple-700 text-white text-xs sm:text-sm font-extrabold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Assessment</span>
                </button>

                {/* Course Switcher */}
                <div className="flex items-center gap-1.5 bg-white/70 px-3 py-2 rounded-full border border-purple-200">
                  <span className="text-[11px] font-bold text-gray-500">Course:</span>
                  <select
                    value={selectedPulseId}
                    onChange={(e) => setSelectedPulseId(e.target.value)}
                    className="bg-transparent text-xs font-bold text-purple-950 focus:outline-none cursor-pointer"
                  >
                    {INITIAL_PULSE_ASSIGNMENTS.filter((p) => p.status === 'published').map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.courseId}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Visual Graphic Card */}
            <div className="w-48 h-48 sm:w-56 sm:h-56 shrink-0 relative flex items-center justify-center">
              <div className="w-full h-full rounded-3xl bg-white/60 border border-purple-200 p-5 shadow-2xs flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded">
                    3 Categories
                  </span>
                  <Award className="w-4 h-4 text-purple-600" />
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-purple-900 font-semibold">
                    <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                    <span>5 Academic Questions</span>
                  </div>
                  <div className="flex items-center gap-2 text-sky-900 font-semibold">
                    <MessageSquare className="w-3.5 h-3.5 text-sky-600" />
                    <span>4 Classroom Feedback</span>
                  </div>
                  <div className="flex items-center gap-2 text-rose-900 font-semibold">
                    <Heart className="w-3.5 h-3.5 text-rose-600" />
                    <span>3 Student Wellbeing</span>
                  </div>
                </div>
                <span className="text-[10px] text-gray-500 italic">
                  Answers unselected until started.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          STAGE 2: STEPPER (One Question At A Time with Next & Previous)
         ========================================================================= */}
      {stage === 'question' && currentQuestion && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-2xs flex flex-col gap-6 animate-in fade-in duration-150">
          {/* Header & Question Navigation Progress */}
          <div>
            <div className="flex items-center justify-between gap-3 mb-2">
              {/* Category Badging */}
              <div className="flex items-center gap-2">
                {currentQuestion.category === 'ACADEMIC' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold border border-purple-200">
                    <BookOpen className="w-3.5 h-3.5" />
                    Category A: Academic Assessment
                  </span>
                )}
                {currentQuestion.category === 'CLASSROOM_FEEDBACK' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200">
                    <MessageSquare className="w-3.5 h-3.5" />
                    Category B: Classroom Feedback (Anonymous)
                  </span>
                )}
                {currentQuestion.category === 'WELLBEING' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 text-rose-700 text-xs font-bold border border-rose-200">
                    <Heart className="w-3.5 h-3.5" />
                    Category C: Student Wellbeing
                  </span>
                )}

                {currentQuestion.difficulty && (
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      currentQuestion.difficulty === 'Easy'
                        ? 'bg-emerald-100 text-emerald-800'
                        : currentQuestion.difficulty === 'Medium'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-rose-100 text-rose-800'
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
                    {currentQuestion.marks} Marks
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
          <div className="p-5 sm:p-6 rounded-2xl bg-[#FAFAFC] border border-gray-200">
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
                          : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300'
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
                  placeholder="Type your explanation here clearly..."
                  className="w-full p-3.5 rounded-xl border border-gray-300 text-xs sm:text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white font-sans"
                />
                <span className="text-[11px] text-gray-400 block text-right">
                  Descriptive responses are reviewed by your instructor using conceptual rubrics.
                </span>
              </div>
            )}
          </div>

          {/* Stepper Controls: Previous, Next, and Final Submit */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <button
              type="button"
              disabled={currentQuestionIndex === 0}
              onClick={handlePreviousQuestion}
              className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                currentQuestionIndex === 0
                  ? 'opacity-40 cursor-not-allowed text-gray-400'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </button>

            <div className="flex items-center gap-2">
              {currentQuestionIndex < totalQuestions - 1 ? (
                <button
                  type="button"
                  onClick={handleNextQuestion}
                  className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  <span>Next Question</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmitAssessment}
                  className="px-7 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-extrabold transition-all shadow-md flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Submit & View Marks</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          STAGE 3: FINAL RESULTS (Student gets their marks and answers breakdown)
         ========================================================================= */}
      {stage === 'results' && submissionResult && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Marks Hero Card */}
          <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300 text-xs font-bold border border-emerald-400/30">
                  Assessment Completed
                </span>
                <span className="text-xs text-purple-200">•</span>
                <span className="text-xs text-purple-200 font-medium">
                  Submitted {new Date(submissionResult.submittedAt).toLocaleDateString()}
                </span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                Your Academic Marks: {submissionResult.academicScore} / {submissionResult.academicMaxMarks}
              </h2>

              <p className="text-xs sm:text-sm text-purple-200 mt-1.5 leading-relaxed">
                Objective questions have been evaluated below with concept explanations. Your classroom feedback and wellbeing answers have been securely anonymized.
              </p>

              <div className="mt-5 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleStartAssessment}
                  className="px-5 py-2.5 rounded-full bg-white text-purple-900 hover:bg-purple-50 text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retake Assessment</span>
                </button>

                {onNavigateToOverview && (
                  <button
                    type="button"
                    onClick={onNavigateToOverview}
                    className="px-5 py-2.5 rounded-full bg-white/20 hover:bg-white/30 text-white text-xs font-bold border border-white/30 transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>Return to Overview</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Score Percentage Badge */}
            <div className="bg-white/10 backdrop-blur-xs p-6 rounded-2xl border border-white/20 text-center shrink-0 min-w-[150px]">
              <span className="text-xs text-purple-200 block font-medium">Accuracy</span>
              <div className="text-4xl font-extrabold text-white mt-1">
                {submissionResult.percentage}%
              </div>
              <span className="text-xs font-bold text-emerald-400 mt-1 block">
                {submissionResult.percentage >= 60 ? 'Above Benchmark' : 'Needs Practice'}
              </span>
            </div>
          </div>

          {/* Privacy Receipt */}
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" />
            <span>
              <strong>Anonymity Guarantee:</strong> Your responses to Category B (Classroom Feedback) and Category C (Student Wellbeing) have been detached from your student profile and recorded anonymously into aggregate batch statistics.
            </span>
          </div>

          {/* Objective Question Review Section */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200 shadow-2xs">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Category A: Question Breakdown & Explanations
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Review your answers, correct options, and faculty explanations below.
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
                      {item.marksAwarded} / {item.maxMarks} Marks
                    </span>
                  </div>

                  <p className="text-sm font-semibold text-gray-900 mb-2">{item.prompt}</p>

                  <div className="text-xs text-gray-700 space-y-1 mb-2">
                    {typeof item.selectedOption === 'number' ? (
                      <p>
                        Your Answer: <strong>Option {item.selectedOption + 1}</strong>
                      </p>
                    ) : (
                      <p>
                        Your Answer: <strong>"{item.selectedOption}"</strong>
                      </p>
                    )}
                  </div>

                  {item.explanation && (
                    <div className="p-3 rounded-xl bg-white/80 border border-gray-200 text-xs text-gray-700 mt-2">
                      <strong>Concept Explanation:</strong> {item.explanation}
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
