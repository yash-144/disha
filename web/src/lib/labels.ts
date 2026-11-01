/**
 * ONE place that turns internal names (enum values, ids, codes, raw timestamps) into plain words.
 * Rule: backend names are for developers. Anything a person reads goes through here.
 */

/* ------------------------------------------------------------------ generic */
/** Last-resort fallback for an unknown code: "some_value" -> "Some value". */
export function humanize(s: string | null | undefined): string {
  if (!s) return ''
  const t = s.replace(/[_-]+/g, ' ').trim()
  return t.charAt(0).toUpperCase() + t.slice(1)
}

/* ------------------------------------------------------------------ risk levels */
export type TierKey = 'HIGH' | 'MEDIUM' | 'WATCH' | 'ON_TRACK'
export const TIER_LABEL: Record<TierKey, string> = {
  HIGH: 'Needs help now',
  MEDIUM: 'Needs a closer look',
  WATCH: 'Keep an eye on',
  ON_TRACK: 'On track',
}
export const TIER_HELP: Record<TierKey, string> = {
  HIGH: 'Very likely to fail or drop out without support',
  MEDIUM: 'Clear warning signs: a conversation would help',
  WATCH: 'Early signs worth keeping an eye on',
  ON_TRACK: 'No concerns right now',
}
export const tierLabel = (t: string | null | undefined): string => (t && TIER_LABEL[t as TierKey]) || humanize(t) || '—'

/* ------------------------------------------------------------------ case stages */
export const STAGE_LABEL: Record<string, string> = {
  suggested: 'New: waiting for review',
  under_review: 'Being reviewed',
  action_planned: 'Plan ready, needs an owner',
  assigned: 'Assigned to a counsellor',
  accepted: 'Counsellor accepted',
  contact_attempted: 'Tried to reach the student',
  support_in_progress: 'Support under way',
  failed_contact: 'Could not reach the student',
  follow_up_due: 'Follow-up due',
  service_unavailable: 'Waiting on a service',
  outcome_reviewed: 'Outcome being checked',
  closed: 'Resolved',
  reopened: 'Reopened',
  dismissed: 'Not needed',
  // older names that may still exist in stored data
  open: 'Open',
  in_review: 'Being reviewed',
  in_progress: 'Support under way',
  new: 'New: waiting for review',
  escalated: 'Escalated',
  resolved: 'Resolved',
}
export const stageLabel = (s: string | null | undefined): string => (s && STAGE_LABEL[s]) || humanize(s) || '—'
export const CLOSED_STAGES = ['closed', 'dismissed']
export const isClosedStage = (s: string | null | undefined) => !!s && CLOSED_STAGES.includes(s)

/** What a person can do next from each stage (plain verbs on buttons). `to` is the stage the case moves to. */
export interface NextStep { to: string; label: string; tone?: 'primary' | 'ghost' | 'danger' }
export const NEXT_STEPS: Record<string, NextStep[]> = {
  suggested: [
    { to: 'under_review', label: 'Start reviewing', tone: 'primary' },
    { to: 'dismissed', label: 'Not needed', tone: 'ghost' },
  ],
  under_review: [
    { to: 'action_planned', label: 'Approve the plan', tone: 'primary' },
    { to: 'dismissed', label: 'Not needed', tone: 'ghost' },
  ],
  action_planned: [
    { to: 'assigned', label: 'Give to a counsellor', tone: 'primary' },
    { to: 'dismissed', label: 'Not needed', tone: 'ghost' },
  ],
  assigned: [
    { to: 'accepted', label: 'Accept this case', tone: 'primary' },
    { to: 'action_planned', label: 'Send back', tone: 'ghost' },
  ],
  accepted: [
    { to: 'contact_attempted', label: 'I tried to reach the student', tone: 'primary' },
    { to: 'support_in_progress', label: 'Start support', tone: 'ghost' },
  ],
  contact_attempted: [
    { to: 'support_in_progress', label: 'Start support', tone: 'primary' },
    { to: 'failed_contact', label: 'Could not reach them', tone: 'ghost' },
    { to: 'follow_up_due', label: 'Plan a follow-up', tone: 'ghost' },
  ],
  failed_contact: [
    { to: 'contact_attempted', label: 'Try again', tone: 'primary' },
    { to: 'closed', label: 'Mark resolved', tone: 'ghost' },
  ],
  support_in_progress: [
    { to: 'follow_up_due', label: 'Plan a follow-up', tone: 'primary' },
    { to: 'outcome_reviewed', label: 'Check the outcome', tone: 'ghost' },
    { to: 'service_unavailable', label: 'Waiting on a service', tone: 'ghost' },
  ],
  follow_up_due: [
    { to: 'support_in_progress', label: 'Continue support', tone: 'primary' },
    { to: 'outcome_reviewed', label: 'Check the outcome', tone: 'ghost' },
    { to: 'failed_contact', label: 'Could not reach them', tone: 'ghost' },
  ],
  service_unavailable: [
    { to: 'action_planned', label: 'Make a new plan', tone: 'primary' },
    { to: 'closed', label: 'Mark resolved', tone: 'ghost' },
  ],
  outcome_reviewed: [
    { to: 'closed', label: 'Mark resolved', tone: 'primary' },
    { to: 'support_in_progress', label: 'Keep supporting', tone: 'ghost' },
  ],
  closed: [{ to: 'reopened', label: 'Reopen this case', tone: 'danger' }],
  reopened: [
    { to: 'assigned', label: 'Give to a counsellor', tone: 'primary' },
    { to: 'action_planned', label: 'Make a new plan', tone: 'ghost' },
  ],
  dismissed: [],
}

