import React, { useEffect } from 'react'
import { ArrowDownRight, ArrowUpRight, Info, Minus, X } from 'lucide-react'
import { useT } from '../../i18n'

/* ------------------------------------------------------------------ tokens */
export type Tier = 'HIGH' | 'MEDIUM' | 'WATCH' | 'ON_TRACK'
export const TIERS: Tier[] = ['HIGH', 'MEDIUM', 'WATCH', 'ON_TRACK']
export const TIER_STYLE: Record<Tier, { label: string; color: string; bar: string; chip: string; help: string }> = {
  HIGH: { label: 'High', color: '#B3261E', bar: 'bg-tier-high', chip: 'bg-rose-50 text-rose-700 border-rose-200', help: 'Very likely to fail or withdraw without support' },
  MEDIUM: { label: 'Medium', color: '#D2691E', bar: 'bg-tier-medium', chip: 'bg-orange-50 text-orange-700 border-orange-200', help: 'Clear warning signs' },
  WATCH: { label: 'Watch', color: '#C79A14', bar: 'bg-tier-watch', chip: 'bg-amber-50 text-amber-700 border-amber-200', help: 'Early signs worth keeping an eye on' },
  ON_TRACK: { label: 'On track', color: '#2C7A66', bar: 'bg-tier-ok', chip: 'bg-emerald-50 text-emerald-700 border-emerald-200', help: 'No concerns right now' },
}

export const pretty = (s: string) => s.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
export const pct = (n: number | null | undefined, digits = 0) =>
  n == null || Number.isNaN(n) ? '—' : `${(n * 100).toFixed(digits)}%`
export const fmtCount = (n: number | null | undefined, suppressed?: boolean) => (suppressed ? '<5' : n == null ? '—' : String(n))
export const fmtDate = (s?: string | null) => (s ? new Date(s).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : '—')
export const fmtDateTime = (s?: string | null) =>
  s ? new Date(s).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'

/* ------------------------------------------------------------------ tooltip */
export function InfoTip({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span className={`group/tip relative inline-flex align-middle ${className}`}>
      <button type="button" aria-label={text} className="rounded-full text-muted hover:text-ink focus:text-ink focus:outline-none">
        <Info className="h-3.5 w-3.5" />
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-30 mt-1.5 hidden w-56 -translate-x-1/2 rounded-xl bg-ink px-3 py-2 text-left text-[11px] font-medium normal-case leading-snug tracking-normal text-white shadow-lg group-hover/tip:block group-focus-within/tip:block"
      >
        {text}
      </span>
    </span>
  )
}

