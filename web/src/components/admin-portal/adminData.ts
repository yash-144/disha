/**
 * DISHA Admin Portal - Data Models & Synthetic Datasets
 * Strictly conforming to DISHA Blueprint:
 * - 01-product-requirements.md
 * - 03-domain-model.md
 * - 04-security-and-access.md
 * - 05-api-specification.md
 * - 07-case-workflow-and-worker.md
 * - 10-wellbeing-pulse-and-rewards.md
 * - 11-documents-and-anchoring.md
 */

export interface StudentRecord {
  id: string
  externalRef: string
  displayName: string
  cohortCode: string
  enrollmentStatus: 'active' | 'inactive' | 'graduated' | 'withdrawn'
  accountLinked: boolean
  linkedUserId?: string
  lastActive: string
  academicAverage: number
  riskSignalStatus: 'normal' | 'attention_suggested' | 'case_active'
}

export interface CaseRecord {
  id: string
  caseNumber: string
  studentId: string
  studentName: string
  cohort: string
  selectedInterventionKey: string
  interventionLabel: string
  domain: 'academic' | 'mentor' | 'finance' | 'counselling'
  state:
    | 'action_planned'
    | 'assigned'
    | 'accepted'
    | 'support_in_progress'
    | 'follow_up_due'
    | 'outcome_reviewed'
    | 'closed'
    | 'reopened'
    | 'escalated'
  primaryOwnerName: string
  primaryOwnerRole: string
  dueAt: string
  isOverdue: boolean
  isEscalated: boolean
  version: number
  summary: string
  lastAction: string
  tasksCount: { total: number; completed: number }
}

export interface AppointmentRecord {
  id: string
  title: string
  category: 'counselling' | 'case_review' | 'mentor_sync' | 'emergency_escalation'
  staffName: string
  staffRole: string
  participantName: string
  dateTime: string
  durationMinutes: number
  status: 'confirmed' | 'in_progress' | 'completed' | 'cancelled'
  mode: 'virtual' | 'in_person'
  roomOrLink: string
}

export interface InterventionCatalogItem {
  id: string
  interventionKey: string
  domain: 'academic' | 'mentor' | 'finance' | 'counselling'
  displayLabel: string
  description: string
  recipientRole: string
  requiredPurposeKey: string
  requiresHumanApproval: boolean
  active: boolean
  version: number
  activeCasesCount: number
}

export interface DocumentRecord {
  id: string
  documentRef: string
  title: string
  docType: 'intervention_plan' | 'support_summary' | 'case_decision' | 'uploaded_proof'
  fileName: string
  fileSizeBytes: number
  sha256Hash: string
  status: 'draft' | 'finalized' | 'anchor_pending' | 'anchored' | 'verification_mismatch'
  finalizedBy: string
  finalizedAt: string
  chainId: number
  txHash?: string
  blockNumber?: number
  anchoredAt?: string
  lastVerifiedAt: string
  verificationStatus: 'verified_match' | 'unanchored' | 'mismatch'
}

export interface RedemptionRecord {
  id: string
  studentId: string
  studentName: string
  studentRef: string
  sku: string
  itemTitle: string
  category: 'apparel' | 'stationery' | 'desk-tech' | 'badges'
  pointsCost: number
  status: 'requested' | 'approved' | 'fulfilled' | 'cancelled'
  requestedAt: string
  fulfilledAt?: string
}

export interface RewardCatalogItem {
  id: string
  sku: string
  title: string
  category: 'apparel' | 'stationery' | 'desk-tech' | 'badges'
  pointsCost: number
  stock: number
  active: boolean
}

// ================= INITIAL DATASETS =================

