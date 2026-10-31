import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface CaseLoadTrendProps {
  dataPoints?: number[]
  weekLabels?: string[]
  maxY?: number
}

export function CaseLoadTrend({
  dataPoints = [8, 12, 11, 16],
  weekLabels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
  maxY = 20,
}: CaseLoadTrendProps) {
  const [selectedRange, setSelectedRange] = useState('Last 4 Weeks')
  const [activePoint, setActivePoint] = useState<number | null>(null)

  // Chart layout dimensions
  const width = 360
  const height = 140
  const xStart = 32
  const xEnd = width - 18
  const yTop = 18
  const yBottom = 118

  // Calculate (x, y) coordinates for data points
  const points = dataPoints.map((val, idx) => {
    const x = xStart + (idx / (dataPoints.length - 1)) * (xEnd - xStart)
    const ratio = Math.min(Math.max(val / maxY, 0), 1)
    const y = yBottom - ratio * (yBottom - yTop)
    return { x, y, val }
  })

  // Smooth bezier curve path
  const pathD = points.reduce((acc, point, i, arr) => {
    if (i === 0) return `M ${point.x} ${point.y}`
    const prev = arr[i - 1]
    const cp1x = prev.x + (point.x - prev.x) / 2
    const cp1y = prev.y
    const cp2x = prev.x + (point.x - prev.x) / 2
    const cp2y = point.y
    return `${acc} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${point.x} ${point.y}`
  }, '')

  // Area path for gradient fill
  const areaD = `${pathD} L ${points[points.length - 1].x} ${yBottom} L ${points[0].x} ${yBottom} Z`

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col justify-between font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold text-[#1E2433]">Case Load Trend</h3>

        <div className="relative">
          <button
            type="button"
            onClick={() =>
              setSelectedRange(selectedRange === 'Last 4 Weeks' ? 'Last 8 Weeks' : 'Last 4 Weeks')
            }
            className="flex items-center gap-1 text-xs font-semibold text-[#717E95] hover:text-[#1E2433] transition"
          >
            <span>{selectedRange}</span>
            <ChevronDown className="w-3 h-3 text-[#94A3B8]" />
          </button>
        </div>
      </div>

      {/* SVG Chart */}
      <div className="relative w-full h-[145px] my-1">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="purpleCaseTrendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Horizontal grid lines & Y-axis labels [20, 15, 10, 5, 0] */}
          {[20, 15, 10, 5, 0].map((tick) => {
            const y = yBottom - (tick / maxY) * (yBottom - yTop)
            return (
              <g key={tick}>
                <text
                  x="6"
                  y={y + 3.5}
                  className="fill-[#94A3B8] text-[9px] font-semibold"
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

          {/* Area gradient under the curve */}
          <path d={areaD} fill="url(#purpleCaseTrendGradient)" />

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
      <div className="flex items-center justify-between pl-7 pr-3 text-[11px] font-medium text-[#94A3B8]">
        {weekLabels.map((lbl, idx) => (
          <span key={idx}>{lbl}</span>
        ))}
      </div>
    </div>
  )
}

