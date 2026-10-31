import React, { useState } from 'react'
import { FocusAreaSegment } from './counsellorDemoData'

interface CasesByFocusAreaProps {
  totalCases?: number
  segments?: FocusAreaSegment[]
}

const DEFAULT_SEGMENTS: FocusAreaSegment[] = [
  { name: 'Academic Stress', percentage: 33, color: '#8B5CF6' },
  { name: 'Emotional Wellbeing', percentage: 25, color: '#FBBF24' },
  { name: 'Adjustment & Belonging', percentage: 17, color: '#10B981' },
  { name: 'Personal Concerns', percentage: 17, color: '#F43F5E' },
  { name: 'Other', percentage: 8, color: '#94A3B8' },
]

export function CasesByFocusArea({
  totalCases = 12,
  segments = DEFAULT_SEGMENTS,
}: CasesByFocusAreaProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  // Donut SVG parameters
  const size = 130
  const strokeWidth = 16
  const radius = (size - strokeWidth) / 2
  const center = size / 2
  const circumference = 2 * Math.PI * radius

  // Calculate accumulated offsets
  let accumulatedPercent = 0
  const computedSegments = segments.map((seg, idx) => {
    const strokeDasharray = `${(seg.percentage / 100) * circumference} ${circumference}`
    const strokeDashoffset = -((accumulatedPercent / 100) * circumference)
    accumulatedPercent += seg.percentage
    return {
      ...seg,
      strokeDasharray,
      strokeDashoffset,
      idx,
    }
  })

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col justify-between font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold text-[#1E2433]">Cases by Focus Area</h3>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 my-1">
        {/* Donut Chart with Center Text */}
        <div className="relative w-[130px] h-[130px] shrink-0 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
            {/* Background track circle */}
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="#F1F5F9"
              strokeWidth={strokeWidth}
            />

            {/* Segments */}
            {computedSegments.map((seg) => (
              <circle
                key={seg.idx}
                cx={center}
                cy={center}
                r={radius}
                fill="none"
                stroke={seg.color}
                strokeWidth={hoveredIdx === seg.idx ? strokeWidth + 3 : strokeWidth}
                strokeDasharray={seg.strokeDasharray}
                strokeDashoffset={seg.strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-300 cursor-pointer"
                onMouseEnter={() => setHoveredIdx(seg.idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            ))}
          </svg>

          {/* Center text: "12 \n Active Cases" */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
            <span className="text-xl font-extrabold text-[#1E2433] leading-none">
              {hoveredIdx !== null ? `${segments[hoveredIdx].percentage}%` : totalCases}
            </span>
            <span className="text-[10px] font-bold text-[#717E95] mt-0.5 leading-tight">
              {hoveredIdx !== null ? segments[hoveredIdx].name.split(' ')[0] : 'Active Cases'}
            </span>
          </div>
        </div>

        {/* Legend with percentages matching reference */}
        <div className="flex-1 min-w-0 flex flex-col gap-1.5 w-full">
          {segments.map((seg, idx) => (
            <div
              key={idx}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              className={`flex items-center justify-between px-2 py-1 rounded-lg transition cursor-pointer text-xs ${
                hoveredIdx === idx ? 'bg-gray-50' : ''
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: seg.color }}
                />
                <span className="truncate text-[11px] font-medium text-[#475569]">
                  {seg.name}
                </span>
              </div>
              <span className="text-[11px] font-bold text-[#1E2433] ml-2 shrink-0">
                {seg.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

