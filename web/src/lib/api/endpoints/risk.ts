import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import type { Tier } from '../../../components/common/ui'
import { studentName } from '../../labels'

/** Rolling risk model reads (api/app/modules/ml). Shapes follow docs/architecture/INSIGHTS_SPEC.md. */
export interface Reason {
  text: string
  group: string
  effect_pts?: number | null
  values?: Record<string, number>
}
export interface ScoreRow {
  id: string
  student_ref: string
  student_id: string | null
  external_student_ref_hash?: string
  course_id: string
  term_id: string
  as_of_day: number
  probability: number
  tier: Tier
  signal: boolean
  previous_tier: Tier | null
  previous_probability: number | null
  direction: 'up' | 'down' | 'steady' | string | null
  reasons: Reason[]
  model_version?: string
}
export interface Insight {
  risk: { tier: Tier; probability: number; previous_tier: Tier | null; previous_probability: number | null; direction: string | null; delta: number | null; previous_day: number | null }
  history: { day: number; tier: Tier; probability: number }[]
  reasons: Reason[]
  course_id: string
  term_id: string
  as_of_day: number
  last_assessment?: string | null
  next_check?: { day: number | null; assessment_id: string | null }
}
export interface InsightResponse {
  student_id: string
  student_ref: string
  items: { score: ScoreRow; insight: Insight }[]
}
export interface CohortInsight {
  course_id: string
  term_id: string
  n_enrolled: number
  n_active: number
  mean_risk: number
  at_risk_share: number
  tier_distribution: Record<string, { n: number | null; share: number | null }>
  time_to_risk?: { day: number; cumulative_signalled_share: number; signalled_share: number }[]
  hotspot?: { label: string; due_day: number; n_students: number | null; share_of_at_risk: number | null } | null
  hotspot_breakdown?: { label: string; due_day: number; n_students: number | null }[]
}
export interface DriftFeature {
  feature: string
  psi: number
  status: 'ok' | 'watch' | 'shift' | string
}

async function fetchAllScores(signal?: AbortSignal): Promise<{ run_id: string; as_of_day: number; items: ScoreRow[] }> {
  const first = await api.get<{ run_id: string; as_of_day: number; items: ScoreRow[]; total_pages: number }>('/api/v1/ml/students', {
    query: { page: 1, page_size: 100 },
    signal,
  })
  let items = first.items
  const pages = Math.min(first.total_pages ?? 1, 20)
  if (pages > 1) {
    const rest = await Promise.all(
      Array.from({ length: pages - 1 }, (_, i) =>
        api.get<{ items: ScoreRow[] }>('/api/v1/ml/students', { query: { page: i + 2, page_size: 100 }, signal }),
      ),
    )
    items = items.concat(...rest.map((r) => r.items))
  }
  return { run_id: first.run_id, as_of_day: first.as_of_day, items }
}

/** Every scored enrolment of the latest run (highest risk first). */
export const useAllScores = () =>
  useQuery({ queryKey: ['ml', 'all-scores'], queryFn: ({ signal }) => fetchAllScores(signal), staleTime: 60_000, retry: false })

export const useStudentInsight = (key: string | null) =>
  useQuery({
    queryKey: ['ml', 'insight', key],
    queryFn: ({ signal }) => api.get<InsightResponse>(`/api/v1/ml/students/${key}/insight`, { signal }),
    enabled: Boolean(key),
    retry: false,
  })

export interface CaseLite {
  id: string
  student_id: string
  student_name?: string | null
  student_ref?: string | null
  department?: string | null
  state: string
  priority: string
  owner_name?: string | null
  is_overdue: boolean
  due_at?: string | null
  created_at: string
}

/** All cases visible to the caller (pages of 100). Also the only roster-with-names source an admin has. */
export const useAllCases = () =>
  useQuery({
    queryKey: ['cases', 'all-lite'],
    staleTime: 30_000,
    queryFn: async ({ signal }) => {
      const out: CaseLite[] = []
      for (let offset = 0; offset < 1000; offset += 100) {
        const page = await api.get<CaseLite[]>('/api/v1/cases/', { query: { limit: 100, offset }, signal })
        out.push(...page)
        if (page.length < 100) break
      }
      return out
    },
  })

export interface PersonInfo {
  name: string | null
  department: string | null
}
/** student_id and student_ref to display info. Names exist only for students that have a case. */
export function buildPeopleIndex(cases: CaseLite[] | undefined): Map<string, PersonInfo> {
  const m = new Map<string, PersonInfo>()
  for (const c of cases ?? []) {
    const info = { name: c.student_name ?? null, department: c.department ?? null }
    m.set(c.student_id, info)
    if (c.student_ref) m.set(c.student_ref, info)
  }
  return m
}
/** The real name if we have one, otherwise null. */
export function knownName(people: Map<string, PersonInfo>, row: { student_id?: string | null; student_ref: string }): string | null {
  return people.get(row.student_id ?? '')?.name ?? people.get(row.student_ref)?.name ?? null
}
export function displayName(people: Map<string, PersonInfo>, row: { student_id?: string | null; student_ref: string }): string {
  return studentName(people.get(row.student_id ?? '')?.name ?? people.get(row.student_ref)?.name, row.student_ref)
}
