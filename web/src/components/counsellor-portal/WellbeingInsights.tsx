import React from 'react'
import { BarChart3, TrendingUp } from 'lucide-react'

interface WellbeingInsightsProps {
  headline?: string
  delta?: string
  trendData?: number[]
}

export function WellbeingInsights({
  headline = 'Student engagement is up by 18% this month. 🎉',
  delta = '+18%',
  trendData = [12, 15, 14, 20, 22, 28, 32],
}: WellbeingInsightsProps) {
  // Sparkline coordinates
  const width = 120
  const height = 48
  const minVal = Math.min(...trendData)
  const maxVal = Math.max(...trendData)
  const valRange = maxVal - minVal || 1

  const points = trendData.map((val, idx) => {
    const x = (idx / (trendData.length - 1)) * (width - 10) + 5
    const y = height - 8 - ((val - minVal) / valRange) * (height - 16)
    return { x, y }
  })

  const pathD = points.reduce((acc, pt, i, arr) => {
    if (i === 0) return `M ${pt.x} ${pt.y}`
    const prev = arr[i - 1]
    const cpx = prev.x + (pt.x - prev.x) / 2
    return `${acc} C ${cpx} ${prev.y}, ${cpx} ${pt.y}, ${pt.x} ${pt.y}`
  }, '')

  const areaD = `${pathD} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`

  return (
    <div className="rounded-3xl bg-gradient-to-br from-[#F0FDF4] to-[#EAF8EE] p-5 border border-[#BBF7D0]/80 shadow-2xs flex flex-col justify-between font-sans select-none relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-emerald-100 text-[#16A34A] flex items-center justify-center">
            <BarChart3 className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-sm font-bold text-[#1E2433]">Wellbeing Insights</h3>
        </div>
      </div>

      <div className="mt-1">
        <p className="text-xs font-semibold text-[#1E2433] leading-relaxed">
          {headline}
        </p>
      </div>

      {/* Delta badge + Sparkline graph */}
      <div className="mt-3 flex items-end justify-between">
        <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white text-xs font-bold text-[#16A34A] border border-emerald-200 shadow-2xs">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>{delta}</span>
        </div>

        {/* Small smooth green sparkline */}
        <div className="w-28 h-12 relative overflow-visible">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="greenSparklineGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22C55E" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#22C55E" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path d={areaD} fill="url(#greenSparklineGradient)" />
            <path
              d={pathD}
              fill="none"
              stroke="#16A34A"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>
    </div>
  )
}