/* ------------------------------------------------------------------ cards */
export function Card({
  title,
  tip,
  action,
  children,
  className = '',
}: {
  title?: string
  tip?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  const t = useT()
  return (
    <section className={`rounded-lg border border-line bg-panel p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="flex items-center gap-1.5 text-[13px] font-semibold text-ink">
            {title ? t(title) : null}
            {tip && <InfoTip text={tip} />}
          </h3>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function Kpi({
  label,
  value,
  hint,
  tip,
  tone = 'text-ink',
  onClick,
}: {
  label: string
  value: React.ReactNode
  hint?: string
  tip?: string
  tone?: string
  onClick?: () => void
}) {
  const t = useT()
  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={onClick ? (e) => (e.key === 'Enter' || e.key === ' ') && onClick() : undefined}
      className={`bg-panel p-4 text-left ${onClick ? 'cursor-pointer transition hover:bg-sunken/60' : ''}`}
    >
      <div className={`font-display text-[40px] leading-none tracking-tight tabular-nums ${tone}`}>{value}</div>
      <div className="mt-2 flex items-center gap-1 text-[13px] font-semibold text-ink">
        {t(label)}
        {tip && <InfoTip text={tip} />}
      </div>
      {hint && <div className="text-[11px] text-muted">{hint}</div>}
    </div>
  )
}

export function TierBadge({ tier }: { tier: string | null | undefined }) {
  const t = useT()
  const s = tier ? TIER_STYLE[tier as Tier] : undefined
  if (!s) return <span className="text-[11px] text-muted">—</span>
  return <span className={`inline-flex rounded border px-1.5 py-0.5 text-[10px] font-semibold ${s.chip}`}>{t(s.label)}</span>
}

export function Pill({ children, tone = 'bg-gray-100 text-gray-700' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold ${tone}`}>{children}</span>
}

export function Direction({ d }: { d?: string | null }) {
  if (d === 'up') return <ArrowUpRight className="h-3.5 w-3.5 text-rose-600" aria-label="risk rising" />
  if (d === 'down') return <ArrowDownRight className="h-3.5 w-3.5 text-emerald-600" aria-label="risk falling" />
  return <Minus className="h-3.5 w-3.5 text-muted" aria-label="steady" />
}

export function PageIntro({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-muted">{children}</p>
}

export function Button({
  children,
  onClick,
  disabled,
  variant = 'primary',
  type = 'button',
  className = '',
}: {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'ghost' | 'danger'
  type?: 'button' | 'submit'
  className?: string
}) {
  const t = useT()
  const v =
    variant === 'primary'
      ? 'bg-ink text-white hover:bg-ink-2'
      : variant === 'danger'
        ? 'bg-rose-600 text-white hover:bg-rose-700'
        : 'border border-line bg-panel text-ink hover:bg-sunken'
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-1.5 rounded-md px-4 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${v} ${className}`}
    >
      {typeof children === 'string' ? t(children) : children}
    </button>
  )
}

export function SearchInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      aria-label={placeholder}
      className="w-full max-w-xs rounded-md border border-line bg-panel px-3.5 py-2 text-xs outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
    />
  )
}

export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: { id: T; label: string }[] }) {
  const t = useT()
  return (
    <div role="tablist" className="inline-flex flex-wrap gap-0.5 rounded-md bg-sunken p-1 text-xs">
      {items.map((i) => (
        <button
          key={i.id}
          role="tab"
          aria-selected={value === i.id}
          type="button"
          onClick={() => onChange(i.id)}
          className={`rounded px-3.5 py-1.5 font-semibold transition ${value === i.id ? 'bg-panel text-ink shadow-sm' : 'text-muted hover:text-ink'}`}
        >
          {t(i.label)}
        </button>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ drawer */
export function Drawer({ open, onClose, title, subtitle, children }: { open: boolean; onClose: () => void; title: string; subtitle?: string; children: React.ReactNode }) {
  useEffect(() => {
    if (!open) return
    const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-ink/40" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-lg flex-col overflow-y-auto bg-paper p-5 shadow-2xl font-sans">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-ink">{title}</h2>
            {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-full p-1.5 text-gray-500 hover:bg-black/5">
            <X className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ charts */
export interface Bucket {
  label: string
  count: number | null
  suppressed?: boolean
}

export function Bars({ rows, color = 'bg-indigo-500', labelWidth = 'w-24', showEmpty = false }: { rows: Bucket[]; color?: string; labelWidth?: string; showEmpty?: boolean }) {
  const visible = rows.filter((r) => showEmpty || r.suppressed || (r.count ?? 0) > 0)
  const max = Math.max(1, ...visible.map((r) => r.count ?? 0))
  if (!visible.length) return <p className="text-xs text-muted">Nothing to show yet.</p>
  return (
    <ul className="space-y-2">
      {visible.map((r) => (
        <li key={r.label} className="flex items-center gap-3 text-xs">
          <span className={`${labelWidth} shrink-0 truncate text-ink-2`} title={pretty(r.label)}>{pretty(r.label)}</span>
          <div className="h-2.5 min-w-10 flex-1 rounded-full bg-sunken">
            <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${r.suppressed ? 8 : ((r.count ?? 0) / max) * 100}%` }} />
          </div>
          <span className="w-8 text-right font-semibold tabular-nums">{fmtCount(r.count, r.suppressed)}</span>
        </li>
      ))}
    </ul>
  )
}

export function TierBar({ counts, height = 'h-4' }: { counts: Partial<Record<string, number>>; height?: string }) {
  const total = TIERS.reduce((a, t) => a + (counts[t] ?? 0), 0)
  return (
    <div className={`flex w-full overflow-hidden rounded-full bg-sunken ${height}`} role="img" aria-label="Risk tier split">
      {TIERS.map((t) => (
        <div key={t} className={TIER_STYLE[t].bar} style={{ width: `${((counts[t] ?? 0) / Math.max(1, total)) * 100}%` }} title={`${TIER_STYLE[t].label}: ${counts[t] ?? 0}`} />
      ))}
    </div>
  )
}

export function TierLegend({ counts }: { counts: Partial<Record<string, number>> }) {
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      {TIERS.map((t) => (
        <span key={t} className={`rounded border px-2.5 py-1 font-semibold ${TIER_STYLE[t].chip}`}>
          {TIER_STYLE[t].label} {counts[t] ?? 0}
        </span>
      ))}
    </div>
  )
}

/** Donut of tier counts. */
export function Donut({ counts, centre, sub }: { counts: Partial<Record<string, number>>; centre: string; sub: string }) {
  const total = Math.max(1, TIERS.reduce((a, t) => a + (counts[t] ?? 0), 0))
  const r = 52
  const c = 2 * Math.PI * r
  let offset = 0
  return (
    <svg viewBox="0 0 140 140" className="h-40 w-40 shrink-0" role="img" aria-label="Risk tier distribution">
      <circle cx="70" cy="70" r={r} fill="none" stroke="#ECE9E0" strokeWidth="16" />
      {TIERS.map((t) => {
        const len = ((counts[t] ?? 0) / total) * c
        const el = (
          <circle key={t} cx="70" cy="70" r={r} fill="none" stroke={TIER_STYLE[t].color} strokeWidth="16" strokeDasharray={`${len} ${c - len}`} strokeDashoffset={-offset} transform="rotate(-90 70 70)">
            <title>{`${TIER_STYLE[t].label}: ${counts[t] ?? 0}`}</title>
          </circle>
        )
        offset += len
        return el
      })}
      <text x="70" y="68" textAnchor="middle" className="fill-ink" fontSize="22" fontWeight="800">{centre}</text>
      <text x="70" y="84" textAnchor="middle" className="fill-muted" fontSize="9" fontWeight="600">{sub}</text>
    </svg>
  )
}

