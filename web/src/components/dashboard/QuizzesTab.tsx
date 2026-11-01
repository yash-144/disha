import React, { useState } from 'react'
import {
  HelpCircle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Award,
  Sparkles,
  ArrowRight,
  Clock,
} from 'lucide-react'
import { QUIZ_QUESTIONS } from '../../mockData'
import { useApp } from '../../context/AppContext'

export function QuizzesTab() {
  const { addToast } = useApp()
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [score, setScore] = useState(0)
  const [isFinished, setIsFinished] = useState(false)

  const currentQ = QUIZ_QUESTIONS[currentIdx]

  const handleSelectOption = (idx: number) => {
    if (isAnswered) return
    setSelectedOption(idx)
    setIsAnswered(true)

    if (idx === currentQ.correctIndex) {
      setScore((prev) => prev + 1)
      addToast('Correct Answer! 🎉', '+25 points added to your score.', 'success')
    } else {
      addToast('Incorrect', 'Review the explanation below to master this concept.', 'error')
    }
  }

  const handleNext = () => {
    if (currentIdx + 1 < QUIZ_QUESTIONS.length) {
      setCurrentIdx((prev) => prev + 1)
      setSelectedOption(null)
      setIsAnswered(false)
    } else {
      setIsFinished(true)
      addToast('Quiz Completed!', `You scored ${score + (selectedOption === currentQ.correctIndex ? 1 : 0)} / ${QUIZ_QUESTIONS.length}!`, 'success')
    }
  }

  const handleRestart = () => {
    setCurrentIdx(0)
    setSelectedOption(null)
    setIsAnswered(false)
    setScore(0)
    setIsFinished(false)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 font-mono">
      <div className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-accent px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
            KNOWLEDGE LAB
          </span>
          <span className="text-xs text-muted">React &amp; Systems Architecture</span>
        </div>
        <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Interactive Skill Assessment</h2>
      </div>

      {!isFinished ? (
        <div className="border-4 border-ink bg-white p-6 shadow-[6px_6px_0_#0d1b3e]">
          {/* Progress Header */}
          <div className="flex items-center justify-between border-b-2 border-ink/10 pb-4">
            <span className="text-xs font-bold text-brand">
              Question {currentIdx + 1} of {QUIZ_QUESTIONS.length}
            </span>
            <div className="flex items-center gap-2">
              <span className="border border-ink bg-accent px-2.5 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                Score: {score * 25} PTS
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-3 h-2.5 w-full border border-ink bg-gray-100 overflow-hidden">
            <div
              className="h-full bg-brand transition-all duration-300"
              style={{ width: `${((currentIdx + 1) / QUIZ_QUESTIONS.length) * 100}%` }}
            />
          </div>

          {/* Question Text */}
          <div className="mt-6">
            <h3 className="text-base font-bold text-ink sm:text-lg leading-snug">{currentQ.question}</h3>
          </div>

          {/* Options List */}
          <div className="mt-5 space-y-3">
            {currentQ.options.map((option, idx) => {
              const isSelected = selectedOption === idx
              const isCorrect = idx === currentQ.correctIndex

              let btnStyle = 'border-ink bg-white text-ink hover:bg-gray-50 shadow-[2px_2px_0_#0d1b3e]'
              if (isAnswered) {
                if (isCorrect) {
                  btnStyle = 'border-ink bg-emerald-100 text-emerald-950 font-bold shadow-[2px_2px_0_#0f9d58]'
                } else if (isSelected && !isCorrect) {
                  btnStyle = 'border-ink bg-red-100 text-red-950 font-bold shadow-[2px_2px_0_#ef4444]'
                } else {
                  btnStyle = 'border-gray-300 bg-gray-50 text-gray-400 opacity-60'
                }
              }

              return (
                <button
                  key={idx}
                  disabled={isAnswered}
                  onClick={() => handleSelectOption(idx)}
                  className={`flex w-full items-center justify-between border-2 p-3.5 text-left text-xs font-bold transition ${btnStyle}`}
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center border border-ink bg-white text-xs font-bold shadow-xs">
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span>{option}</span>
                  </span>

                  {isAnswered && isCorrect && <CheckCircle2 className="h-5 w-5 text-emerald-700" />}
                  {isAnswered && isSelected && !isCorrect && (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                </button>
              )
            })}
          </div>

          {/* Explanation Box */}
          {isAnswered && (
            <div className="mt-5 border-2 border-ink bg-paper p-4 text-xs shadow-[3px_3px_0_#0d1b3e] animate-in fade-in">
              <p className="font-bold text-brand flex items-center gap-1.5">
                <HelpCircle className="h-4 w-4" /> Explanation &amp; Key Concept:
              </p>
              <p className="mt-1 text-gray-700 leading-relaxed">{currentQ.explanation}</p>
            </div>
          )}

          {/* Next CTA */}
          {isAnswered && (
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleNext}
                className="flex items-center gap-2 border-2 border-ink bg-accent px-6 py-2.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
              >
                {currentIdx + 1 === QUIZ_QUESTIONS.length ? 'View Final Results' : 'Next Question'}{' '}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Results Card */
        <div className="border-4 border-ink bg-white p-8 text-center shadow-[6px_6px_0_#0d1b3e]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center border-2 border-ink bg-accent text-white shadow-[3px_3px_0_#0d1b3e]">
            <Award className="h-8 w-8" />
          </div>

          <h3 className="mt-4 text-xl font-bold text-ink">Assessment Completed!</h3>
          <p className="mt-1 text-xs text-muted">
            Here is your verified performance report for this cohort module.
          </p>

          <div className="mx-auto mt-6 max-w-xs border-2 border-ink bg-paper p-4 shadow-[3px_3px_0_#0d1b3e]">
            <span className="text-xs font-bold text-gray-500">Total Score:</span>
            <p className="text-3xl font-bold text-brand">
              {score} / {QUIZ_QUESTIONS.length}
            </p>
            <p className="mt-1 text-xs font-bold text-emerald-700">
              {Math.round((score / QUIZ_QUESTIONS.length) * 100)}% Mastery Level
            </p>
          </div>

          <div className="mt-8 flex justify-center gap-3">
            <button
              onClick={handleRestart}
              className="flex items-center gap-1.5 border-2 border-ink bg-white px-5 py-2 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] hover:bg-gray-100"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Retake Assessment
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