export const INITIAL_STUDENTS: StudentRecord[] = [
  {
    id: 'stud-1',
    externalRef: 'STU-2025-081',
    displayName: 'Asha Verma',
    cohortCode: '2025-CS',
    enrollmentStatus: 'active',
    accountLinked: true,
    linkedUserId: 'usr-stud-1',
    lastActive: 'Today, 09:30 AM',
    academicAverage: 82.4,
    riskSignalStatus: 'case_active',
  },
  {
    id: 'stud-2',
    externalRef: 'STU-2025-092',
    displayName: 'Rohan Mehta',
    cohortCode: '2025-CS',
    enrollmentStatus: 'active',
    accountLinked: true,
    linkedUserId: 'usr-stud-2',
    lastActive: 'Yesterday, 04:15 PM',
    academicAverage: 71.0,
    riskSignalStatus: 'attention_suggested',
  },
  {
    id: 'stud-3',
    externalRef: 'STU-2024-114',
    displayName: 'Neha Kapoor',
    cohortCode: '2024-ECE',
    enrollmentStatus: 'active',
    accountLinked: true,
    linkedUserId: 'usr-stud-3',
    lastActive: '28 Oct, 02:00 PM',
    academicAverage: 88.5,
    riskSignalStatus: 'normal',
  },
  {
    id: 'stud-4',
    externalRef: 'STU-2025-045',
    displayName: 'Arjun Singh',
    cohortCode: '2025-MECH',
    enrollmentStatus: 'active',
    accountLinked: false,
    lastActive: '25 Oct, 11:20 AM',
    academicAverage: 65.2,
    riskSignalStatus: 'attention_suggested',
  },
  {
    id: 'stud-5',
    externalRef: 'STU-2023-201',
    displayName: 'Priya Nair',
    cohortCode: '2023-CS',
    enrollmentStatus: 'graduated',
    accountLinked: true,
    lastActive: '15 Sep, 10:00 AM',
    academicAverage: 91.2,
    riskSignalStatus: 'normal',
  },
  {
    id: 'stud-6',
    externalRef: 'STU-2025-334',
    displayName: 'Vikram Joshi',
    cohortCode: '2025-EE',
    enrollmentStatus: 'inactive',
    accountLinked: true,
    lastActive: '12 Oct, 01:10 PM',
    academicAverage: 58.7,
    riskSignalStatus: 'case_active',
  },
]

export const INITIAL_CASES: CaseRecord[] = [
  {
    id: 'case-1027',
    caseNumber: 'CASE-2025-1027',
    studentId: 'stud-1',
    studentName: 'Asha Verma',
    cohort: '2025-CS',
    selectedInterventionKey: 'academic_workload_pacing',
    interventionLabel: 'Workload Pacing & Mentorship',
    domain: 'academic',
    state: 'support_in_progress',
    primaryOwnerName: 'Prof. Sharma',
    primaryOwnerRole: 'Faculty Mentor',
    dueAt: '14 Oct, 2025',
    isOverdue: false,
    isEscalated: false,
    version: 3,
    summary: 'Assistance for elevated academic stress and lab assignment backlog.',
    lastAction: 'Follow-up check-in logged by mentor',
    tasksCount: { total: 4, completed: 2 },
  },
  {
    id: 'case-0984',
    caseNumber: 'CASE-2025-0984',
    studentId: 'stud-2',
    studentName: 'Rohan Mehta',
    cohort: '2025-CS',
    selectedInterventionKey: 'counselling_referral',
    interventionLabel: 'Anxiety & Exam Resilience Support',
    domain: 'counselling',
    state: 'escalated',
    primaryOwnerName: 'Dr. Rao',
    primaryOwnerRole: 'Senior Counsellor',
    dueAt: '10 Oct, 2025',
    isOverdue: true,
    isEscalated: true,
    version: 4,
    summary: 'Elevated anxiety indicators detected during pre-midterm survey.',
    lastAction: 'Overdue deadline escalated to Student Welfare Committee',
    tasksCount: { total: 3, completed: 1 },
  },
  {
    id: 'case-0971',
    caseNumber: 'CASE-2025-0971',
    studentId: 'stud-4',
    studentName: 'Arjun Singh',
    cohort: '2025-MECH',
    selectedInterventionKey: 'attendance_recovery_plan',
    interventionLabel: 'Attendance Benchmark Restoration',
    domain: 'mentor',
    state: 'assigned',
    primaryOwnerName: 'Dr. Mukherjee',
    primaryOwnerRole: 'Department Mentor',
    dueAt: '18 Oct, 2025',
    isOverdue: false,
    isEscalated: false,
    version: 1,
    summary: 'Attendance slipped below 75% threshold in two core engineering labs.',
    lastAction: 'Awaiting primary owner acceptance',
    tasksCount: { total: 3, completed: 0 },
  },
  {
    id: 'case-0948',
    caseNumber: 'CASE-2025-0948',
    studentId: 'stud-6',
    studentName: 'Vikram Joshi',
    cohort: '2025-EE',
    selectedInterventionKey: 'wellbeing_checkin',
    interventionLabel: 'Routine Wellbeing Pulse Follow-up',
    domain: 'counselling',
    state: 'closed',
    primaryOwnerName: 'Meera K.',
    primaryOwnerRole: 'Wellbeing Specialist',
    dueAt: '05 Sep, 2025',
    isOverdue: false,
    isEscalated: false,
    version: 5,
    summary: 'Start-of-term wellbeing pulse review successfully completed.',
    lastAction: 'Case resolved with positive student feedback',
    tasksCount: { total: 4, completed: 4 },
  },
]

