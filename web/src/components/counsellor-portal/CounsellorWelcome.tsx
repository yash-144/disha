import React from 'react'

interface CounsellorWelcomeProps {
  name?: string
  subtitle?: string
}

export function CounsellorWelcome({
  name = 'Dr. Meera',
  subtitle = "Here's an overview of your counselling activities at DISHA.",
}: CounsellorWelcomeProps) {
  return (
    <div className="flex flex-col lg:flex-row items-stretch gap-4 select-none font-sans">
      {/* Left Welcome Card with Dr. Meera illustration */}
      <div className="flex-1 bg-white rounded-3xl p-5 sm:p-6 border border-purple-100/70 shadow-2xs flex items-center justify-between relative overflow-hidden">
        {/* Left greeting text */}
        <div className="max-w-md z-10">
          <h1 className="text-2xl sm:text-[26px] font-extrabold tracking-tight text-[#1E2433] flex items-center gap-2">
            <span>Welcome back, {name}!</span>
            <span className="text-2xl">👋</span>
          </h1>
          <p className="text-xs sm:text-[13px] text-[#717E95] font-medium mt-1.5 leading-relaxed">
            {subtitle}
          </p>
        </div>

        {/* Right Counsellor Vector Illustration matching the reference screenshot */}
        <div className="relative shrink-0 w-36 sm:w-44 h-28 sm:h-32 flex items-center justify-center">
          <svg
            viewBox="0 0 180 140"
            className="w-full h-full overflow-visible"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Soft background aura circles */}
            <circle cx="90" cy="70" r="58" fill="#EDE9FE" opacity="0.65" />
            <circle cx="110" cy="65" r="45" fill="#FCE7F3" opacity="0.45" />

            {/* Botanical pastel leaves in background */}
            <path
              d="M35 110 C25 80 50 65 65 80 C70 98 52 115 35 110 Z"
              fill="#A7F3D0"
              opacity="0.8"
            />
            <path
              d="M145 115 C155 85 130 70 115 85 C110 102 128 120 145 115 Z"
              fill="#C4B5FD"
              opacity="0.75"
            />
            <path
              d="M130 60 C140 40 155 45 150 60 C142 70 132 68 130 60 Z"
              fill="#FDE047"
              opacity="0.75"
            />

            {/* Shoulders / White Clinical Coat with Purple Scrub Top */}
            <path
              d="M50 140 C52 110 68 100 90 100 C112 100 128 110 130 140 Z"
              fill="#FFFFFF"
              stroke="#E2E8F0"
              strokeWidth="1.5"
            />
            {/* Inner purple scrub neckline */}
            <path
              d="M80 100 L90 116 L100 100 Z"
              fill="#8B5CF6"
            />
            {/* Stethoscope around neck */}
            <path
              d="M74 100 C74 120 82 126 90 126 C98 126 106 120 106 100"
              stroke="#64748B"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
            <circle cx="90" cy="128" r="3.5" fill="#475569" />

            {/* Neck */}
            <rect x="83" y="80" width="14" height="22" rx="4" fill="#FED7AA" />

            {/* Face */}
            <ellipse cx="90" cy="68" rx="15" ry="18" fill="#FED7AA" />

            {/* Dark Hair tied in a neat professional bun with loose side strands */}
            <path
              d="M72 60 C72 40 82 32 90 32 C98 32 108 40 108 60 C108 72 106 82 104 88 C100 88 100 78 100 72 C100 56 96 46 90 46 C84 46 80 56 80 72 C80 78 80 88 76 88 C74 82 72 72 72 60 Z"
              fill="#1E2433"
            />
            {/* Hair Bun */}
            <circle cx="90" cy="26" r="11" fill="#1E2433" />
            <ellipse cx="90" cy="24" rx="8" ry="6" fill="#2E384D" />

            {/* Friendly eyes and smile */}
            <circle cx="85" cy="67" r="1.5" fill="#334155" />
            <circle cx="95" cy="67" r="1.5" fill="#334155" />
            <path
              d="M87 74 Q90 77 93 74"
              stroke="#EA580C"
              strokeWidth="1.4"
              strokeLinecap="round"
              fill="none"
            />

            {/* Counsellor holding a digital counselling tablet in her hands */}
            <rect
              x="62"
              y="112"
              width="36"
              height="26"
              rx="4"
              transform="rotate(-8 62 112)"
              fill="#1E293B"
            />
            <rect
              x="64"
              y="114"
              width="32"
              height="22"
              rx="2.5"
              transform="rotate(-8 64 114)"
              fill="#EDE9FE"
            />
            {/* Hands holding tablet */}
            <circle cx="62" cy="126" r="4.5" fill="#FED7AA" />
            <circle cx="95" cy="122" r="4.5" fill="#FED7AA" />
          </svg>
        </div>
      </div>

      {/* Right Motivational Quote Card */}
      <div className="w-full lg:w-72 shrink-0 rounded-3xl bg-gradient-to-br from-[#F5F0FE] via-[#FAF7FE] to-[#F1EAFA] p-5 sm:p-6 border border-purple-100/80 shadow-2xs flex flex-col justify-between relative overflow-hidden">
        {/* Soft background wavy watermark SVG */}
        <div className="absolute right-0 bottom-0 pointer-events-none opacity-40">
          <svg viewBox="0 0 160 80" className="w-40 h-20 text-[#DDD6FE]" fill="none">
            <path
              d="M0 60 C40 30 90 70 160 40 L160 80 L0 80 Z"
              fill="currentColor"
            />
          </svg>
        </div>

        <div className="relative z-10">
          <h3 className="text-sm sm:text-[15px] font-bold text-[#1E2433] leading-snug">
            A calmer, healthier campus starts with you.{' '}
            <span className="inline-block">💜</span>
          </h3>
        </div>

        <div className="relative z-10 mt-3 flex items-center gap-1.5 text-[11px] font-semibold text-[#7C3AED]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#7C3AED]" />
          <span>Active Operations Today</span>
        </div>
      </div>
    </div>
  )
}

