import { DemoMode } from '../student-portal/studentDemoData'

export interface CounsellorStudentItem {
  id: string
  name: string
  initials: string
  subtitle: string
  priority: 'High Priority' | 'Medium' | 'Low'
  avatarBg: string
  avatarText: string
  caseId: string
}

export interface CounsellorAppointment {
  id: string
  time: string
  title: string
  studentName: string
  type: 'video' | 'in-person'
}

export interface FocusAreaSegment {
  name: string
  percentage: number
  color: string
}

export interface ChecklistItem {
  id: string
  text: string
  completed: boolean
}

export interface CounsellorScenarioData {
  greetingName: string
  stats: {
    assignedStudents: { value: number; change: string; positive: boolean }
    activeCases: { value: number; change: string; positive: boolean }
    upcomingSessions: { value: number; label: string }
    followUpsDue: { value: number; change: string; positive: boolean }
  }
  caseLoadTrend: {
    weekLabels: string[]
    dataPoints: number[] // 4 weeks
    maxY: number
  }
  casesByFocusArea: {
    totalCases: number
    segments: FocusAreaSegment[]
  }
  studentsNeedingAttention: CounsellorStudentItem[]
  todaysSchedule: CounsellorAppointment[]
  wellbeingInsights: {
    headline: string
    delta: string
    trendData: number[]
  }
  focusItems: ChecklistItem[]
}

