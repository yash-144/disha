import React from 'react'
import { Play } from 'lucide-react'

interface SelfCareBannerProps {
  onStartBreathing: () => void
}

export function SelfCareBanner({ onStartBreathing }: SelfCareBannerProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#EDE8FB] via-[#F3EDFC] to-[#FCEEF5] p-5 border border-[#DDD6FE]/60 shadow-xs flex items-center justify-between">
      {/* Left content */}
      <div className="relative z-10 max-w-[62%] sm:max-w-[68%]">
        <h3 className="text-base font-bold text-[#1E2433] tracking-tight">
          Take a Moment for Yourself
        </h3>
        <p className="text-xs text-[#64748B] font-medium mt-1 leading-relaxed">
          A short guided activity can help you reset and feel more focused.
        </p>

        <button
          type="button"
          onClick={onStartBreathing}
          className="mt-3.5 inline-flex items-center gap-2 px-4 py-2 bg-[#1E2433] hover:bg-[#2C3549] text-white rounded-full text-xs font-semibold shadow-xs hover:shadow-sm transition transform hover:-translate-y-0.5 active:translate-y-0"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Try a 5-Min Breathing Exercise</span>
        </button>
      </div>

      {/* Right side peaceful meditation illustration */}
      <div className="relative shrink-0 w-28 sm:w-36 h-28 flex items-center justify-center">
        <svg
          viewBox="0 0 160 140"
          className="w-full h-full overflow-visible"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Soft background aura circles */}
          <circle cx="80" cy="70" r="55" fill="#E9D5FF" opacity="0.45" />
          <circle cx="95" cy="65" r="45" fill="#FCE7F3" opacity="0.5" />

          {/* Botanical leaves / foliage around her */}
          {/* Left leaf green */}
          <path
            d="M25 105 C20 80 40 70 52 82 C55 98 42 110 25 105 Z"
            fill="#86EFAC"
            opacity="0.85"
          />
          {/* Left yellow leaf */}
          <path
            d="M38 120 C32 100 48 95 60 105 C62 118 50 125 38 120 Z"
            fill="#FDE047"
            opacity="0.8"
          />
          {/* Right lilac leaf */}
          <path
            d="M135 110 C140 85 120 75 108 88 C105 102 118 115 135 110 Z"
            fill="#C084FC"
            opacity="0.75"
          />
          {/* Right mint leaf */}
          <path
            d="M122 125 C128 105 112 100 100 110 C98 122 110 130 122 125 Z"
            fill="#A7F3D0"
            opacity="0.8"
          />

          {/* Shoulders / Torso in lilac top */}
          <path
            d="M48 140 C50 112 65 102 80 102 C95 102 110 112 112 140 Z"
            fill="#C4B5FD"
          />
          <path
            d="M72 102 C72 110 88 110 88 102 Z"
            fill="#FDBA74"
            opacity="0.4"
          />

          {/* Neck */}
          <rect x="73" y="82" width="14" height="22" rx="4" fill="#FED7AA" />

          {/* Head */}
          <ellipse cx="80" cy="68" rx="16" ry="19" fill="#FED7AA" />

          {/* Long dark hair behind and around */}
          <path
            d="M62 60 C62 38 72 32 80 32 C88 32 98 38 98 60 C98 85 94 105 92 115 C88 115 88 100 88 95 C88 90 92 75 92 65 C92 50 88 44 80 44 C72 44 68 50 68 65 C68 75 72 90 72 95 C72 100 72 115 68 115 C66 105 62 85 62 60 Z"
            fill="#1E2433"
          />
          {/* Bangs / hair front */}
          <path
            d="M64 54 C70 42 78 40 85 45 C92 40 96 46 96 54 C92 48 88 47 84 50 C80 47 72 47 64 54 Z"
            fill="#1E2433"
          />

          {/* Closed peaceful eyes */}
          <path
            d="M71 67 Q75 70 77 67"
            stroke="#475569"
            strokeWidth="1.5"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M83 67 Q85 70 89 67"
            stroke="#475569"
            strokeWidth="1.5"
            strokeLinecap="round"
            fill="none"
          />

          {/* Subtle calm smile */}
          <path
            d="M76 77 Q80 80 84 77"
            stroke="#EA580C"
            strokeWidth="1.2"
            strokeLinecap="round"
            fill="none"
          />

          {/* Headphones band */}
          <path
            d="M62 65 C60 42 70 30 80 30 C90 30 100 42 98 65"
            stroke="#4F46E5"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
          {/* Headphone earcups */}
          <rect x="58" y="58" width="7" height="15" rx="3.5" fill="#6366F1" />
          <rect x="95" y="58" width="7" height="15" rx="3.5" fill="#6366F1" />
        </svg>
      </div>
    </div>
  )
}