/* ------------------------------------------------------------------ priorities, outcomes, statuses */
export const PRIORITY_LABEL: Record<string, string> = { urgent: 'Urgent', critical: 'Urgent', high: 'High', medium: 'Normal', normal: 'Normal', low: 'Low' }
export const priorityLabel = (p: string | null | undefined): string => (p && PRIORITY_LABEL[p.toLowerCase()]) || humanize(p) || 'Normal'

export const OUTCOME_LABEL: Record<string, string> = { helped: 'It helped', mixed: 'It helped a little', not_helped: 'It did not help' }
export const outcomeLabel = (o: string | null | undefined): string => (o && OUTCOME_LABEL[o]) || humanize(o)

export const CATEGORY_LABEL: Record<string, string> = {
  academic_advising: 'Study advice',
  tutoring: 'Peer tutoring',
  counselling: 'Private counselling',
  financial_aid: 'Emergency financial help',
  mentoring: 'Mentoring',
  attendance: 'Attendance support',
}
export const categoryLabel = (c: string | null | undefined): string => (c && CATEGORY_LABEL[c]) || humanize(c)

/** Statuses of interventions, follow-ups, requests, sessions, uploads. */
export const STATUS_LABEL: Record<string, string> = {
  planned: 'Planned', scheduled: 'Booked', completed: 'Done', complete: 'Done', done: 'Done', cancelled: 'Cancelled', canceled: 'Cancelled',
  overdue: 'Late', upcoming: 'Coming up', pending: 'Waiting', active: 'Active', in_progress: 'Under way', open: 'Open',
  unassigned: 'No owner yet', unknown: 'Someone', missed: 'Missed', no_show: 'Did not attend', rescheduled: 'Moved',
  approved: 'Approved', rejected: 'Declined', submitted: 'Sent', new: 'New', closed: 'Closed', resolved: 'Resolved',
  succeeded: 'Done', failed: 'Did not work', processing: 'Working on it', queued: 'Waiting', validated: 'Checked',
  helped: 'It helped', mixed: 'It helped a little', not_helped: 'It did not help',
  improved: 'Improved', stable: 'About the same', declined: 'Got worse', draft: 'Draft', archived: 'Retired',
}
export const statusLabel = (s: string | null | undefined): string => (s && STATUS_LABEL[s.toLowerCase()]) || humanize(s)

/** Where a case came from. */
export const SOURCE_LABEL: Record<string, string> = {
  model: 'Spotted by the weekly check',
  risk_model: 'Spotted by the weekly check',
  signal: 'Spotted by the weekly check',
  student_request: 'Student asked for help',
  self_referral: 'Student asked for help',
  faculty: 'Raised by a teacher',
  faculty_referral: 'Raised by a teacher',
  manual: 'Added by staff',
}
export const sourceLabel = (s: string | null | undefined): string => (s && SOURCE_LABEL[s]) || humanize(s)

