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
  HelpCircle,
  Check,
  AlertCircle,
  Eye,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'
import { useApp } from '../../context/AppContext'
import {
  PULSE_QUESTION_BANK,
  INITIAL_PULSE_ASSIGNMENTS,
  INITIAL_STUDENT_SUBMISSION,
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

  // Selected pulse assignment (defaults to CS201 Student Pulse #3)
  const [selectedPulseId, setSelectedPulseId] = useState<string>('pulse-cs201-03')
  const currentPulse =
    INITIAL_PULSE_ASSIGNMENTS.find((p) => p.id === selectedPulseId) ||
    INITIAL_PULSE_ASSIGNMENTS[0]

  // Filter questions for the active pulse
  const activeQuestions: PulseQuestion[] = PULSE_QUESTION_BANK.filter((q) =>
    currentPulse.questionIds.includes(q.id)
  )

  const academicQuestions = activeQuestions.filter((q) => q.category === 'ACADEMIC')
  const feedbackQuestions = activeQuestions.filter((q) => q.category === 'CLASSROOM_FEEDBACK')
  const wellbeingQuestions = activeQuestions.filter((q) => q.category === 'WELLBEING')

  // Student Answers State
  const [academicAnswers, setAcademicAnswers] = useState<Record<string, number | string>>({
    'cs201-acad-01': 1,
    'cs201-acad-02': 2,
    'cs201-acad-03': 1,
    'cs201-acad-04': 1,
    'cs201-acad-05': 'DFS utilizes a Last-In-First-Out call stack to probe along branch depths. BFS utilizes a FIFO Queue to traverse frontier nodes level by level.',
  })

  const [feedbackAnswers, setFeedbackAnswers] = useState<Record<string, string | number>>({
    'cs201-feed-01': 'Just right – comfortable pace with balanced problem breakdowns',
    'cs201-feed-02': 4,
    'cs201-feed-03': 'Very comfortable speaking up right away in class',
    'cs201-feed-04': 4,
  })

  const [wellbeingAnswers, setWellbeingAnswers] = useState<Record<string, number | string>>({
    'cs201-well-01': 4,
    'cs201-well-02': 3,
    'cs201-well-03': 4,
  })

  // Mode: 'take' (answering questions) | 'submitted' (viewing score & explanations)
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false)
  const [submissionResult, setSubmissionResult] = useState<StudentPulseSubmission | null>(null)

  // Active category filter tab in taking mode
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<'ALL' | 'ACADEMIC' | 'FEEDBACK' | 'WELLBEING'>('ALL')

  // Calculate answer progress
  const answeredAcademicCount = Object.keys(academicAnswers).length
  const answeredFeedbackCount = Object.keys(feedbackAnswers).length
  const answeredWellbeingCount = Object.keys(wellbeingAnswers).length
  const totalAnswered = answeredAcademicCount + answeredFeedbackCount + answeredWellbeingCount
  const totalQuestionsCount = activeQuestions.length
  const completionPercentage = Math.round((totalAnswered / Math.max(totalQuestionsCount, 1)) * 100)

  // Submit Handler
  const handleSubmit = () => {
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
        const awarded = q.marks * 0.8
        earnedMarks += awarded
        objectiveResults.push({
          questionId: q.id,
          prompt: q.prompt,
          selectedOption: userAns,
          correctOption: undefined,
          isCorrect: true,
          marksAwarded: awarded,
          maxMarks: q.marks,
          explanation: 'Descriptive response submitted. Provisional marks awarded; pending faculty rubric review.',
        })
      }
    })

    const pct = Math.round((earnedMarks / totalMaxMarks) * 100)
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
    setIsSubmitted(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })

    addToast(
      'Student Pulse Submitted! 🎉',
      `Academic Score: ${result.academicScore}/${result.academicMaxMarks} (${pct}%). Feedback submitted anonymously.`,
      'success'
    )
  }

  // Retake Assessment
  const handleRetake = () => {
    setIsSubmitted(false)
    setSubmissionResult(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="flex-1 flex flex-col gap-5 font-sans select-none pb-12">
      {/* 1. Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#EDE8FB] via-[#F3EDFC] to-[#FCEEF5] p-6 sm:p-7 border border-[#DDD6FE]/70 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div className="max-w-2xl z-10">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/90 border border-purple-200 text-purple-700 text-xs font-bold shadow-2xs">
              <Sparkles className="w-3.5 h-3.5" />
              Student Pulse • Academic Assessment & Feedback
            </span>
            <span className="text-xs text-purple-400">•</span>
            <span className="text-xs font-bold text-purple-700 bg-purple-100/60 px-2 py-0.5 rounded-md">
              {currentPulse.courseId}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {currentPulse.title}
          </h1>
          <p className="text-xs sm:text-sm text-[#475569] font-medium mt-1.5 leading-relaxed">
            Answer the 3 randomized question categories below: evaluate your subject knowledge, share honest classroom feedback, and reflect on your academic workload.
          </p>

          {/* Metadata badges */}
          <div className="flex flex-wrap items-center gap-3 mt-4">
            <div className="flex items-center gap-1.5 text-xs text-gray-600 font-semibold bg-white/80 px-3 py-1 rounded-full border border-purple-100">
              <Clock className="w-3.5 h-3.5 text-purple-600" />
              <span>Due: {new Date(currentPulse.dueAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-600 font-semibold bg-white/80 px-3 py-1 rounded-full border border-purple-100">
              <BookOpen className="w-3.5 h-3.5 text-purple-600" />
              <span>{academicQuestions.length} Academic Qs</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-600 font-semibold bg-white/80 px-3 py-1 rounded-full border border-purple-100">
              <MessageSquare className="w-3.5 h-3.5 text-sky-600" />
              <span>{feedbackQuestions.length} Feedback Qs (Anonymous)</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-600 font-semibold bg-white/80 px-3 py-1 rounded-full border border-purple-100">
              <Heart className="w-3.5 h-3.5 text-rose-600" />
              <span>{wellbeingQuestions.length} Wellbeing Qs</span>
            </div>
          </div>
        </div>

        {/* Pulse Switcher dropdown */}
        <div className="flex flex-col items-end gap-2 shrink-0">
          <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
            Switch Course Pulse:
          </label>
          <select
            value={selectedPulseId}
            onChange={(e) => {
              setSelectedPulseId(e.target.value)
              setIsSubmitted(false)
              setSubmissionResult(null)
            }}
            className="px-3 py-2 rounded-xl bg-white border border-purple-200 text-xs font-bold text-purple-950 focus:ring-2 focus:ring-purple-400 focus:outline-none shadow-2xs cursor-pointer"
          >
            {INITIAL_PULSE_ASSIGNMENTS.filter((p) => p.status === 'published').map((p) => (
              <option key={p.id} value={p.id}>
                {p.courseId} — {p.title}
              </option>
            ))}
          </select>

          {isSubmitted ? (
            <button
              type="button"
              onClick={handleRetake}
              className="text-xs font-bold text-purple-700 hover:text-purple-900 underline flex items-center gap-1 cursor-pointer mt-1"
            >
              <RotateCcw className="w-3 h-3" />
              Retake Assessment
            </button>
          ) : (
            <div className="text-xs text-emerald-700 font-bold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 mt-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              100% Anonymized Feedback
            </div>
          )}
        </div>
      </div>

      {/* 2. POST-SUBMISSION RESULTS VIEW (Visible when student submits) */}
      {isSubmitted && submissionResult && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-200">
          {/* Score Banner Card */}
          <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 text-white rounded-3xl p-6 sm:p-7 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
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
              <h2 className="text-2xl font-bold tracking-tight">
                Academic Performance Score: {submissionResult.academicScore} / {submissionResult.academicMaxMarks} Marks
              </h2>
              <p className="text-xs sm:text-sm text-purple-200 mt-1">
                Your answers to Category A (Academic Assessment) have been computed below with correct answer keys and concept explanations.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-xs p-5 rounded-2xl border border-white/20 text-center shrink-0 min-w-[140px]">
              <span className="text-xs text-purple-200 block font-medium">Accuracy</span>
              <div className="text-3xl font-extrabold text-white mt-0.5">
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
              <strong>Anonymity Guarantee:</strong> Your responses to Category B (Classroom Feedback) and Category C (Student Wellbeing) have been detached from your student account and submitted anonymously to cohort aggregates.
            </span>
          </div>

          {/* Graded Objective Questions Review */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200 shadow-2xs">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Category A: Question Breakdown & Answers
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Review your answers, correct options, and faculty explanations below.
            </p>

            <div className="space-y-4">
              {submissionResult.objectiveResults.map((item, idx) => (
                <div
                  key={item.questionId}
                  className={`p-4 rounded-2xl border ${
                    item.isCorrect
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : 'bg-rose-50/40 border-rose-200'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                          item.isCorrect
                            ? 'bg-emerald-600 text-white'
                            : 'bg-rose-600 text-white'
                        }`}
                      >
                        {item.isCorrect ? '✓' : '✗'}
                      </span>
                      <span className="text-xs font-bold text-gray-800">
                        Question {idx + 1}
                      </span>
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

      {/* 3. ACTIVE QUESTIONS VIEW (Immediately visible on page) */}
      {!isSubmitted && (
        <div className="flex flex-col gap-6">
          {/* Category Filter Pills & Progress Bar */}
          <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-2xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
              <span className="text-xs font-bold text-gray-700 mr-1">Filter:</span>
              <button
                type="button"
                onClick={() => setActiveCategoryFilter('ALL')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                  activeCategoryFilter === 'ALL'
                    ? 'bg-purple-600 text-white shadow-2xs'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                All Questions ({activeQuestions.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategoryFilter('ACADEMIC')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1 ${
                  activeCategoryFilter === 'ACADEMIC'
                    ? 'bg-purple-600 text-white shadow-2xs'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                Academic ({academicQuestions.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategoryFilter('FEEDBACK')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1 ${
                  activeCategoryFilter === 'FEEDBACK'
                    ? 'bg-sky-600 text-white shadow-2xs'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                Feedback ({feedbackQuestions.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategoryFilter('WELLBEING')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1 ${
                  activeCategoryFilter === 'WELLBEING'
                    ? 'bg-rose-600 text-white shadow-2xs'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Heart className="w-3.5 h-3.5" />
                Wellbeing ({wellbeingQuestions.length})
              </button>
            </div>

            {/* Answered progress */}
            <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
              <span className="text-xs text-gray-600 font-medium">
                Answered: <strong>{totalAnswered}</strong> / {totalQuestionsCount}
              </span>
              <div className="w-28 h-2 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all duration-300"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>
            </div>
          </div>

          {/* =========================================================================
              CATEGORY A: ACADEMIC ASSESSMENT QUESTIONS
             ========================================================================= */}
          {(activeCategoryFilter === 'ALL' || activeCategoryFilter === 'ACADEMIC') && (
            <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-2xs">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs">
                    A
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900">
                      Category A: Academic Assessment ({academicQuestions.length} Questions)
                    </h2>
                    <p className="text-xs text-gray-500">
                      Evaluates your subject knowledge and algorithmic understanding. Auto-graded on submission.
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 font-bold text-xs border border-purple-200">
                  {currentPulse.totalMarks} Total Marks
                </span>
              </div>

              <div className="space-y-5">
                {academicQuestions.map((q, idx) => (
                  <div
                    key={q.id}
                    className="p-4 sm:p-5 rounded-2xl bg-[#FAFAFC] border border-gray-200/90 hover:border-purple-200 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                          {q.questionType}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            q.difficulty === 'Easy'
                              ? 'bg-emerald-100 text-emerald-800'
                              : q.difficulty === 'Medium'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {q.difficulty}
                        </span>
                      </div>
                      <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        {q.marks} Marks
                      </span>
                    </div>

                    <p className="text-sm font-semibold text-gray-900 mb-3">{q.prompt}</p>

                    {/* MCQ Options Radio List */}
                    {q.questionType === 'mcq' && (
                      <div className="space-y-2">
                        {q.options.map((opt, optIdx) => {
                          const isSelected = academicAnswers[q.id] === optIdx
                          return (
                            <button
                              key={optIdx}
                              type="button"
                              onClick={() =>
                                setAcademicAnswers((prev) => ({
                                  ...prev,
                                  [q.id]: optIdx,
                                }))
                              }
                              className={`w-full text-left p-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex items-center justify-between cursor-pointer ${
                                isSelected
                                  ? 'bg-purple-100/70 border-purple-400 text-purple-950 font-semibold shadow-2xs'
                                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              <span>{opt}</span>
                              <div
                                className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                                  isSelected ? 'border-purple-600 bg-purple-600 text-white' : 'border-gray-300'
                                }`}
                              >
                                {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* Descriptive Text Area */}
                    {q.questionType === 'descriptive' && (
                      <div className="space-y-2">
                        <textarea
                          rows={3}
                          value={(academicAnswers[q.id] as string) || ''}
                          onChange={(e) =>
                            setAcademicAnswers((prev) => ({
                              ...prev,
                              [q.id]: e.target.value,
                            }))
                          }
                          placeholder="Type your explanation clearly..."
                          className="w-full p-3 rounded-xl border border-gray-300 text-xs sm:text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white font-sans"
                        />
                        <span className="text-[11px] text-gray-400 block text-right">
                          Evaluated by instructor against conceptual rubrics.
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* =========================================================================
              CATEGORY B: CLASSROOM FEEDBACK QUESTIONS (ANONYMOUS)
             ========================================================================= */}
          {(activeCategoryFilter === 'ALL' || activeCategoryFilter === 'FEEDBACK') && (
            <div className="bg-white rounded-3xl p-6 border border-sky-100 shadow-2xs">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs">
                    B
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900">
                      Category B: Classroom Feedback ({feedbackQuestions.length} Questions)
                    </h2>
                    <p className="text-xs text-gray-500">
                      Share honest feedback on lecture pacing, explanation clarity, and engagement.
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-sky-50 text-sky-700 font-bold text-xs border border-sky-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> 100% Anonymous
                </span>
              </div>

              <div className="space-y-5">
                {feedbackQuestions.map((q, idx) => (
                  <div
                    key={q.id}
                    className="p-4 sm:p-5 rounded-2xl bg-[#FAFAFC] border border-gray-200/90 hover:border-sky-200 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 text-xs font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <span className="text-xs font-bold text-sky-900 uppercase tracking-wider">
                          {q.parameterTag?.replace('_', ' ') || 'Feedback'}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm font-semibold text-gray-900 mb-3">{q.prompt}</p>

                    <div className="space-y-2">
                      {q.options.map((opt, optIdx) => {
                        const isSelected =
                          feedbackAnswers[q.id] === opt || feedbackAnswers[q.id] === optIdx + 1
                        return (
                          <button
                            key={optIdx}
                            type="button"
                            onClick={() =>
                              setFeedbackAnswers((prev) => ({
                                ...prev,
                                [q.id]: opt,
                              }))
                            }
                            className={`w-full text-left p-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex items-center justify-between cursor-pointer ${
                              isSelected
                                ? 'bg-sky-100/70 border-sky-400 text-sky-950 font-semibold shadow-2xs'
                                : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            <span>{opt}</span>
                            <div
                              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                                isSelected ? 'border-sky-600 bg-sky-600 text-white' : 'border-gray-300'
                              }`}
                            >
                              {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* =========================================================================
              CATEGORY C: STUDENT WELLBEING QUESTIONS
             ========================================================================= */}
          {(activeCategoryFilter === 'ALL' || activeCategoryFilter === 'WELLBEING') && (
            <div className="bg-white rounded-3xl p-6 border border-rose-100 shadow-2xs">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs">
                    C
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900">
                      Category C: Student Wellbeing & Workload ({wellbeingQuestions.length} Questions)
                    </h2>
                    <p className="text-xs text-gray-500">
                      Helps instructors identify if difficulty is driven by concept gaps or high deadline pressure.
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 font-bold text-xs border border-rose-200">
                  Non-diagnostic
                </span>
              </div>

              <div className="space-y-5">
                {wellbeingQuestions.map((q, idx) => (
                  <div
                    key={q.id}
                    className="p-4 sm:p-5 rounded-2xl bg-[#FAFAFC] border border-gray-200/90 hover:border-rose-200 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-rose-100 text-rose-700 text-xs font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <span className="text-xs font-bold text-rose-900 uppercase tracking-wider">
                          {q.parameterTag?.replace('_', ' ') || 'Wellbeing'}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm font-semibold text-gray-900 mb-3">{q.prompt}</p>

                    <div className="space-y-2">
                      {q.options.map((opt, optIdx) => {
                        const isSelected =
                          wellbeingAnswers[q.id] === opt || wellbeingAnswers[q.id] === optIdx + 1
                        return (
                          <button
                            key={optIdx}
                            type="button"
                            onClick={() =>
                              setWellbeingAnswers((prev) => ({
                                ...prev,
                                [q.id]: opt,
                              }))
                            }
                            className={`w-full text-left p-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex items-center justify-between cursor-pointer ${
                              isSelected
                                ? 'bg-rose-100/70 border-rose-400 text-rose-950 font-semibold shadow-2xs'
                                : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            <span>{opt}</span>
                            <div
                              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                                isSelected ? 'border-rose-600 bg-rose-600 text-white' : 'border-gray-300'
                              }`}
                            >
                              {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Submission Bar */}
          <div className="bg-white rounded-3xl p-5 border border-purple-100 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4 sticky bottom-4 z-20">
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>
                <strong>{totalAnswered}</strong> of {totalQuestionsCount} questions answered. Category B & C are strictly anonymized.
              </span>
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              className="w-full sm:w-auto px-8 py-3 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <Send className="w-4 h-4" />
              Submit Student Pulse Assessment
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