/** Stacked columns of tier counts per scoring run (oldest to newest). */
export function TierTrend({ points }: { points: { label: string; counts: Partial<Record<string, number>> }[] }) {
  const W = 360
  const H = 170
  const pad = { l: 8, r: 8, t: 10, b: 26 }
  const max = Math.max(1, ...points.map((p) => TIERS.reduce((a, t) => a + (p.counts[t] ?? 0), 0)))
  const bw = Math.min(70, (W - pad.l - pad.r) / Math.max(1, points.length) - 16)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Risk tiers across scoring runs">
      {points.map((p, i) => {
        const x = pad.l + ((W - pad.l - pad.r) / points.length) * (i + 0.5) - bw / 2
        let y = H - pad.b
        return (
          <g key={p.label}>
            {[...TIERS].reverse().map((t) => {
              const v = p.counts[t] ?? 0
              const h = (v / max) * (H - pad.t - pad.b)
              y -= h
              return (
                <rect key={t} x={x} y={y} width={bw} height={Math.max(0, h)} fill={TIER_STYLE[t].color} rx={i === points.length ? 0 : 2}>
                  <title>{`${p.label} · ${TIER_STYLE[t].label}: ${v}`}</title>
                </rect>
              )
            })}
            <text x={x + bw / 2} y={H - 8} textAnchor="middle" fontSize="10" className="fill-muted" fontWeight="600">{p.label}</text>
          </g>
        )
      })}
    </svg>
  )
}

/** Simple multi-point line (values 0..1 or any numbers). */
export function LineChart({ points, color = '#6366F1', yFmt = (v: number) => `${Math.round(v * 100)}%`, xLabel, yMax }: { points: { x: number; y: number }[]; color?: string; yFmt?: (v: number) => string; xLabel?: string; yMax?: number }) {
  const W = 360
  const H = 160
  const pad = { l: 34, r: 24, t: 10, b: 24 }
  if (points.length < 2) return <p className="text-xs text-muted">Not enough data yet.</p>
  const xs = points.map((p) => p.x)
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs)
  const ymax = yMax ?? Math.max(0.01, ...points.map((p) => p.y))
  const sx = (x: number) => pad.l + ((x - x0) / Math.max(1, x1 - x0)) * (W - pad.l - pad.r)
  const sy = (y: number) => H - pad.b - (y / ymax) * (H - pad.t - pad.b)
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Line chart">
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line x1={pad.l} x2={W - pad.r} y1={sy(ymax * f)} y2={sy(ymax * f)} stroke="#DEDACE" strokeDasharray="3 3" />
          <text x={pad.l - 4} y={sy(ymax * f) + 3} textAnchor="end" fontSize="9" className="fill-muted">{yFmt(ymax * f)}</text>
        </g>
      ))}
      <path d={`${d} L${sx(x1)},${H - pad.b} L${sx(x0)},${H - pad.b} Z`} fill={color} opacity="0.1" />
      <path d={d} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" />
      {points.map((p) => (
        <circle key={p.x} cx={sx(p.x)} cy={sy(p.y)} r="3" fill={color}>
          <title>{`Day ${p.x}: ${yFmt(p.y)}`}</title>
        </circle>
      ))}
      <text x={pad.l} y={H - 6} fontSize="9" className="fill-muted">day {x0}</text>
      <text x={W - pad.r} y={H - 6} textAnchor="end" fontSize="9" className="fill-muted">{xLabel ?? `day ${x1}`}</text>
    </svg>
  )
}

export function DetailsDisclosure({ summary, children }: { summary: string; children: React.ReactNode }) {
  return (
    <details className="group rounded-xl border border-line bg-sunken/50 px-3 py-2 text-[11px] text-ink-2">
      <summary className="cursor-pointer select-none font-semibold text-muted">{summary}</summary>
      <div className="mt-2 space-y-1 font-mono break-all">{children}</div>
    </details>
  )
}

export function ColorLegend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-2">
      {TIERS.map((t) => (
        <span key={t} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: TIER_STYLE[t].color }} />{TIER_STYLE[t].label}</span>
      ))}
    </div>
  )
}

/** A row of KPIs sharing one hairline-divided panel (reads as an instrument strip, not a card grid). */
export function KpiStrip({ children, cols = 'lg:grid-cols-5', className = '' }: { children: React.ReactNode; cols?: string; className?: string }) {
  return <div className={`grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line ${cols} ${className}`}>{children}</div>
}
