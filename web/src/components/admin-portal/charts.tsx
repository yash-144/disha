import React from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, Line, LineChart, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TIERS, TIER_STYLE, pct, type Tier } from '../common/ui'

const AXIS = { fontSize: 13, fill: '#4A5160' }
const GRID = '#E7E3D8'

function Tip({ children }: { children: React.ReactNode }) {
  return <div className="rounded-md border border-line bg-panel px-3 py-2 text-xs shadow-lg">{children}</div>
}

/** Stacked bars: how many student-courses sat in each tier at every scoring run. */
export function TierRunsChart({ runs }: { runs: { label: string; counts: Partial<Record<string, number>> }[] }) {
  const data = runs.map((r) => ({ label: r.label, ...Object.fromEntries(TIERS.map((t) => [t, r.counts[t] ?? 0])) }))
  return (
    <div>
      <div className="h-[300px]">
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 8 }} barCategoryGap="22%">
            <CartesianGrid vertical={false} stroke={GRID} />
            <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
            <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} label={{ value: 'Student-courses', angle: -90, position: 'insideLeft', style: { ...AXIS, textAnchor: 'middle' }, offset: 8 }} />
            <Tooltip
              cursor={{ fill: 'rgba(20,24,31,0.04)' }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <Tip>
                    <p className="mb-1 font-semibold">{label}</p>
                    {[...payload].reverse().map((p) => (
                      <p key={String(p.dataKey)} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: p.color }} />{TIER_STYLE[p.dataKey as Tier].label}: <b>{p.value}</b></p>
                    ))}
                  </Tip>
                ) : null
              }
            />
            {[...TIERS].reverse().map((t) => (
              <Bar key={t} dataKey={t} stackId="s" fill={TIER_STYLE[t].color} stroke="#FCFBF8" strokeWidth={2} isAnimationActive={false}>
                <LabelList dataKey={t} position="center" formatter={(v: number) => (v >= 20 ? v : '')} style={{ fill: '#fff', fontSize: 13, fontWeight: 700 }} />
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

/** Ranked horizontal bars, % labelled at the end of each bar. */
export function RankedBars({ rows, color = '#B3261E', valueLabel = 'of students at High or Medium risk' }: { rows: { label: string; value: number; sub?: string }[]; color?: string; valueLabel?: string }) {
  const max = Math.max(0.01, ...rows.map((r) => r.value))
  return (
    <div style={{ height: Math.max(180, rows.length * 38 + 40) }}>
      <ResponsiveContainer>
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 52, left: 4, bottom: 24 }} barCategoryGap="28%">
          <CartesianGrid horizontal={false} stroke={GRID} />
          <XAxis type="number" domain={[0, Math.ceil(max * 12) / 10 > 1 ? 1 : Math.ceil(max * 12) / 10]} tickFormatter={(v) => pct(v)} tick={AXIS} tickLine={false} axisLine={false} label={{ value: 'Share of students at High or Medium risk', position: 'insideBottom', offset: -14, style: { ...AXIS, textAnchor: 'middle' } }} />
          <YAxis type="category" dataKey="label" tick={{ ...AXIS, fontWeight: 600, fill: '#14181F' }} tickLine={false} axisLine={false} width={64} />
          <Tooltip cursor={{ fill: 'rgba(20,24,31,0.04)' }} content={({ active, payload }) => active && payload?.length ? <Tip><p className="font-semibold">{payload[0].payload.label}</p><p>{pct(payload[0].payload.value)} {valueLabel}</p>{payload[0].payload.sub && <p className="text-muted">{payload[0].payload.sub}</p>}</Tip> : null} />
          <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} isAnimationActive={false}>
            <LabelList dataKey="value" position="right" formatter={(v: number) => pct(v)} style={{ fill: '#14181F', fontSize: 13, fontWeight: 700 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Cumulative flagged line with labelled points. */
export function FlaggedLine({ points }: { points: { day: number; flagged_students: number }[] }) {
  const data = points.map((p) => ({ day: p.day, n: p.flagged_students }))
  const last = data[data.length - 1]
  return (
    <div className="h-[260px]">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 22, right: 28, left: 4, bottom: 24 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis dataKey="day" type="number" domain={['dataMin - 4', 'dataMax + 4']} ticks={data.map((d) => d.day)} tickFormatter={(v) => `Day ${v}`} tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} label={{ value: 'Weekly scoring run (day of term)', position: 'insideBottom', offset: -14, style: { ...AXIS, textAnchor: 'middle' } }} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} domain={[0, 'dataMax + 20']} label={{ value: 'Flagged so far', angle: -90, position: 'insideLeft', style: { ...AXIS, textAnchor: 'middle' }, offset: 6 }} />
          <Tooltip content={({ active, payload }) => active && payload?.length ? <Tip><p className="font-semibold">Day {payload[0].payload.day}</p><p><b>{payload[0].payload.n}</b> student-courses flagged so far</p></Tip> : null} />
          <Line type="stepAfter" dataKey="n" stroke="#1F54D6" strokeWidth={3} dot={{ r: 5, fill: '#1F54D6', stroke: '#FCFBF8', strokeWidth: 2 }} isAnimationActive={false}>
            <LabelList dataKey="n" position="top" offset={10} style={{ fill: '#14181F', fontSize: 13, fontWeight: 700 }} />
          </Line>
          {last && <ReferenceDot x={last.day} y={last.n} r={0} />}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Tiny trend line for KPI cards. Last point is emphasised. */
export function Sparkline({ values, color = '#1F54D6' }: { values: number[]; color?: string }) {
  if (values.length < 2) return null
  const W = 92
  const H = 30
  const min = Math.min(...values)
  const max = Math.max(...values)
  const sx = (i: number) => 3 + (i / (values.length - 1)) * (W - 6)
  const sy = (v: number) => H - 4 - ((v - min) / Math.max(1e-9, max - min)) * (H - 8)
  const d = values.map((v, i) => `${i ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} aria-hidden="true">
      <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={sx(values.length - 1)} cy={sy(values[values.length - 1])} r="3" fill={color} />
    </svg>
  )
}

/** Big donut with the total in the centre and every segment labelled (count and share). */
export function TierDonut({ counts, unit = 'student-courses' }: { counts: Partial<Record<string, number>>; unit?: string }) {
  const total = Math.max(1, TIERS.reduce((a, t) => a + (counts[t] ?? 0), 0))
  const r = 74
  const c = 2 * Math.PI * r
  let offset = 0
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
      <svg viewBox="0 0 200 200" className="h-52 w-52 shrink-0" role="img" aria-label={`Risk tiers across ${total} ${unit}`}>
        <circle cx="100" cy="100" r={r} fill="none" stroke="#ECE9E0" strokeWidth="26" />
        {TIERS.map((t) => {
          const len = ((counts[t] ?? 0) / total) * c
          const el = (
            <circle key={t} cx="100" cy="100" r={r} fill="none" stroke={TIER_STYLE[t].color} strokeWidth="26" strokeDasharray={`${Math.max(0, len - 2)} ${c - Math.max(0, len - 2)}`} strokeDashoffset={-offset} transform="rotate(-90 100 100)">
              <title>{`${TIER_STYLE[t].label}: ${counts[t] ?? 0} (${pct((counts[t] ?? 0) / total)})`}</title>
            </circle>
          )
          offset += len
          return el
        })}
        <text x="100" y="98" textAnchor="middle" fontSize="38" fontWeight="800" fill="#14181F">{total}</text>
        <text x="100" y="120" textAnchor="middle" fontSize="13" fill="#4A5160">{unit}</text>
      </svg>
      <ul className="w-full min-w-[170px] space-y-3">
        {TIERS.map((t) => (
          <li key={t} className="flex items-center justify-between gap-4 text-sm">
            <span className="flex items-center gap-2.5 font-semibold text-ink"><span className="h-3.5 w-3.5 rounded-sm" style={{ background: TIER_STYLE[t].color }} />{TIER_STYLE[t].label}</span>
            <span className="tabular-nums"><b className="text-base">{counts[t] ?? 0}</b> <span className="text-muted">· {pct((counts[t] ?? 0) / total)}</span></span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function Takeaway({ children }: { children: React.ReactNode }) {
  return <p className="mt-3 border-t border-line pt-3 text-sm text-ink-2">{children}</p>
}