/** Generic: pick the most specific dictionary for any bucket label coming from the server. */
export function plainBucket(label: string): string {
  if (STAGE_LABEL[label]) return STAGE_LABEL[label]
  if (STATUS_LABEL[label.toLowerCase()]) return STATUS_LABEL[label.toLowerCase()]
  if (TIER_LABEL[label as TierKey]) return TIER_LABEL[label as TierKey]
  if (PRIORITY_LABEL[label.toLowerCase()]) return PRIORITY_LABEL[label.toLowerCase()]
  return /^[a-z0-9_]+$/.test(label) ? humanize(label) : label
}

/* ------------------------------------------------------------------ roles */
export const ROLE_LABEL: Record<string, string> = {
  institution_admin: 'Campus admin',
  platform_admin: 'Platform admin',
  hod: 'Head of department',
  faculty: 'Teacher',
  counsellor: 'Counsellor',
  student: 'Student',
  mentor: 'Mentor',
  finance: 'Finance',
  placement: 'Placement',
  leadership: 'Leadership',
}
export const roleName = (r: string | null | undefined): string => (r && ROLE_LABEL[r]) || humanize(r)

/* ------------------------------------------------------------------ reasons */
export const REASON_GROUP_LABEL: Record<string, string> = {
  score_level: 'Marks',
  score_trend: 'Marks',
  trend: 'Marks',
  baseline: 'Past results',
  load_history: 'Workload',
  co_attainment: 'Other courses',
  scores: 'Marks',
  marks: 'Marks',
  submissions: 'Missed work',
  submission: 'Missed work',
  late: 'Missed work',
  engagement: 'Online activity',
  activity: 'Online activity',
  attendance: 'Attendance',
  wellbeing: 'Wellbeing check-ins',
  pulse: 'Wellbeing check-ins',
  load: 'Workload',
  workload: 'Workload',
  prior: 'Past results',
  history: 'Past results',
}
export const reasonGroupLabel = (g: string | null | undefined): string => (g && REASON_GROUP_LABEL[g]) || humanize(g)

/* ------------------------------------------------------------------ dates */
const MS_DAY = 86_400_000
function toDate(s: string | Date | null | undefined): Date | null {
  if (!s) return null
  const d = s instanceof Date ? s : new Date(s)
  return Number.isNaN(d.getTime()) ? null : d
}
const dayMonth = (d: Date, withYear = false) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', ...(withYear ? { year: 'numeric' } : {}) })
const timeOf = (d: Date) => d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString()

/** "25 Oct" (adds the year when it is not this year). */
export function friendlyDate(s: string | Date | null | undefined): string {
  const d = toDate(s)
  if (!d) return '—'
  const now = new Date()
  if (sameDay(d, now)) return 'Today'
  if (sameDay(d, new Date(now.getTime() + MS_DAY))) return 'Tomorrow'
  if (sameDay(d, new Date(now.getTime() - MS_DAY))) return 'Yesterday'
  return dayMonth(d, d.getFullYear() !== now.getFullYear())
}
/** "Today 3:00 PM", "25 Oct, 3:00 PM". */
export function friendlyDateTime(s: string | Date | null | undefined): string {
  const d = toDate(s)
  if (!d) return '—'
  const day = friendlyDate(d)
  return `${day}${/^(Today|Tomorrow|Yesterday)$/.test(day) ? ' ' : ', '}${timeOf(d)}`
}
/** "25 Oct to 8 Nov". */
export function dateRange(start: string | null | undefined, end: string | null | undefined): string {
  const a = toDate(start)
  const b = toDate(end)
  if (a && b) return `${dayMonth(a)} to ${dayMonth(b)}`
  return a ? `From ${dayMonth(a)}` : b ? `Until ${dayMonth(b)}` : ''
}

/* ------------------------------------------------------------------ wellbeing check-ins */
/** Title for a check-in: its date range. Never the internal period code. */
export function checkInTitle(p: { starts_at?: string | null; ends_at?: string | null }, index?: number): string {
  const r = dateRange(p.starts_at, p.ends_at)
  return r || (index != null ? `Check-in ${index + 1}` : 'Check-in')
}
/**
 * Titles for a list of check-ins that only carry `starts_at` (oldest first).
 * The end of each is the day before the next one starts; the last one reuses the usual gap.
 */
