import React from 'react'
import { QueryState } from '../common/QueryState'
import { Drawer, LineChart, TierBadge, Direction, InfoTip, pct, TIER_STYLE } from '../common/ui'
import { useStudentInsight } from '../../lib/api/endpoints/risk'
import { courseName, inTen, movement, reasonGroupLabel, termWeek, tierLabel } from '../../lib/labels'


/** Per-student model view: tier, risk history and the plain-language reasons with their effect sizes. */
export function StudentInsightDrawer({ studentKey, name, onClose }: { studentKey: string | null; name?: string; onClose: () => void }) {
  const q = useStudentInsight(studentKey)
  return (
    <Drawer open={Boolean(studentKey)} onClose={onClose} title={name || 'Student'} subtitle="Why this student was flagged, course by course">
      <QueryState query={q} isEmpty={(d) => !d.items?.length}>
        {(d) => (
          <div className="space-y-4">
            {d.items.map(({ score, insight }) => {
              const maxEffect = Math.max(1, ...insight.reasons.map((r) => Math.abs(r.effect_pts ?? 0)))
              return (
                <section key={score.course_id} className="rounded-2xl border border-line bg-white p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-bold text-ink">{courseName(score.course_id)}</p>
                      <p className="text-xs text-muted">{termWeek(insight.as_of_day)}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <TierBadge tier={insight.risk.tier} /> <Direction d={insight.risk.direction} />
                      </div>
                      <p className="mt-1 text-lg font-semibold tabular-nums" style={{ color: TIER_STYLE[insight.risk.tier]?.color }}>
                        {inTen(insight.risk.probability)}
                      </p>
                      <p className="text-xs text-muted">chance of struggling · {movement(insight.risk.direction).toLowerCase()}</p>
                    </div>
                  </div>
                  {insight.risk.previous_tier && insight.risk.previous_tier !== insight.risk.tier && (
                    <p className="mt-2 text-xs text-ink-2">
                      Moved from <b>{tierLabel(insight.risk.previous_tier)}</b> to <b>{tierLabel(insight.risk.tier)}</b> since last week.
                    </p>
                  )}
                  <div className="mt-3">
                    <p className="mb-1 flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-muted">
                      How things changed over the term <InfoTip text="Each point is a weekly check. Higher means more likely to struggle." />
                    </p>
                    <LineChart points={insight.history.map((h) => ({ x: h.day, y: h.probability }))} color={TIER_STYLE[insight.risk.tier]?.color} yMax={1} />
                  </div>
                  <div className="mt-3">
                    <p className="mb-2 flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-muted">
                      Why flagged <InfoTip text="Longer bars mean that reason matters more." />
                    </p>
                    {insight.reasons.length === 0 ? (
                      <p className="text-xs text-muted">No concerns found for this course.</p>
                    ) : (
                      <ul className="space-y-2.5">
                        {insight.reasons.map((r, i) => (
                          <li key={i} className="text-xs">
                            <div className="flex items-start justify-between gap-2">
                              <span className="text-ink">{r.text}</span>
                              <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-ink-2">{reasonGroupLabel(r.group)}</span>
                            </div>
                            {r.effect_pts != null && (
                              <div className="mt-1 flex items-center gap-2">
                                <div className="h-1.5 flex-1 rounded-full bg-gray-100">
                                  <div className="h-1.5 rounded-full bg-indigo-500" style={{ width: `${(Math.abs(r.effect_pts) / maxEffect) * 100}%` }} />
                                </div>
                                <span className="w-16 text-right text-xs font-semibold text-ink-2">{Math.abs(r.effect_pts) >= maxEffect * 0.66 ? 'Big factor' : Math.abs(r.effect_pts) >= maxEffect * 0.33 ? 'Medium' : 'Small'}</span>
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </section>
              )
            })}
            <p className="text-xs text-muted">These flags help people decide. They are not decisions.</p>
          </div>
        )}
      </QueryState>
    </Drawer>
  )
}