export const INITIAL_APPOINTMENTS: AppointmentRecord[] = [
  {
    id: 'app-1',
    title: 'High-Priority Case Escalation Sync',
    category: 'emergency_escalation',
    staffName: 'Dr. Rao (Counsellor)',
    staffRole: 'Senior Counsellor',
    participantName: 'Student Welfare Committee & Dean',
    dateTime: 'Today, 03:30 PM',
    durationMinutes: 45,
    status: 'confirmed',
    mode: 'virtual',
    roomOrLink: 'DISHA Secure Room #Alpha',
  },
  {
    id: 'app-2',
    title: 'Bi-Weekly Departmental Support Briefing',
    category: 'case_review',
    staffName: 'Prof. Sharma (Faculty)',
    staffRole: 'Faculty Mentor',
    participantName: 'Computer Science Faculty Cohort',
    dateTime: 'Tomorrow, 11:00 AM',
    durationMinutes: 60,
    status: 'confirmed',
    mode: 'in_person',
    roomOrLink: 'Conference Room 204',
  },
  {
    id: 'app-3',
    title: 'Confidential 1-on-1 Consultation',
    category: 'counselling',
    staffName: 'Meera K. (Counsellor)',
    staffRole: 'Wellbeing Specialist',
    participantName: 'Asha Verma',
    dateTime: '14 Oct, 05:30 PM',
    durationMinutes: 30,
    status: 'confirmed',
    mode: 'virtual',
    roomOrLink: 'DISHA Secure Room #401',
  },
  {
    id: 'app-4',
    title: 'Institutional Safeguarding Term Review',
    category: 'case_review',
    staffName: 'Dr. V. Raman (Admin)',
    staffRole: 'Chief Administrator',
    participantName: 'University Academic Senate',
    dateTime: '17 Oct, 02:00 PM',
    durationMinutes: 90,
    status: 'confirmed',
    mode: 'in_person',
    roomOrLink: 'Senate Hall A',
  },
]

export const INITIAL_INTERVENTIONS: InterventionCatalogItem[] = [
  {
    id: 'int-1',
    interventionKey: 'academic_workload_pacing',
    domain: 'academic',
    displayLabel: 'Academic Workload Pacing & Pomodoro Schedule',
    description: 'Structured 4-week pacing benchmarks for students facing high assignment density.',
    recipientRole: 'student',
    requiredPurposeKey: 'academic_support',
    requiresHumanApproval: true,
    active: true,
    version: 2,
    activeCasesCount: 14,
  },
  {
    id: 'int-2',
    interventionKey: 'counselling_referral',
    domain: 'counselling',
    displayLabel: 'Confidential Counselling & Stress Management',
    description: 'Direct referral to campus licensed psychological guidance specialists.',
    recipientRole: 'counsellor',
    requiredPurposeKey: 'counselling_referral',
    requiresHumanApproval: true,
    active: true,
    version: 1,
    activeCasesCount: 8,
  },
  {
    id: 'int-3',
    interventionKey: 'attendance_recovery_plan',
    domain: 'mentor',
    displayLabel: 'Lab Attendance & Makeup Benchmark Plan',
    description: 'Coordinated catch-up labs and attendance tracking protocol.',
    recipientRole: 'mentor',
    requiredPurposeKey: 'early_warning',
    requiresHumanApproval: true,
    active: true,
    version: 3,
    activeCasesCount: 11,
  },
  {
    id: 'int-4',
    interventionKey: 'emergency_welfare_escalation',
    domain: 'counselling',
    displayLabel: 'Urgent Institutional Welfare Escalation',
    description: 'High-priority protocol triggering immediate campus authority notifications.',
    recipientRole: 'counsellor',
    requiredPurposeKey: 'emergency_response',
    requiresHumanApproval: true,
    active: true,
    version: 1,
    activeCasesCount: 2,
  },
]

