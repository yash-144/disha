import React from 'react'
import { Heart, Calendar, Flame, Feather } from 'lucide-react'

interface WellbeingStatsProps {
  wellbeingScore: number
  scoreDelta: string
  isScorePositive: boolean
  checkInsCompleted: number
  checkInsTotal: number
  streakWeeks: number
}

export function WellbeingStats({
  wellbeingScore,
  scoreDelta,
  isScorePositive,
  checkInsCompleted,
  checkInsTotal,
  streakWeeks,
}: WellbeingStatsProps) {
  // SVG Donut calculation
  const radius = 18
  const circumference = 2 * Math.PI * radius
  const progressRatio = Math.min(Math.max(checkInsCompleted / (checkInsTotal || 1), 0), 1)
  const strokeDashoffset = circumference * (1 - progressRatio)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 select-none">
      {/* 1. Wellbeing Score Card */}
      <div className="bg-[#FEF7DA] rounded-2xl p-4.5 border border-[#FDE68A]/40 shadow-xs flex flex-col justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433]">
          <Heart className="w-3.5 h-3.5 text-[#D97706] fill-[#FDE68A]" />
          <span>Wellbeing Score</span>
        </div>
        <div className="mt-3 flex items-baseline justify-between">
          <div className="flex items-baseline">
            <span className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
              {wellbeingScore}
            </span>
            <span className="text-xs font-semibold text-[#717E95] ml-1.5">/100</span>
          </div>

          <span
            className={`inline-flex items-center gap-0.5 text-[11px] font-bold px-2 py-0.5 rounded-full ${
              isScorePositive
                ? 'bg-[#EAF7EE] text-[#16A34A] border border-[#BBF7D0]'
                : 'bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA]'
            }`}
          >
            <span>{isScorePositive ? '↑' : '↓'}</span>
            <span>{scoreDelta}</span>
          </span>
        </div>
      </div>

      {/* 2. Check-ins Card */}
      <div className="bg-[#EBF3FE] rounded-2xl p-4.5 border border-[#BFDBFE]/40 shadow-xs flex flex-col justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433]">
          <Calendar className="w-3.5 h-3.5 text-[#2563EB]" />
          <span>Check-ins</span>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-baseline">
            <span className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
              {checkInsCompleted}
            </span>
            <span className="text-xs font-semibold text-[#717E95] ml-1.5">
              / {checkInsTotal}
            </span>
          </div>

          {/* Donut progress ring */}
          <div className="relative w-10 h-10 flex items-center justify-center">
            <svg className="w-10 h-10 -rotate-90" viewBox="0 0 44 44">
              <circle
                cx="22"
                cy="22"
                r={radius}
                className="text-[#DBEAFE]"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <circle
                cx="22"
                cy="22"
                r={radius}
                className="text-[#2563EB] transition-all duration-500 ease-out"
                stroke="currentColor"
                strokeWidth="4"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="none"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* 3. Streak Card */}
      <div className="bg-[#F0EBFE] rounded-2xl p-4.5 border border-[#DDD6FE]/40 shadow-xs flex flex-col justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#1E2433]">
          <Feather className="w-3.5 h-3.5 text-[#7C3AED]" />
          <span>Streak</span>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {streakWeeks} {streakWeeks === 1 ? 'week' : 'weeks'}
          </span>

          {/* Flame Icon with subtle glow */}
          <div className="w-8 h-8 rounded-full bg-amber-100/60 flex items-center justify-center text-amber-500">
            <Flame className="w-5 h-5 fill-amber-500 text-amber-500" />
          </div>
        </div>
      </div>
    </div>
  )
}

