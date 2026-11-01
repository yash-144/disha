import React, { useState } from 'react'
import {
  Sparkles,
  BookOpen,
  MessageSquare,
  Heart,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Check,
  RotateCcw,
  HelpCircle,
  Award,
  ChevronRight,
  Send,
} from 'lucide-react'
import {
  PulseAssignment,
  PulseQuestion,
  StudentPulseSubmission,
  ObjectiveResult,
} from '../../types/studentPulse'
import {
  INITIAL_PULSE_ASSIGNMENTS,
  PULSE_QUESTION_BANK,
  INITIAL_STUDENT_SUBMISSION,
} from './studentPulseData'
import { useApp } from '../../context/AppContext'

interface StudentPulseTakingViewProps {
  onBackToOverview?: () => void
}

export function StudentPulseTakingView({ onBackToOverview }: StudentPulseTakingViewProps) {
  const { addToast } = useApp()

  // State: 'list' | 'taking' | 'results'
  const [viewState, setViewState] = useState<'list' | 'taking' | 'results'>('list')
  const [selectedPulse, setSelectedPulse] = useState<PulseAssignment>(INITIAL_PULSE_ASSIGNMENTS[0])

  // Submissions map (to track completed pulses)
  const [completedSubmissions, setCompletedSubmissions] = useState<Record<string, StudentPulseSubmission>>({
    'pulse-cs201-03': INITIAL_STUDENT_SUBMISSION,
  })

  // Active taking session state
  const [takingCategoryStep, setTakingCategoryStep] = useState<1 | 2 | 3>(1)
  const [academicAnswers, setAcademicAnswers] = useState<Record<string, number | string>>({
    'cs201-acad-01': 1,
    'cs201-acad-02': 2,
    'cs201-acad-03': 1,
    'cs201-acad-04': 1,
    'cs201-acad-05': 'DFS explores deeply with a Stack; BFS explores level-by-level with a FIFO Queue.',
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

  // Current active result being viewed
  const [activeResult, setActiveResult] = useState<StudentPulseSubmission | null>(INITIAL_STUDENT_SUBMISSION)

  // Questions for the selected pulse
  const pulseQuestions = PULSE_QUESTION_BANK.filter((q) =>
    selectedPulse.questionIds.includes(q.id)
  )
  const academicQuestions = pulseQuestions.filter((q) => q.category === 'ACADEMIC')
  const feedbackQuestions = pulseQuestions.filter((q) => q.category === 'CLASSROOM_FEEDBACK')
  const wellbeingQuestions = pulseQuestions.filter((q) => q.category === 'WELLBEING')

  // Start taking a pulse
  const handleStartTaking = (pulse: PulseAssignment) => {
    setSelectedPulse(pulse)
    setTakingCategoryStep(1)
    setViewState('taking')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // View results of already completed pulse
  const handleViewResults = (pulse: PulseAssignment) => {
    setSelectedPulse(pulse)
    const existing = completedSubmissions[pulse.id]
    if (existing) {
      setActiveResult(existing)
    }
    setViewState('results')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Submit pulse responses
  const handleSubmitPulse = () => {
    // Grade academic questions
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
    const newSubmission: StudentPulseSubmission = {
      submissionId: `sub-${selectedPulse.id}-${Date.now().toString().slice(-4)}`,
      pulseId: selectedPulse.id,
      studentId: 'student-current-user',
      studentName: 'Asha Verma',
      academicScore: Math.round(earnedMarks * 10) / 10,
      academicMaxMarks: totalMaxMarks,
      percentage: pct,
      submittedAt: new Date().toISOString(),
      isAnonymous: true,
      objectiveResults,
    }

    setCompletedSubmissions((prev) => ({
      ...prev,
      [selectedPulse.id]: newSubmission,
    }))
    setActiveResult(newSubmission)
    setViewState('results')
    window.scrollTo({ top: 0, behavior: 'smooth' })

    addToast(
      'Student Pulse Submitted! 🎉',
      `Academic Score: ${newSubmission.academicScore}/${newSubmission.academicMaxMarks} (${pct}%). Feedback submitted anonymously.`,
      'success'
    )
  }

  return (
    <div className="flex flex-col gap-5 font-sans">
      {/* 1. LIST VIEW: Active and Completed Student Pulses */}
      {viewState === 'list' && (
        <div className="flex flex-col gap-5">
          {/* Active Pulses Grid */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-base font-bold text-gray-900">
                  Active Student Pulse Assignments
                </h3>
                <p className="text-xs text-gray-500">
                  Complete these assessments to demonstrate your subject understanding and share anonymous classroom feedback.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {INITIAL_PULSE_ASSIGNMENTS.filter((p) => p.status === 'published').map((pulse) => {
                const isCompleted = !!completedSubmissions[pulse.id]
                const submission = completedSubmissions[pulse.id]

                return (
                  <div
                    key={pulse.id}
                    className="bg-white rounded-3xl p-5 border border-purple-100/90 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      {/* Top badging */}
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
                          {pulse.courseId} • {pulse.sectionId}
                        </span>
                        {isCompleted ? (
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Completed ({submission.percentage}%)
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">
                            Active • Due in 3 days
                          </span>
                        )}
                      </div>

                      <h4 className="font-bold text-gray-900 text-base leading-snug">
                        {pulse.title}
                      </h4>

                      {/* 3 Categories Badges */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-3">
                        <span className="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 text-[11px] font-semibold border border-purple-100">
                          {pulse.academicCount} Academic Qs
                        </span>
                        <span className="px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 text-[11px] font-semibold border border-sky-100">
                          {pulse.feedbackCount} Feedback Qs
                        </span>
                        <span className="px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 text-[11px] font-semibold border border-rose-100">
                          {pulse.wellbeingCount} Wellbeing Qs
                        </span>
                      </div>

                      <p className="text-xs text-gray-500 mt-3">
                        Randomized questions from course question bank covering core concepts, lecture pace, and workload.
                      </p>
                    </div>

                    <div className="mt-5 pt-3 border-t border-line flex items-center justify-between">
                      <div className="text-[11px] text-gray-500 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        Due {new Date(pulse.dueAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>

                      {isCompleted ? (
                        <button
                          type="button"
                          onClick={() => handleViewResults(pulse)}
                          className="px-4 py-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
                        >
                          <Award className="w-3.5 h-3.5" />
                          View Results & Answers
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleStartTaking(pulse)}
                          className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
                        >
                          Start Pulse Assessment
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* 2. TAKING VIEW: Multi-step interactive assessment */}
      {viewState === 'taking' && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-2xs flex flex-col gap-6">
          {/* Header & Steps Progress Bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
                {selectedPulse.courseId} • {selectedPulse.title}
              </span>
              <button
                type="button"
                onClick={() => setViewState('list')}
                className="text-xs text-gray-500 hover:text-gray-800 font-medium cursor-pointer"
              >
                Cancel & Exit
              </button>
            </div>

            <div className="flex items-center gap-3 mt-4">
              {/* Step 1 */}
              <div
                className={`flex-1 flex items-center gap-2 p-2.5 rounded-xl border transition-all ${
                  takingCategoryStep === 1
                    ? 'bg-purple-50 border-purple-300 text-purple-900 font-bold'
                    : takingCategoryStep > 1
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-gray-50 border-line text-muted'
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-current text-white text-[11px] font-bold flex items-center justify-center">
                  1
                </span>
                <span className="text-xs">Category A: Academic</span>
              </div>

              {/* Step 2 */}
              <div
                className={`flex-1 flex items-center gap-2 p-2.5 rounded-xl border transition-all ${
                  takingCategoryStep === 2
                    ? 'bg-sky-50 border-sky-300 text-sky-900 font-bold'
                    : takingCategoryStep > 2
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-gray-50 border-line text-muted'
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-current text-white text-[11px] font-bold flex items-center justify-center">
                  2
                </span>
                <span className="text-xs">Category B: Feedback</span>
              </div>

              {/* Step 3 */}
              <div
                className={`flex-1 flex items-center gap-2 p-2.5 rounded-xl border transition-all ${
                  takingCategoryStep === 3
                    ? 'bg-rose-50 border-rose-300 text-rose-900 font-bold'
                    : 'bg-gray-50 border-line text-muted'
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-current text-white text-[11px] font-bold flex items-center justify-center">
                  3
                </span>
                <span className="text-xs">Category C: Wellbeing</span>
              </div>
            </div>
          </div>

          {/* STEP 1: CATEGORY A - ACADEMIC ASSESSMENT */}
          {takingCategoryStep === 1 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="p-3.5 rounded-2xl bg-purple-50/70 border border-purple-200 text-xs text-purple-900 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-purple-600 shrink-0" />
                <span>
                  <strong>Category A: Subject Knowledge Evaluation.</strong> Answer the objective and descriptive questions below. Correct answers and auto-grades will be computed immediately upon submission.
                </span>
              </div>

              {academicQuestions.map((q, idx) => (
                <div key={q.id} className="p-4 sm:p-5 rounded-2xl bg-paper border border-line">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-700">Question {idx + 1} of {academicQuestions.length}</span>
                    <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      {q.marks} Marks
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 mb-3">{q.prompt}</p>

                  {/* MCQ Options */}
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
                                ? 'bg-purple-100/70 border-purple-400 text-purple-950 font-semibold'
                                : 'bg-white border-line text-gray-700 hover:bg-gray-50'
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

                  {/* Descriptive text area */}
                  {q.questionType === 'descriptive' && (
                    <div>
                      <textarea
                        rows={3}
                        value={(academicAnswers[q.id] as string) || ''}
                        onChange={(e) =>
                          setAcademicAnswers((prev) => ({
                            ...prev,
                            [q.id]: e.target.value,
                          }))
                        }
                        placeholder="Write your explanation concisely..."
                        className="w-full p-3 rounded-xl border border-gray-300 text-xs sm:text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white font-sans"
                      />
                    </div>
                  )}
                </div>
              ))}

              <div className="flex justify-end pt-3">
                <button
                  type="button"
                  onClick={() => setTakingCategoryStep(2)}
                  className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-2xs flex items-center gap-2 cursor-pointer"
                >
                  Continue to Classroom Feedback
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: CATEGORY B - CLASSROOM FEEDBACK */}
          {takingCategoryStep === 2 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="p-3.5 rounded-2xl bg-sky-50 border border-sky-200 text-xs text-sky-950 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-600 shrink-0" />
                <span>
                  <strong>Category B: Classroom Feedback is 100% Anonymous.</strong> Your answers are aggregated with batch responses under k-anonymity (≥5). Your instructor cannot view individual feedback entries.
                </span>
              </div>

              {feedbackQuestions.map((q, idx) => (
                <div key={q.id} className="p-4 sm:p-5 rounded-2xl bg-paper border border-line">
                  <span className="text-xs font-bold text-sky-700 mb-1 block">Feedback Question {idx + 1}</span>
                  <p className="text-sm font-semibold text-gray-900 mb-3">{q.prompt}</p>

                  {/* Single Choice / Likert options */}
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
                              ? 'bg-sky-100/70 border-sky-400 text-sky-950 font-semibold'
                              : 'bg-white border-line text-gray-700 hover:bg-gray-50'
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

              <div className="flex items-center justify-between pt-3">
                <button
                  type="button"
                  onClick={() => setTakingCategoryStep(1)}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-gray-600 hover:bg-gray-100 transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Academic
                </button>
                <button
                  type="button"
                  onClick={() => setTakingCategoryStep(3)}
                  className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-2xs flex items-center gap-2 cursor-pointer"
                >
                  Continue to Wellbeing Check
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: CATEGORY C - STUDENT WELLBEING */}
          {takingCategoryStep === 3 && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-950 flex items-center gap-2">
                <Heart className="w-4 h-4 text-rose-600 shrink-0" />
                <span>
                  <strong>Category C: Academic Wellbeing & Motivation.</strong> Phrased constructively to help faculty identify whether students need revision clinics or pacing adjustments.
                </span>
              </div>

              {wellbeingQuestions.map((q, idx) => (
                <div key={q.id} className="p-4 sm:p-5 rounded-2xl bg-paper border border-line">
                  <span className="text-xs font-bold text-rose-700 mb-1 block">Wellbeing Question {idx + 1}</span>
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
                              ? 'bg-rose-100/70 border-rose-400 text-rose-950 font-semibold'
                              : 'bg-white border-line text-gray-700 hover:bg-gray-50'
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

              <div className="flex items-center justify-between pt-4 border-t border-line">
                <button
                  type="button"
                  onClick={() => setTakingCategoryStep(2)}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-gray-600 hover:bg-gray-100 transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Feedback
                </button>
                <button
                  type="button"
                  onClick={handleSubmitPulse}
                  className="px-7 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer"
                >
                  <Send className="w-4 h-4" />
                  Submit Student Pulse
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. RESULTS VIEW: Instant score & objective answers review */}
      {viewState === 'results' && activeResult && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-200">
          {/* Top Score Banner Card */}
          <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300 text-xs font-bold border border-emerald-400/30">
                  Assessment Completed
                </span>
                <span className="text-xs text-purple-200">•</span>
                <span className="text-xs text-purple-200 font-medium">
                  Submitted {new Date(activeResult.submittedAt).toLocaleDateString()}
                </span>
              </div>
              <h2 className="text-2xl font-bold tracking-tight">
                {selectedPulse.title}
              </h2>
              <p className="text-xs sm:text-sm text-purple-200 mt-1">
                Your answers to Category A have been graded. Feedback and wellbeing inputs are securely anonymized.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-xs p-5 rounded-2xl border border-white/20 text-center shrink-0">
              <span className="text-xs text-purple-200 block font-medium">Academic Score</span>
              <div className="text-3xl font-extrabold text-white mt-0.5">
                {activeResult.academicScore} <span className="text-lg text-purple-200">/ {activeResult.academicMaxMarks}</span>
              </div>
              <span className="text-xs font-bold text-emerald-400 mt-1 block">
                {activeResult.percentage}% Correct
              </span>
            </div>
          </div>

          {/* Privacy Guarantee Receipt */}
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
            <span>
              <strong>Anonymity Receipt:</strong> Your responses to Category B (Classroom Feedback) and Category C (Student Wellbeing) have been detached from your student profile and recorded anonymously into aggregate cohort statistics.
            </span>
          </div>

          {/* Objective Question Review Section */}
          <div className="bg-white rounded-3xl p-6 border border-line shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-line">
              <div>
                <h3 className="text-base font-bold text-gray-900">
                  Academic Question Breakdown & Answers
                </h3>
                <p className="text-xs text-gray-500">
                  Review your answers alongside official concepts and faculty explanations.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setViewState('list')}
                className="px-4 py-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold transition-colors cursor-pointer"
              >
                Back to Pulse List
              </button>
            </div>

            <div className="space-y-4">
              {activeResult.objectiveResults.map((item, idx) => (
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
                    <div className="p-3 rounded-xl bg-white/80 border border-line text-xs text-gray-700">
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