export const INITIAL_DOCUMENTS: DocumentRecord[] = [
  {
    id: 'doc-1',
    documentRef: 'DOC-2025-081-PLAN',
    title: 'Official Intervention Plan - Asha Verma',
    docType: 'intervention_plan',
    fileName: 'Intervention_Plan_CASE_1027.pdf',
    fileSizeBytes: 245760,
    sha256Hash: '9f83a48e3d81b9e248b1d98a02c3e1a7b8e5d3c2b1a0f9e8d7c6b5a4f3e2d1c0',
    status: 'anchored',
    finalizedBy: 'Prof. Sharma',
    finalizedAt: '12 Oct, 2025',
    chainId: 84532, // Base Sepolia
    txHash: '0x3a4b9c1d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b',
    blockNumber: 18492041,
    anchoredAt: '12 Oct, 2025 · 14:22 UTC',
    lastVerifiedAt: 'Today, 02:15 AM',
    verificationStatus: 'verified_match',
  },
  {
    id: 'doc-2',
    documentRef: 'DOC-2025-098-SUMMARY',
    title: 'Support Summary Attestation - Rohan Mehta',
    docType: 'support_summary',
    fileName: 'Support_Summary_CASE_0984.pdf',
    fileSizeBytes: 189440,
    sha256Hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    status: 'anchor_pending',
    finalizedBy: 'Dr. Rao',
    finalizedAt: '13 Oct, 2025',
    chainId: 84532,
    lastVerifiedAt: 'Pending confirmation',
    verificationStatus: 'unanchored',
  },
  {
    id: 'doc-3',
    documentRef: 'DOC-2025-045-DECISION',
    title: 'Academic Board Case Decision - Case 0948',
    docType: 'case_decision',
    fileName: 'Case_Decision_CASE_0948.pdf',
    fileSizeBytes: 312000,
    sha256Hash: '7a12b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2',
    status: 'anchored',
    finalizedBy: 'Dr. V. Raman',
    finalizedAt: '05 Sep, 2025',
    chainId: 84532,
    txHash: '0x7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d',
    blockNumber: 17920194,
    anchoredAt: '05 Sep, 2025 · 16:45 UTC',
    lastVerifiedAt: 'Yesterday, 11:30 PM',
    verificationStatus: 'verified_match',
  },
]

export const INITIAL_REDEMPTIONS: RedemptionRecord[] = [
  {
    id: 'red-101',
    studentId: 'stud-1',
    studentName: 'Asha Verma',
    studentRef: 'STU-2025-081',
    sku: 'DISHA-TSHIRT-L',
    itemTitle: 'DISHA Campus Wellbeing Hoodie (Lilac)',
    category: 'apparel',
    pointsCost: 500,
    status: 'requested',
    requestedAt: 'Yesterday, 06:15 PM',
  },
  {
    id: 'red-102',
    studentId: 'stud-2',
    studentName: 'Rohan Mehta',
    studentRef: 'STU-2025-092',
    sku: 'DISHA-BOTTLE-STEEL',
    itemTitle: 'Eco Hydration Steel Flask',
    category: 'desk-tech',
    pointsCost: 350,
    status: 'approved',
    requestedAt: '28 Oct, 03:20 PM',
  },
  {
    id: 'red-103',
    studentId: 'stud-3',
    studentName: 'Neha Kapoor',
    studentRef: 'STU-2024-114',
    sku: 'DISHA-NOTEBOOK-RECYCLED',
    itemTitle: 'Mindful Journal & Pen Set',
    category: 'stationery',
    pointsCost: 200,
    status: 'fulfilled',
    requestedAt: '20 Oct, 11:00 AM',
    fulfilledAt: '22 Oct, 02:00 PM',
  },
]

export const INITIAL_REWARD_CATALOG: RewardCatalogItem[] = [
  {
    id: 'item-1',
    sku: 'DISHA-TSHIRT-L',
    title: 'DISHA Campus Wellbeing Hoodie (Lilac)',
    category: 'apparel',
    pointsCost: 500,
    stock: 24,
    active: true,
  },
  {
    id: 'item-2',
    sku: 'DISHA-BOTTLE-STEEL',
    title: 'Eco Hydration Steel Flask',
    category: 'desk-tech',
    pointsCost: 350,
    stock: 45,
    active: true,
  },
  {
    id: 'item-3',
    sku: 'DISHA-NOTEBOOK-RECYCLED',
    title: 'Mindful Journal & Pen Set',
    category: 'stationery',
    pointsCost: 200,
    stock: 80,
    active: true,
  },
  {
    id: 'item-4',
    sku: 'DISHA-BADGE-PERSISTENCE',
    title: 'Semester Persistence Digital Badge',
    category: 'badges',
    pointsCost: 100,
    stock: 999,
    active: true,
  },
]