export const COUNSELLOR_DEMO_DATA: Record<DemoMode, CounsellorScenarioData> = {
  normalStudent: {
    greetingName: 'Dr. Meera',
    stats: {
      assignedStudents: { value: 28, change: '↑ +4 this week', positive: true },
      activeCases: { value: 12, change: '↑ +2 new', positive: true },
      upcomingSessions: { value: 6, label: 'Today & this week' },
      followUpsDue: { value: 4, change: '↓ -2 from last week', positive: true },
    },
    caseLoadTrend: {
      weekLabels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      dataPoints: [8, 12, 11, 16],
      maxY: 20,
    },
    casesByFocusArea: {
      totalCases: 12,
      segments: [
        { name: 'Academic Stress', percentage: 33, color: '#8B5CF6' },
        { name: 'Emotional Wellbeing', percentage: 25, color: '#FBBF24' },
        { name: 'Adjustment & Belonging', percentage: 17, color: '#10B981' },
        { name: 'Personal Concerns', percentage: 17, color: '#F43F5E' },
        { name: 'Other', percentage: 8, color: '#94A3B8' },
      ],
    },
    studentsNeedingAttention: [
      {
        id: 's-1',
        name: 'Aarav Khanna',
        initials: 'AK',
        subtitle: 'Increased stress indicators • Follow-up due',
        priority: 'High Priority',
        avatarBg: 'bg-[#EDE9FE]',
        avatarText: 'text-[#7C3AED]',
        caseId: 'case-ak-01',
      },
      {
        id: 's-2',
        name: 'Sneha Singh',
        initials: 'SS',
        subtitle: 'Missed 2 check-ins • Reach out',
        priority: 'Medium',
        avatarBg: 'bg-[#E0F2FE]',
        avatarText: 'text-[#0284C7]',
        caseId: 'case-ss-02',
      },
      {
        id: 's-3',
        name: 'Rohan Verma',
        initials: 'RV',
        subtitle: 'Declining wellbeing trend • Schedule session',
        priority: 'Medium',
        avatarBg: 'bg-[#DCFCE7]',
        avatarText: 'text-[#16A34A]',
        caseId: 'case-rv-03',
      },
    ],
    todaysSchedule: [
      {
        id: 'app-1',
        time: '10:30',
        title: 'Counselling Session',
        studentName: 'Aarav Khanna',
        type: 'video',
      },
      {
        id: 'app-2',
        time: '13:00',
        title: 'Follow-up Discussion',
        studentName: 'Sneha Singh',
        type: 'video',
      },
      {
        id: 'app-3',
        time: '15:30',
        title: 'Initial Assessment',
        studentName: 'Rohan Verma',
        type: 'video',
      },
    ],
    wellbeingInsights: {
      headline: 'Student engagement is up by 18% this month. 🎉',
      delta: '+18%',
      trendData: [12, 15, 14, 20, 22, 28, 32],
    },
    focusItems: [
      { id: 'f-1', text: 'Complete follow-ups (3)', completed: true },
      { id: 'f-2', text: 'Review new support requests', completed: true },
      { id: 'f-3', text: 'Conduct scheduled sessions (6)', completed: false },
      { id: 'f-4', text: 'Update case notes', completed: false },
    ],
  },

  needsAttention: {
    greetingName: 'Dr. Meera',
    stats: {
      assignedStudents: { value: 34, change: '↑ +8 this week', positive: false },
      activeCases: { value: 18, change: '↑ +5 urgent', positive: false },
      upcomingSessions: { value: 9, label: 'High triage demand' },
      followUpsDue: { value: 7, change: '↑ +3 overdue', positive: false },
    },
    caseLoadTrend: {
      weekLabels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      dataPoints: [10, 14, 18, 22],
      maxY: 25,
    },
    casesByFocusArea: {
      totalCases: 18,
      segments: [
        { name: 'Academic Stress', percentage: 42, color: '#8B5CF6' },
        { name: 'Emotional Wellbeing', percentage: 30, color: '#FBBF24' },
        { name: 'Adjustment & Belonging', percentage: 12, color: '#10B981' },
        { name: 'Personal Concerns', percentage: 11, color: '#F43F5E' },
        { name: 'Other', percentage: 5, color: '#94A3B8' },
      ],
    },
    studentsNeedingAttention: [
      {
        id: 's-101',
        name: 'Aarav Khanna',
        initials: 'AK',
        subtitle: 'Acute mid-term anxiety reported • Urgent review',
        priority: 'High Priority',
        avatarBg: 'bg-[#FEE2E2]',
        avatarText: 'text-[#DC2626]',
        caseId: 'case-ak-01',
      },
      {
        id: 's-102',
        name: 'Priyanshu Roy',
        initials: 'PR',
        subtitle: 'Lab attendance drop flagged by Faculty mentor',
        priority: 'High Priority',
        avatarBg: 'bg-[#EDE9FE]',
        avatarText: 'text-[#7C3AED]',
        caseId: 'case-pr-04',
      },
      {
        id: 's-103',
        name: 'Sneha Singh',
        initials: 'SS',
        subtitle: 'Check-in window expired without submission',
        priority: 'Medium',
        avatarBg: 'bg-[#FEF3C7]',
        avatarText: 'text-[#D97706]',
        caseId: 'case-ss-02',
      },
    ],
    todaysSchedule: [
      {
        id: 'app-101',
        time: '09:30',
        title: 'Emergency Triage Check-in',
        studentName: 'Aarav Khanna',
        type: 'video',
      },
      {
        id: 'app-102',
        time: '11:15',
        title: 'Academic Stress Consultation',
        studentName: 'Priyanshu Roy',
        type: 'video',
      },
      {
        id: 'app-103',
        time: '14:00',
        title: 'Wellbeing Follow-up',
        studentName: 'Sneha Singh',
        type: 'video',
      },
    ],
    wellbeingInsights: {
      headline: 'Exam period workload surge: 5 pending reviews today.',
      delta: '+24% cases',
      trendData: [10, 12, 18, 22, 25, 29, 36],
    },
    focusItems: [
      { id: 'f-101', text: 'Complete urgent follow-ups (5)', completed: false },
      { id: 'f-102', text: 'Triage new exam anxiety referrals', completed: true },
      { id: 'f-103', text: 'Coordinate with Prof. Sharma on Lab 3 plan', completed: false },
      { id: 'f-104', text: 'Log emergency contact notes', completed: false },
    ],
  },

  activeSupport: {
    greetingName: 'Dr. Meera',
    stats: {
      assignedStudents: { value: 30, change: '↑ +2 this week', positive: true },
      activeCases: { value: 14, change: '4 cases recovering', positive: true },
      upcomingSessions: { value: 7, label: 'Milestone reviews' },
      followUpsDue: { value: 3, change: '↓ -3 completed', positive: true },
    },
    caseLoadTrend: {
      weekLabels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      dataPoints: [14, 16, 15, 13],
      maxY: 20,
    },
    casesByFocusArea: {
      totalCases: 14,
      segments: [
        { name: 'Academic Stress', percentage: 28, color: '#8B5CF6' },
        { name: 'Emotional Wellbeing', percentage: 28, color: '#FBBF24' },
        { name: 'Adjustment & Belonging', percentage: 22, color: '#10B981' },
        { name: 'Personal Concerns', percentage: 14, color: '#F43F5E' },
        { name: 'Other', percentage: 8, color: '#94A3B8' },
      ],
    },
    studentsNeedingAttention: [
      {
        id: 's-201',
        name: 'Aarav Khanna',
        initials: 'AK',
        subtitle: 'Milestone 2 cleared • Progress stable',
        priority: 'Medium',
        avatarBg: 'bg-[#DCFCE7]',
        avatarText: 'text-[#16A34A]',
        caseId: 'case-ak-01',
      },
      {
        id: 's-202',
        name: 'Tanya Sen',
        initials: 'TS',
        subtitle: 'Mid-term check-in scheduled for tomorrow',
        priority: 'Medium',
        avatarBg: 'bg-[#E0F2FE]',
        avatarText: 'text-[#0284C7]',
        caseId: 'case-ts-05',
      },
      {
        id: 's-203',
        name: 'Rohan Verma',
        initials: 'RV',
        subtitle: 'Reviewing sleep & lifestyle goals',
        priority: 'Low',
        avatarBg: 'bg-[#F3E8FF]',
        avatarText: 'text-[#7C3AED]',
        caseId: 'case-rv-03',
      },
    ],
    todaysSchedule: [
      {
        id: 'app-201',
        time: '11:00',
        title: 'Milestone Review Session',
        studentName: 'Aarav Khanna',
        type: 'video',
      },
      {
        id: 'app-202',
        time: '14:30',
        title: 'Lifestyle Routine Follow-up',
        studentName: 'Rohan Verma',
        type: 'video',
      },
      {
        id: 'app-203',
        time: '16:00',
        title: 'Intervention Sign-off Briefing',
        studentName: 'Tanya Sen',
        type: 'video',
      },
    ],
    wellbeingInsights: {
      headline: 'Positive intervention trajectory: 64% cases stabilizing.',
      delta: '+32% recovery',
      trendData: [15, 18, 22, 26, 30, 34, 38],
    },
    focusItems: [
      { id: 'f-201', text: 'Complete milestone follow-ups (3)', completed: true },
      { id: 'f-202', text: 'Sign off on Aarav’s attendance clearance', completed: true },
      { id: 'f-203', text: 'Conduct scheduled review sessions (7)', completed: false },
      { id: 'f-204', text: 'Document intervention outcomes in ledger', completed: false },
    ],
  },
}

