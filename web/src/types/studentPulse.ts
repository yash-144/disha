export type PulseCategory = 'ACADEMIC' | 'CLASSROOM_FEEDBACK' | 'WELLBEING'

export type QuestionType = 'mcq' | 'descriptive' | 'likert' | 'single_choice' | 'multi_choice'

export type QuestionDifficulty = 'Easy' | 'Medium' | 'Hard'

export interface PulseQuestion {
  id: string
  courseId: string
  courseName: string
  category: PulseCategory
  categoryLabel: string
  prompt: string
  questionType: QuestionType
  difficulty: QuestionDifficulty
  marks: number
  options: string[]
  correctOption?: number
  correctAnswer?: string
  explanation?: string
  parameterTag?: string
}

export interface PulseAssignment {
  id: string
  courseId: string
  courseName: string
  sectionId: string
  title: string
  status: 'draft' | 'published' | 'closed'
  dueAt: string
  createdAt: string
  questionIds: string[]
  academicCount: number
  feedbackCount: number
  wellbeingCount: number
  totalMarks: number
  submissionCount: number
  totalStudents: number
  avgScorePercentage: number
}

export interface StudentPulseAnswerState {
  academicAnswers: Record<string, number | string> // questionId -> option index or descriptive text
  feedbackAnswers: Record<string, string | number> // questionId -> option text or 1-5 rating
  wellbeingAnswers: Record<string, number | string> // questionId -> 1-5 rating or string
}

export interface ObjectiveResult {
  questionId: string
  prompt: string
  selectedOption: number | string | undefined
  correctOption: number | undefined
  isCorrect: boolean
  marksAwarded: number
  maxMarks: number
  explanation?: string
}

export interface StudentPulseSubmission {
  submissionId: string
  pulseId: string
  studentId: string
  studentName?: string
  academicScore: number
  academicMaxMarks: number
  percentage: number
  objectiveResults: ObjectiveResult[]
  descriptiveAnswers?: Record<string, string>
  submittedAt: string
  isAnonymous: boolean
}

export interface ItemAnalysis {
  questionId: string
  prompt: string
  difficulty: QuestionDifficulty
  questionType: QuestionType
  marks: number
  accuracyRate: number
  discriminationIndex: 'High' | 'Normal'
}

export interface Pulse3PartAnalytics {
  pulseId: string
  title: string
  courseId: string
  sampleSize: number
  kAnonymityEnforced: boolean
  academicAnalysis: {
    averageScore: number
    maxMarks: number
    averagePercentage: number
    highestScore: number
    lowestScore: number
    itemAnalysis: ItemAnalysis[]
  }
  classroomFeedback: {
    paceDistribution: {
      justRightPct: number
      tooFastPct: number
      tooSlowPct: number
    }
    averageClarityRating: number
    averageHandsOnRating: number
    askingQuestionsComfortPct: number
    privacyStatus: string
  }
  wellbeingInsights: {
    cohortMotivationIndex: number
    highPressureStudentPct: number
    examConfidenceIndex: number
    actionableRecommendations: string[]
  }
}