export function checkInRanges(points: { starts_at: string; ends_at?: string | null }[]): string[] {
  const t = points.map((p) => new Date(p.starts_at).getTime())
  const gaps = t.slice(1).map((v, i) => v - t[i]).filter((g) => g > 0).sort((a, b) => a - b)
  const usual = gaps.length ? gaps[Math.floor(gaps.length / 2)] : 0
  return points.map((p, i) => {
    if (p.ends_at) return dateRange(p.starts_at, p.ends_at)
    const next = t[i + 1]
    const end = next ? next - MS_DAY : usual ? t[i] + usual - MS_DAY : null
    return end ? dateRange(p.starts_at, new Date(end).toISOString()) : checkInTitle(p, i)
  })
}
/** A wellbeing score (0-100) in words. */
export function wellbeingWord(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return 'Not enough answers yet'
  return score >= 75 ? 'Doing well' : score >= 60 ? 'Doing fine' : score >= 45 ? 'Hard lately' : 'Needs support'
}
export function wellbeingTone(score: number | null | undefined): 'good' | 'fine' | 'hard' | 'support' | 'none' {
  if (score == null || Number.isNaN(score)) return 'none'
  return score >= 75 ? 'good' : score >= 60 ? 'fine' : score >= 45 ? 'hard' : 'support'
}

/* ------------------------------------------------------------------ people, courses, weeks */
/** Name first. A bare id (like S260015) only appears as secondary text via `studentRef`. */
export function studentName(name?: string | null, ref?: string | null): string {
  return name || (ref ? `Student ${ref}` : 'Student')
}
export const studentRef = (name?: string | null, ref?: string | null): string | null => (name && ref ? `Student ${ref}` : null)
/** "CS201" with a title when we have one, otherwise just the code. */
export function courseName(code?: string | null, title?: string | null): string {
  return title ? `${title} (${code})` : code || 'Course'
}

const TERM_WEEKS = 17
/** Day 77 of the term -> "Week 11 of 17". */
export function termWeek(day: number | null | undefined): string {
  if (day == null) return ''
  return `Week ${Math.max(1, Math.min(TERM_WEEKS, Math.round(day / 7)))} of ${TERM_WEEKS}`
}

/* ------------------------------------------------------------------ numbers */
/** 0.81 -> "81%". */
export const percent = (n: number | null | undefined, digits = 0): string => (n == null || Number.isNaN(n) ? '—' : `${(n * 100).toFixed(digits)}%`)
/** 0.81 -> "8 in 10". */
export function inTen(p: number | null | undefined): string {
  if (p == null || Number.isNaN(p)) return '—'
  const n = Math.round(p * 10)
  return n <= 0 ? 'Fewer than 1 in 10' : `${Math.min(10, n)} in 10`
}
/** "chance of struggling" phrase: "8 in 10 chance of struggling". */
export const chanceOfStruggling = (p: number | null | undefined): string => (p == null ? '—' : `${inTen(p)} chance of struggling`)

/** Plain direction words for risk movement. */
export function movement(d: string | null | undefined): string {
  return d === 'up' ? 'Getting worse' : d === 'down' ? 'Getting better' : 'Steady'
}

/* ------------------------------------------------------------------ errors */
/** One short sentence saying what to do next. Status codes and ids never appear here. */
export function friendlyError(e: unknown): string {
  const status = (e as { status?: number } | null)?.status
  if (status === 0) return 'We could not reach the server. Check your internet and try again.'
  if (status === 401) return 'Your sign-in has expired. Please sign in again.'
  if (status === 403) return 'You do not have access to this. Ask your campus admin if you need it.'
  if (status === 404) return 'We could not find that. It may have been removed.'
  if (status === 409) return 'Someone else just changed this. Reload and try again.'
  if (status === 422) return 'Some details are missing or not valid. Please check and try again.'
  if (status && status >= 500) return 'Something went wrong on our side. Please try again in a moment.'
  return 'Something went wrong. Please try again.'
}
