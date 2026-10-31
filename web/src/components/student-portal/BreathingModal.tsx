import React, { useState, useEffect } from 'react'
import { X, Play, Pause, RotateCcw } from 'lucide-react'

interface BreathingModalProps {
  isOpen: boolean
  onClose: () => void
}

type BreathingPhase = 'Inhale' | 'Hold' | 'Exhale' | 'Rest'

export function BreathingModal({ isOpen, onClose }: BreathingModalProps) {
  const [isPlaying, setIsPlaying] = useState(true)
  const [phase, setPhase] = useState<BreathingPhase>('Inhale')
  const [countdown, setCountdown] = useState(4)
  const [cycleCount, setCycleCount] = useState(0)

  useEffect(() => {
    if (!isOpen || !isPlaying) return

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev > 1) return prev - 1

        // Switch phases
        if (phase === 'Inhale') {
          setPhase('Hold')
          return 4
        } else if (phase === 'Hold') {
          setPhase('Exhale')
          return 4
        } else if (phase === 'Exhale') {
          setPhase('Rest')
          return 2
        } else {
          setPhase('Inhale')
          setCycleCount((c) => c + 1)
          return 4
        }
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isOpen, isPlaying, phase])

  if (!isOpen) return null

  // Circle scaling depending on breathing phase
  const getScaleClass = () => {
    switch (phase) {
      case 'Inhale':
        return 'scale-125 duration-4000 ease-out'
      case 'Hold':
        return 'scale-125 duration-1000'
      case 'Exhale':
        return 'scale-90 duration-4000 ease-in'
      case 'Rest':
        return 'scale-90 duration-2000'
    }
  }

  const getPhaseColor = () => {
    switch (phase) {
      case 'Inhale':
        return 'text-[#6366F1]'
      case 'Hold':
        return 'text-[#8B5CF6]'
      case 'Exhale':
        return 'text-[#10B981]'
      case 'Rest':
        return 'text-[#64748B]'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-purple-100 flex flex-col items-center text-center">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-gray-800 flex items-center justify-center transition"
        >
          <X className="w-4 h-4" />
        </button>

        <span className="text-[11px] font-bold uppercase tracking-wider text-purple-600 bg-purple-50 px-2.5 py-1 rounded-full mb-3">
          Mindfulness & Focus
        </span>

        <h3 className="text-xl font-bold text-[#1E2433]">
          Mindful Box Breathing
        </h3>
        <p className="text-xs text-[#64748B] mt-1 max-w-xs">
          Take a deep, slow breath to relieve study stress and center your focus.
        </p>

        {/* Breathing Animation Canvas */}
        <div className="my-8 relative w-48 h-48 flex items-center justify-center">
          {/* Outer glowing ripple */}
          <div
            className={`absolute inset-0 rounded-full bg-gradient-to-tr from-purple-100 via-indigo-50 to-pink-50 transition-all ${getScaleClass()} opacity-80`}
          />

          {/* Inner pulsating circle */}
          <div
            className={`relative w-36 h-36 rounded-full bg-gradient-to-tr from-[#8B5CF6] to-[#6366F1] shadow-lg flex flex-col items-center justify-center text-white transition-all ${getScaleClass()}`}
          >
            <span className="text-2xl font-black">{countdown}</span>
            <span className="text-xs font-semibold uppercase tracking-wider mt-0.5">
              {phase}
            </span>
          </div>
        </div>

        {/* Guidance caption */}
        <p className={`text-sm font-bold tracking-tight ${getPhaseColor()} mb-4`}>
          {phase === 'Inhale' && 'Slowly breathe in through your nose...'}
          {phase === 'Hold' && 'Hold your breath comfortably...'}
          {phase === 'Exhale' && 'Gently exhale all the air out...'}
          {phase === 'Rest' && 'Pause and relax your shoulders...'}
        </p>

        {/* Controls */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center gap-2 px-5 py-2 rounded-full bg-[#1E2433] text-white text-xs font-semibold hover:bg-[#2F384C] transition shadow-xs"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setPhase('Inhale')
              setCountdown(4)
              setCycleCount(0)
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold hover:bg-gray-200 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>

        <span className="text-[11px] text-gray-400 mt-4">
          Cycles completed: {cycleCount}
        </span>
      </div>
    </div>
  )
}

