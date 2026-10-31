import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface WellbeingTrendProps {
  trendData: number[] // values between 40 and 100 for 4 weeks
}

export function WellbeingTrend({ trendData = [75, 68, 80, 92] }: WellbeingTrendProps) {
  const [selectedRange, setSelectedRange] = useState('Last 4 Weeks')
  const [activePoint, setActivePoint] = useState<number | null>(null)

  // Chart coordinate mapping
  // Chart box: width 340, height 120
  // X bounds: padding left 35, padding right 20 -> usable width 285
  // Y bounds: 100 (top 15) to 40 (bottom 105) -> height 90
  const width = 340
  const height = 120
  const xStart = 35
  const xEnd = width - 20
  const yTop = 15
  const yBottom = 105
  const yRange = 60 // 100 - 40

  const points = trendData.map((val, idx) => {
    const x = xStart + (idx / (trendData.length - 1)) * (xEnd - xStart)
    const clampedVal = Math.max(40, Math.min(100, val))
    const y = yBottom - ((clampedVal - 40) / yRange) * (yBottom - yTop)
    return { x, y, val }
  })

  // Create smooth bezier curve path
  const pathD = points.reduce((acc, point, i, arr) => {
    if (i === 0) return `M ${point.x} ${point.y}`
    const prev = arr[i - 1]
    const cp1x = prev.x + (point.x - prev.x) / 2
    const cp1y = prev.y
    const cp2x = prev.x + (point.x - prev.x) / 2
    const cp2y = point.y
    return `${acc} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${point.x} ${point.y}`
  }, '')

  // Closed area path for gradient fill
  const areaD = `${pathD} L ${points[points.length - 1].x} ${yBottom} L ${points[0].x} ${yBottom} Z`

  return (
    <div className="bg-white rounded-2xl p-4.5 border border-gray-100/90 shadow-2xs flex flex-col justify-between">
      {/* Card Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-[#1E2433]">Your Wellbeing Trend</h3>
        <button
          type="button"
          onClick={() => setSelectedRange(selectedRange === 'Last 4 Weeks' ? 'Last 8 Weeks' : 'Last 4 Weeks')}
          className="flex items-center gap-1 text-xs font-semibold text-[#717E95] hover:text-[#1E2433] transition"
        >
          <span>{selectedRange}</span>
          <ChevronDown className="w-3 h-3 text-[#94A3B8]" />
        </button>
      </div>

      {/* SVG Chart */}
      <div className="relative w-full h-[130px]">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="purpleGradientArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Horizontal grid lines & Y-axis labels */}
          {[100, 80, 60, 40].map((tick) => {
            const y = yBottom - ((tick - 40) / yRange) * (yBottom - yTop)
            return (
              <g key={tick}>
                <text
                  x="5"
                  y={y + 3.5}
                  className="fill-[#94A3B8] text-[9px] font-medium"
                >
                  {tick}
                </text>
                <line
                  x1={xStart}
                  y1={y}
                  x2={xEnd}
                  y2={y}
                  stroke="#F1F5F9"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                />
              </g>
            )
          })}

          {/* Area gradient */}
          <path d={areaD} fill="url(#purpleGradientArea)" />

          {/* Smooth curved trend line */}
          <path
            d={pathD}
            fill="none"
            stroke="#8B5CF6"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points */}
          {points.map((pt, idx) => (
            <g
              key={idx}
              className="cursor-pointer"
              onMouseEnter={() => setActivePoint(idx)}
              onMouseLeave={() => setActivePoint(null)}
            >
              <circle
                cx={pt.x}
                cy={pt.y}
                r={activePoint === idx ? 6 : 4}
                className="fill-[#8B5CF6] stroke-white stroke-2 transition-all duration-150"
              />
              {activePoint === idx && (
                <g>
                  <rect
                    x={pt.x - 14}
                    y={pt.y - 24}
                    width="28"
                    height="18"
                    rx="4"
                    fill="#1E2433"
                  />
                  <text
                    x={pt.x}
                    y={pt.y - 12}
                    textAnchor="middle"
                    fill="#FFFFFF"
                    className="text-[10px] font-bold"
                  >
                    {pt.val}
                  </text>
                </g>
              )}
            </g>
          ))}
        </svg>
      </div>

      {/* X-axis labels */}
      <div className="flex items-center justify-between pl-7 pr-3 pt-1 text-[11px] font-medium text-[#94A3B8]">
        <span>Week 1</span>
        <span>Week 2</span>
        <span>Week 3</span>
        <span>Week 4</span>
      </div>
    </div>
  )
}

