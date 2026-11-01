import React from 'react'

/** Abstract risk-signal illustration: weekly risk bars climbing across tiers, one student flagged. */
export function SignalArt({ className = '' }: { className?: string }) {
  const weeks = [18, 24, 22, 31, 38, 46, 61, 78]
  const tier = (v: number) => (v >= 70 ? '#E0574D' : v >= 45 ? '#E58A4A' : v >= 28 ? '#D9B13A' : '#4FA58F')
  return (
    <svg viewBox="0 0 420 260" className={className} role="img" aria-label="Weekly risk rising until a student is flagged for support">
      {[50, 100, 150, 200].map((y) => <line key={y} x1="20" x2="400" y1={y} y2={y} stroke="#fff" strokeOpacity="0.1" />)}
      {weeks.map((v, i) => (
        <g key={i}>
          <rect x={34 + i * 46} y={220 - v * 2.3} width="28" height={v * 2.3} fill={tier(v)} />
          <text x={48 + i * 46} y="240" textAnchor="middle" fontSize="10" fill="#fff" fillOpacity="0.5">W{i + 4}</text>
        </g>
      ))}
      <path d="M48 181 L94 165 L140 169 L186 148 L232 133 L278 114 L324 80 L370 41" fill="none" stroke="#fff" strokeWidth="2" />
      <circle cx="370" cy="41" r="5" fill="#fff" />
      <g transform="translate(250 14)">
        <rect width="146" height="26" fill="#fff" />
        <rect width="4" height="26" fill="#E0574D" />
        <text x="14" y="17" fontSize="11" fontWeight="600" fill="#14181F">Flagged, case opened</text>
      </g>
    </svg>
  )
}
