export type DemoMode = 'normalStudent' | 'needsAttention' | 'activeSupport'

export interface StudentDemoScenario {
  studentName: string
  avatar: string
  degree: string
  year: string
  wellbeingScore: number
  scoreDelta: string
  isScorePositive: boolean
  checkInsCompleted: number
  checkInsTotal: number
  streakWeeks: number
  trendData: number[] // 4 weeks
  encouragement: {
    title: string
    description: string
    variant: 'positive' | 'warning' | 'info'
  }
  focusItems: { id: string; label: string; done: boolean }[]
  recentUpdates: {
    id: string
    title: string
    subtitle: string
    iconType: 'calendar' | 'document' | 'check'
    color: string
  }[]
  upcomingEvents: {
    id: string
    title: string
    time: string
    iconType: 'calendar' | 'users' | 'assessment'
  }[]
}

export const STUDENT_DEMO_DATA: Record<DemoMode, StudentDemoScenario> = {
  normalStudent: {
    studentName: 'Asha Verma',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    degree: 'B.Tech (CSE)',
    year: '3rd Year',
    wellbeingScore: 78,
    scoreDelta: '+6',
    isScorePositive: true,
    checkInsCompleted: 4,
    checkInsTotal: 7,
    streakWeeks: 3,
    trendData: [75, 68, 80, 92],
    encouragement: {
      title: "You're doing well!",
      description: 'Your engagement has been consistent this month.',
      variant: 'positive',
    },
    focusItems: [
      { id: 'f1', label: 'Complete check-in', done: true },
      { id: 'f2', label: 'Practice a wellbeing activity', done: false },
      { id: 'f3', label: 'Follow up on your action plan', done: false },
      { id: 'f4', label: 'Reflect on your progress', done: false },
    ],
    recentUpdates: [
      {
        id: 'u1',
        title: 'Mentor check-in scheduled',
        subtitle: '14 Oct, 17:30 with Prof. Sharma',
        iconType: 'calendar',
        color: 'purple',
      },
      {
        id: 'u2',
        title: 'Intervention plan updated',
        subtitle: 'New recommendations added',
        iconType: 'document',
        color: 'blue',
      },
      {
        id: 'u3',
        title: 'Assessment completed',
        subtitle: 'Wellbeing Assessment · 09 Oct',
        iconType: 'check',
        color: 'green',
      },
    ],
    upcomingEvents: [
      {
        id: 'ev1',
        title: 'Mentor Check-in',
        time: '14 Oct, 17:30',
        iconType: 'calendar',
      },
      {
        id: 'ev2',
        title: 'Follow-up Activity',
        time: '16 Oct, 12:00',
        iconType: 'users',
      },
      {
        id: 'ev3',
        title: 'Wellbeing Review',
        time: '20 Oct, 15:00',
        iconType: 'assessment',
      },
    ],
  },

  needsAttention: {
    studentName: 'Asha Verma',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    degree: 'B.Tech (CSE)',
    year: '3rd Year',
    wellbeingScore: 54,
    scoreDelta: '-8',
    isScorePositive: false,
    checkInsCompleted: 2,
    checkInsTotal: 7,
    streakWeeks: 1,
    trendData: [72, 65, 58, 54],
    encouragement: {
      title: 'Take it easy today',
      description: 'We noticed a dip in check-ins. Your mentor is here to help anytime.',
      variant: 'warning',
    },
    focusItems: [
      { id: 'f1', label: 'Complete pending weekly check-in', done: false },
      { id: 'f2', label: 'Review stress management exercise', done: false },
      { id: 'f3', label: 'Book optional confidential check-in', done: false },
      { id: 'f4', label: 'Take a 5-min breathing break', done: true },
    ],
    recentUpdates: [
      {
        id: 'u1',
        title: 'Check-in reminder flagged',
        subtitle: 'Weekly pulse window closes in 24 hours',
        iconType: 'calendar',
        color: 'yellow',
      },
      {
        id: 'u2',
        title: 'Confidential support available',
        subtitle: 'Counsellor slots open this Friday',
        iconType: 'document',
        color: 'purple',
      },
      {
        id: 'u3',
        title: 'Attendance notification',
        subtitle: 'Missed lab session on 12 Oct',
        iconType: 'check',
        color: 'yellow',
      },
    ],
    upcomingEvents: [
      {
        id: 'ev1',
        title: 'Weekly Pulse Deadline',
        time: 'Tomorrow, 18:00',
        iconType: 'calendar',
      },
      {
        id: 'ev2',
        title: 'Support Check-in Opportunity',
        time: '15 Oct, 15:30',
        iconType: 'users',
      },
      {
        id: 'ev3',
        title: 'Syllabus Catch-up Lab',
        time: '18 Oct, 10:00',
        iconType: 'assessment',
      },
    ],
  },

  activeSupport: {
    studentName: 'Asha Verma',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    degree: 'B.Tech (CSE)',
    year: '3rd Year',
    wellbeingScore: 68,
    scoreDelta: '+4',
    isScorePositive: true,
    checkInsCompleted: 5,
    checkInsTotal: 7,
    streakWeeks: 2,
    trendData: [52, 58, 64, 68],
    encouragement: {
      title: 'Support in progress!',
      description: 'Great progress on your makeup lab milestones this week.',
      variant: 'info',
    },
    focusItems: [
      { id: 'f1', label: 'Complete check-in', done: true },
      { id: 'f2', label: 'Attend 1-on-1 with Prof. Sharma', done: true },
      { id: 'f3', label: 'Submit lab 3 makeup exercise', done: true },
      { id: 'f4', label: 'Review weekly progress milestone', done: false },
    ],
    recentUpdates: [
      {
        id: 'u1',
        title: 'Mentor consultation recorded',
        subtitle: 'Attestation signed by Prof. Sharma',
        iconType: 'calendar',
        color: 'blue',
      },
      {
        id: 'u2',
        title: 'Intervention milestone 1 cleared',
        subtitle: 'Attendance benchmark restored to 78%',
        iconType: 'check',
        color: 'green',
      },
      {
        id: 'u3',
        title: 'Next 1-on-1 scheduled',
        subtitle: '14 Oct, 17:30 in Faculty Office',
        iconType: 'document',
        color: 'purple',
      },
    ],
    upcomingEvents: [
      {
        id: 'ev1',
        title: 'Mentor Check-in with Prof. Sharma',
        time: '14 Oct, 17:30',
        iconType: 'calendar',
      },
      {
        id: 'ev2',
        title: 'Lab Makeup Attendance Review',
        time: '16 Oct, 14:00',
        iconType: 'users',
      },
      {
        id: 'ev3',
        title: 'Plan Milestone Sign-off',
        time: '21 Oct, 16:30',
        iconType: 'assessment',
      },
    ],
  },
}

