import React from 'react'
import {
  Heart,
  Headphones,
  Sparkles,
  ChevronRight,
  Sprout,
  AlertCircle,
  Info,
} from 'lucide-react'
import { StudentDemoScenario } from './studentDemoData'

interface StudentProfilePanelProps {
  scenario: StudentDemoScenario
  onTakeCheckIn: () => void
  onRequestSupport: () => void
  onStartAssessment: () => void
}

export function StudentProfilePanel({
  scenario,
  onTakeCheckIn,
  onRequestSupport,
  onStartAssessment,
}: StudentProfilePanelProps) {
  const { studentName, avatar, degree, year, streakWeeks, encouragement } = scenario

  const getEncouragementStyle = () => {
    switch (encouragement.variant) {
      case 'warning':
        return {
          bg: 'bg-[#FEF7EA]',
          border: 'border-[#FDE68A]',
          icon: <AlertCircle className="w-4 h-4 text-amber-600" />,
          titleColor: 'text-[#1E2433]',
          textColor: 'text-amber-800',
        }
      case 'info':
        return {
          bg: 'bg-[#EEF2FF]',
          border: 'border-[#C7D2FE]',
          icon: <Info className="w-4 h-4 text-indigo-600" />,
          titleColor: 'text-[#1E2433]',
          textColor: 'text-indigo-800',
        }
      case 'positive':
      default:
        return {
          bg: 'bg-[#EAF7EE]',
          border: 'border-[#BBF7D0]',
          icon: <Sprout className="w-4 h-4 text-emerald-600" />,
          titleColor: 'text-[#1E2433]',
          textColor: 'text-[#334155]',
        }
    }
  }

  const encStyle = getEncouragementStyle()

  return (
    <div className="w-full xl:w-72 shrink-0 flex flex-col gap-3.5 select-none">
      {/* 1. Profile Card */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100/90 shadow-2xs flex flex-col items-center text-center">
        {/* Avatar with online dot */}
        <div className="relative">
          <img
            src={avatar}
            alt={studentName}
            className="w-18 h-18 rounded-full object-cover shadow-xs border-2 border-white ring-1 ring-gray-100"
          />
          <span className="absolute bottom-1 right-1 w-3.5 h-3.5 bg-[#22C55E] ring-2 ring-white rounded-full" />
        </div>

        <h2 className="text-base font-bold text-[#1E2433] mt-2.5">
          {studentName}
        </h2>
        <p className="text-xs text-[#717E95] font-medium mt-0.5">
          {degree} • {year}
        </p>

        {/* Dynamic Encouragement Card */}
        <div
          className={`w-full mt-4 p-3 rounded-xl border flex items-start gap-2.5 text-left transition-colors duration-200 ${encStyle.bg} ${encStyle.border}`}
        >
          <div className="mt-0.5 shrink-0">{encStyle.icon}</div>
          <div>
            <h4 className={`text-xs font-bold ${encStyle.titleColor}`}>
              {encouragement.title}
            </h4>
            <p className={`text-[11px] mt-0.5 leading-snug font-medium ${encStyle.textColor}`}>
              {encouragement.description}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Quick Actions */}
      <div className="bg-white rounded-2xl p-4.5 border border-gray-100/90 shadow-2xs">
        <h3 className="text-xs font-bold text-[#1E2433] mb-2.5">
          Quick Actions
        </h3>

        <div className="flex flex-col gap-2">
          {/* Action 1: Take a Check-in */}
          <button
            type="button"
            onClick={onTakeCheckIn}
            className="w-full flex items-center justify-between p-2.5 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/40 transition group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-pink-50 text-pink-600 flex items-center justify-center shrink-0">
                <Heart className="w-3.5 h-3.5 fill-pink-500 text-pink-500" />
              </div>
              <span className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition-colors">
                Take a Check-in
              </span>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#1E2433] group-hover:translate-x-0.5 transition-all" />
          </button>

          {/* Action 2: Request Support */}
          <button
            type="button"
            onClick={onRequestSupport}
            className="w-full flex items-center justify-between p-2.5 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/40 transition group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <Headphones className="w-3.5 h-3.5 text-indigo-600" />
              </div>
              <span className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition-colors">
                Request Support
              </span>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#1E2433] group-hover:translate-x-0.5 transition-all" />
          </button>

          {/* Action 3: Start an Assessment */}
          <button
            type="button"
            onClick={onStartAssessment}
            className="w-full flex items-center justify-between p-2.5 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/40 transition group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              </div>
              <span className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition-colors">
                Start an Assessment
              </span>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#1E2433] group-hover:translate-x-0.5 transition-all" />
          </button>
        </div>
      </div>

      {/* 3. "Your Streak" Sprout Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#F5F2FE] to-[#EBE4FC] p-4.5 border border-[#DDD6FE]/80 shadow-xs flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-[#1E2433]">Your Streak</span>
          <div className="text-xl font-extrabold text-[#1E2433] mt-1">
            {streakWeeks} {streakWeeks === 1 ? 'week' : 'weeks'}
          </div>
          <p className="text-[11px] text-[#64748B] font-medium mt-0.5">
            of consistent check-ins!
          </p>
        </div>

        {/* Sprout illustration on purple mound */}
        <div className="w-16 h-16 shrink-0 relative flex items-center justify-center">
          <svg
            viewBox="0 0 80 80"
            className="w-full h-full overflow-visible"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Mound */}
            <path
              d="M10 70 C20 52 60 52 70 70 Z"
              fill="#C4B5FD"
              opacity="0.9"
            />
            <path
              d="M18 70 C28 58 52 58 62 70 Z"
              fill="#A78BFA"
              opacity="0.6"
            />

            {/* Stem */}
            <path
              d="M40 60 C40 45 42 36 44 26"
              stroke="#65A30D"
              strokeWidth="2.5"
              strokeLinecap="round"
            />

            {/* Left Leaf */}
            <path
              d="M42 38 C32 36 28 26 34 22 C40 26 42 32 42 38 Z"
              fill="#84CC16"
            />

            {/* Right Leaf */}
            <path
              d="M44 32 C54 30 58 20 52 16 C46 20 44 26 44 32 Z"
              fill="#4ADE80"
            />
          </svg>
        </div>
      </div>
    </div>
  )
}

