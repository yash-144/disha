import React, { useState } from 'react'
import {
  Sparkles,
  Dices,
  BarChart3,
  CheckCircle2,
  Clock,
  Users,
  Award,
  BookOpen,
  MessageSquare,
  Heart,
  ChevronRight,
  Plus,
  RefreshCw,
  Eye,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
  FileText,
  Filter,
  Check,
  X,
  HelpCircle,
  TrendingUp,
} from 'lucide-react'
import {
  PulseQuestion,
  PulseAssignment,
  Pulse3PartAnalytics,
} from '../../types/studentPulse'
import {
  INITIAL_PULSE_ASSIGNMENTS,
  DEMO_PULSE_ANALYTICS,
  generateRandomizedPulseQuestions,
} from '../student-portal/studentPulseData'
import { useApp } from '../../context/AppContext'

export function TeacherAssessmentsPage() {
  const { addToast } = useApp()

  // Tab State: 'list' | 'create' | 'analytics'
  const [activeSubTab, setActiveSubTab] = useState<'list' | 'create' | 'analytics'>('list')
  const [courseFilter, setCourseFilter] = useState<'ALL' | 'CS201' | 'CS202'>('ALL')

  // Assignments store
  const [assignments, setAssignments] = useState<PulseAssignment[]>(INITIAL_PULSE_ASSIGNMENTS)
  const [selectedPulseForAnalytics, setSelectedPulseForAnalytics] = useState<PulseAssignment>(
    INITIAL_PULSE_ASSIGNMENTS[0]
  )

  // Creation & Randomizer State
  const [newTitle, setNewTitle] = useState('Student Pulse #5: Dynamic Programming & Recursion')
  const [newCourseId, setNewCourseId] = useState<'CS201' | 'CS202'>('CS201')
  const [newSectionId, setNewSectionId] = useState('Section A (B.Tech 3rd Yr)')
  const [newDueDate, setNewDueDate] = useState('2026-11-12')
  const [academicCount, setAcademicCount] = useState(5)
  const [feedbackCount, setFeedbackCount] = useState(4)
  const [wellbeingCount, setWellbeingCount] = useState(3)

  // Generated randomized questions preview
  const [generatedQuestions, setGeneratedQuestions] = useState<{
    academic: PulseQuestion[]
    feedback: PulseQuestion[]
    wellbeing: PulseQuestion[]
    allQuestions: PulseQuestion[]
    totalMarks: number
  }>(() => generateRandomizedPulseQuestions('CS201', 5, 4, 3))

  const [previewCategoryTab, setPreviewCategoryTab] = useState<'ACADEMIC' | 'CLASSROOM_FEEDBACK' | 'WELLBEING'>('ACADEMIC')

  // Descriptive grading drawer state
  const [gradingModalOpen, setGradingModalOpen] = useState(false)
  const [descriptiveGrade, setDescriptiveGrade] = useState(4.5)
  const [descriptiveFeedback, setDescriptiveFeedback] = useState('Solid articulation of call stack frame allocation versus FIFO queue buffering.')

  // Handler: Re-roll randomized questions
  const handleRegenerateQuestions = () => {
    const result = generateRandomizedPulseQuestions(newCourseId, academicCount, feedbackCount, wellbeingCount)
    setGeneratedQuestions(result)
    addToast(
      'Questions Re-randomized',
      `Sampled ${result.allQuestions.length} unique questions without duplicates from question bank.`,
      'info'
    )
  }

  // Handler: Course change in creation form
  const handleCourseChange = (cid: 'CS201' | 'CS202') => {
    setNewCourseId(cid)
    const result = generateRandomizedPulseQuestions(cid, academicCount, feedbackCount, wellbeingCount)
    setGeneratedQuestions(result)
    setNewTitle(
      cid === 'CS201'
        ? 'Student Pulse #5: Dynamic Programming & Heaps'
        : 'Student Pulse #3: Query Plans, Indexes & Concurrency'
    )
  }

  // Handler: Publish new Student Pulse
  const handlePublishPulse = () => {
    if (!newTitle.trim()) {
      addToast('Validation Error', 'Please enter a valid pulse assignment title.', 'error')
      return
    }

    const newAssignment: PulseAssignment = {
      id: `pulse-${newCourseId.toLowerCase()}-${Date.now().toString().slice(-4)}`,
      courseId: newCourseId,
      courseName: newCourseId === 'CS201' ? 'Data Structures & Algorithms' : 'Database Management Systems',
      sectionId: newSectionId,
      title: newTitle,
      status: 'published',
      dueAt: `${newDueDate}T23:59:59Z`,
      createdAt: new Date().toISOString(),
      questionIds: generatedQuestions.allQuestions.map((q) => q.id),
      academicCount: generatedQuestions.academic.length,
      feedbackCount: generatedQuestions.feedback.length,
      wellbeingCount: generatedQuestions.wellbeing.length,
      totalMarks: generatedQuestions.totalMarks,
      submissionCount: 0,
      totalStudents: 45,
      avgScorePercentage: 0,
    }

    setAssignments((prev) => [newAssignment, ...prev])
    setActiveSubTab('list')
    addToast(
      'Student Pulse Published! 🎉',
      `Locked ${generatedQuestions.allQuestions.length} questions across 3 categories and published to students.`,
      'success'
    )
  }

  // Filtered assignments
  const filteredAssignments = assignments.filter((p) => {
    if (courseFilter === 'ALL') return true
    return p.courseId === courseFilter
  })

  // Open 3-part analytics for an assignment
  const handleOpenAnalytics = (assignment: PulseAssignment) => {
    setSelectedPulseForAnalytics(assignment)
    setActiveSubTab('analytics')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="flex-1 flex flex-col gap-4 min-w-0 font-sans text-[#1E2433] overflow-y-auto pr-1">
      {/* 1. Header & Navigation Ribbon */}
      <div className="bg-white rounded-2xl sm:rounded-3xl p-5 border border-purple-100 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-semibold">
              Assessment & Feedback Hub
            </span>
            <span className="text-xs text-gray-400">•</span>
            <span className="text-xs text-gray-500 font-medium">Replaces legacy CLO sheets</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#0F172A] tracking-tight">
            Student Pulse Assessments
          </h1>
          <p className="text-xs sm:text-sm text-gray-600 mt-0.5">
            Evaluate academic understanding, gather aggregated classroom feedback, and monitor student wellbeing.
          </p>
        </div>

        {/* Tab switch buttons */}
        <div className="flex items-center gap-2 bg-[#F8F9FE] p-1.5 rounded-2xl border border-gray-200">
          <button
            type="button"
            onClick={() => setActiveSubTab('list')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'list'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            All Pulses ({assignments.length})
          </button>
          <button
            type="button"
            onClick={() => {
              handleRegenerateQuestions()
              setActiveSubTab('create')
            }}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'create'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Plus className="w-4 h-4" />
            Create Student Pulse
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('analytics')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'analytics'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            3-Part Analytics
          </button>
        </div>
      </div>

      {/* 2. SUBTAB: ALL PULSES LIST */}
      {activeSubTab === 'list' && (
        <div className="flex flex-col gap-4">
          {/* Top Quick Stats Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-2xs">
              <span className="text-xs text-gray-500 font-medium">Published Pulses</span>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {assignments.filter((a) => a.status === 'published').length}
              </div>
              <span className="text-[11px] text-emerald-600 font-medium">Active in semester</span>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-2xs">
              <span className="text-xs text-gray-500 font-medium">Submissions Received</span>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {assignments.reduce((sum, a) => sum + a.submissionCount, 0)}
              </div>
              <span className="text-[11px] text-purple-600 font-medium">Across active cohorts</span>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-2xs">
              <span className="text-xs text-gray-500 font-medium">Avg Academic Score</span>
              <div className="text-2xl font-bold text-emerald-600 mt-1">81.4%</div>
              <span className="text-[11px] text-emerald-700 font-medium">↑ +3.2% vs previous pulse</span>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-2xs">
              <span className="text-xs text-gray-500 font-medium">Lecture Pace Approval</span>
              <div className="text-2xl font-bold text-purple-600 mt-1">73.8%</div>
              <span className="text-[11px] text-gray-500 font-medium">Rated "Just Right"</span>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex items-center justify-between bg-white px-4 py-3 rounded-2xl border border-gray-200">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-xs font-semibold text-gray-700">Course Filter:</span>
              <button
                type="button"
                onClick={() => setCourseFilter('ALL')}
                className={`px-3 py-1 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                  courseFilter === 'ALL'
                    ? 'bg-purple-100 text-purple-700 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                All Courses
              </button>
              <button
                type="button"
                onClick={() => setCourseFilter('CS201')}
                className={`px-3 py-1 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                  courseFilter === 'CS201'
                    ? 'bg-purple-100 text-purple-700 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                CS201 (DSA)
              </button>
              <button
                type="button"
                onClick={() => setCourseFilter('CS202')}
                className={`px-3 py-1 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                  courseFilter === 'CS202'
                    ? 'bg-purple-100 text-purple-700 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                CS202 (DBMS)
              </button>
            </div>
            <button
              type="button"
              onClick={() => {
                handleRegenerateQuestions()
                setActiveSubTab('create')
              }}
              className="px-3.5 py-1.5 rounded-xl bg-purple-600 text-white text-xs font-semibold hover:bg-purple-700 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
            >
              <Plus className="w-3.5 h-3.5" />
              New Student Pulse
            </button>
          </div>

          {/* Pulse Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAssignments.map((pulse) => {
              const participationPct =
                pulse.totalStudents > 0
                  ? Math.round((pulse.submissionCount / pulse.totalStudents) * 100)
                  : 0

              return (
                <div
                  key={pulse.id}
                  className="bg-white rounded-3xl p-5 border border-gray-200/90 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Top badging */}
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[11px] font-bold border border-blue-200">
                        {pulse.courseId} • {pulse.sectionId}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase ${
                          pulse.status === 'published'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {pulse.status}
                      </span>
                    </div>

                    <h3 className="font-bold text-gray-900 text-base leading-snug">
                      {pulse.title}
                    </h3>

                    {/* Question category badges */}
                    <div className="flex flex-wrap items-center gap-1.5 mt-3">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 text-[11px] font-medium border border-purple-100">
                        <BookOpen className="w-3 h-3" />
                        {pulse.academicCount} Academic
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 text-[11px] font-medium border border-sky-100">
                        <MessageSquare className="w-3 h-3" />
                        {pulse.feedbackCount} Feedback
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 text-[11px] font-medium border border-rose-100">
                        <Heart className="w-3 h-3" />
                        {pulse.wellbeingCount} Wellbeing
                      </span>
                    </div>

                    {/* Participation progress bar */}
                    <div className="mt-4 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1.5">
                        <span>
                          Submissions: <strong>{pulse.submissionCount}</strong> / {pulse.totalStudents}
                        </span>
                        <span className="font-bold text-purple-600">{participationPct}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all duration-500"
                          style={{ width: `${participationPct}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Actions footer */}
                  <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
                    <div className="text-[11px] text-gray-500 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      Due {new Date(pulse.dueAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </div>

                    <button
                      type="button"
                      onClick={() => handleOpenAnalytics(pulse)}
                      className="px-3.5 py-1.5 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      View 3-Part Analytics
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 3. SUBTAB: CREATE STUDENT PULSE (RANDOMIZER ENGINE) */}
      {activeSubTab === 'create' && (
        <div className="flex flex-col gap-5">
          {/* Configuration Card */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  Configure & Randomize Student Pulse
                </h2>
                <p className="text-xs text-gray-500">
                  Specify category distribution and automatically draw randomized, non-duplicate questions from the question bank.
                </p>
              </div>
              <button
                type="button"
                onClick={handleRegenerateQuestions}
                className="px-4 py-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shadow-2xs"
              >
                <Dices className="w-4 h-4 text-purple-600 animate-spin-once" />
                Regenerate Questions
              </button>
            </div>

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Course</label>
                <select
                  value={newCourseId}
                  onChange={(e) => handleCourseChange(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 text-xs font-medium focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white cursor-pointer"
                >
                  <option value="CS201">CS201: Data Structures & Algorithms</option>
                  <option value="CS202">CS202: Database Management Systems</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Target Section</label>
                <select
                  value={newSectionId}
                  onChange={(e) => setNewSectionId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 text-xs font-medium focus:ring-2 focus:ring-purple-400 focus:outline-none bg-white cursor-pointer"
                >
                  <option value="Section A (B.Tech 3rd Yr)">Section A (B.Tech 3rd Yr) — 45 Students</option>
                  <option value="Section B (B.Tech 3rd Yr)">Section B (B.Tech 3rd Yr) — 44 Students</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-gray-700 mb-1">Assignment Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Student Pulse #4: Recursion & Trees"
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 text-xs font-medium focus:ring-2 focus:ring-purple-400 focus:outline-none"
                />
              </div>
            </div>

            {/* 3 Categories Question Distribution Sliders */}
            <div className="mt-5 pt-4 border-t border-gray-100">
              <span className="text-xs font-bold text-gray-900 block mb-3">
                Question Distribution across 3 Categories:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Category A */}
                <div className="p-4 rounded-2xl bg-purple-50/70 border border-purple-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-purple-900 flex items-center gap-1.5">
                      <BookOpen className="w-4 h-4 text-purple-600" />
                      Category A: Academic
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-purple-600 text-white text-xs font-bold">
                      {academicCount} Questions
                    </span>
                  </div>
                  <input
                    type="range"
                    min={2}
                    max={7}
                    value={academicCount}
                    onChange={(e) => {
                      const count = Number(e.target.value)
                      setAcademicCount(count)
                      setGeneratedQuestions(
                        generateRandomizedPulseQuestions(newCourseId, count, feedbackCount, wellbeingCount)
                      )
                    }}
                    className="w-full accent-purple-600 cursor-pointer"
                  />
                  <span className="text-[11px] text-purple-800 mt-1 block">
                    MCQs & Short descriptive tasks for subject understanding.
                  </span>
                </div>

                {/* Category B */}
                <div className="p-4 rounded-2xl bg-sky-50/70 border border-sky-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-sky-900 flex items-center gap-1.5">
                      <MessageSquare className="w-4 h-4 text-sky-600" />
                      Category B: Feedback
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-sky-600 text-white text-xs font-bold">
                      {feedbackCount} Questions
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={5}
                    value={feedbackCount}
                    onChange={(e) => {
                      const count = Number(e.target.value)
                      setFeedbackCount(count)
                      setGeneratedQuestions(
                        generateRandomizedPulseQuestions(newCourseId, academicCount, count, wellbeingCount)
                      )
                    }}
                    className="w-full accent-sky-600 cursor-pointer"
                  />
                  <span className="text-[11px] text-sky-800 mt-1 block">
                    Lecture pace, clarity, hands-on exposure, and participation.
                  </span>
                </div>

                {/* Category C */}
                <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-rose-900 flex items-center gap-1.5">
                      <Heart className="w-4 h-4 text-rose-600" />
                      Category C: Wellbeing
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white text-xs font-bold">
                      {wellbeingCount} Questions
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={4}
                    value={wellbeingCount}
                    onChange={(e) => {
                      const count = Number(e.target.value)
                      setWellbeingCount(count)
                      setGeneratedQuestions(
                        generateRandomizedPulseQuestions(newCourseId, academicCount, feedbackCount, count)
                      )
                    }}
                    className="w-full accent-rose-600 cursor-pointer"
                  />
                  <span className="text-[11px] text-rose-800 mt-1 block">
                    Non-diagnostic motivation, academic pressure, and exam readiness.
                  </span>
                </div>
              </div>
            </div>

            {/* Total summary bar */}
            <div className="mt-5 p-3 rounded-2xl bg-[#F8F9FE] border border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-3 text-xs text-gray-700">
                <span>
                  Total Randomized Questions: <strong>{generatedQuestions.allQuestions.length}</strong>
                </span>
                <span>•</span>
                <span>
                  Total Academic Marks: <strong>{generatedQuestions.totalMarks} Marks</strong>
                </span>
                <span>•</span>
                <span className="text-emerald-700 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4" /> Zero-duplicate randomized sampling active
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handlePublishPulse}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
                >
                  <Check className="w-4 h-4" />
                  Publish & Lock Questions
                </button>
              </div>
            </div>
          </div>

          {/* Live Questions Preview Card */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <Eye className="w-4 h-4 text-purple-600" />
                  Live Preview of Randomized Questions
                </h3>
                <p className="text-xs text-gray-500">
                  Faculty preview before locking. Re-roll at any time with the Regenerate button.
                </p>
              </div>

              {/* Preview Category Tabs */}
              <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl">
                <button
                  type="button"
                  onClick={() => setPreviewCategoryTab('ACADEMIC')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    previewCategoryTab === 'ACADEMIC'
                      ? 'bg-white text-purple-700 shadow-2xs'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Academic ({generatedQuestions.academic.length})
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewCategoryTab('CLASSROOM_FEEDBACK')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    previewCategoryTab === 'CLASSROOM_FEEDBACK'
                      ? 'bg-white text-sky-700 shadow-2xs'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Classroom Feedback ({generatedQuestions.feedback.length})
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewCategoryTab('WELLBEING')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    previewCategoryTab === 'WELLBEING'
                      ? 'bg-white text-rose-700 shadow-2xs'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Wellbeing ({generatedQuestions.wellbeing.length})
                </button>
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-3">
              {(previewCategoryTab === 'ACADEMIC'
                ? generatedQuestions.academic
                : previewCategoryTab === 'CLASSROOM_FEEDBACK'
                ? generatedQuestions.feedback
                : generatedQuestions.wellbeing
              ).map((q, idx) => (
                <div
                  key={q.id}
                  className="p-4 rounded-2xl border border-gray-200/80 bg-[#FAFAFC] hover:border-purple-200 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">
                        Q{idx + 1}
                      </span>
                      <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                        {q.questionType}
                      </span>
                      {q.difficulty && (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            q.difficulty === 'Easy'
                              ? 'bg-emerald-100 text-emerald-800'
                              : q.difficulty === 'Medium'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {q.difficulty}
                        </span>
                      )}
                    </div>
                    {q.marks > 0 && (
                      <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        {q.marks} Marks
                      </span>
                    )}
                  </div>

                  <p className="text-sm font-semibold text-gray-900 mb-2">{q.prompt}</p>

                  {/* Options render if MCQ or single choice */}
                  {q.options && q.options.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                      {q.options.map((opt, optIdx) => {
                        const isCorrect = q.correctOption === optIdx
                        return (
                          <div
                            key={optIdx}
                            className={`p-2.5 rounded-xl text-xs flex items-center justify-between border ${
                              isCorrect && previewCategoryTab === 'ACADEMIC'
                                ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold'
                                : 'bg-white border-gray-200 text-gray-700'
                            }`}
                          >
                            <span>{opt}</span>
                            {isCorrect && previewCategoryTab === 'ACADEMIC' && (
                              <span className="text-[10px] bg-emerald-600 text-white px-1.5 py-0.5 rounded font-bold">
                                Key Answer
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Descriptive note */}
                  {q.questionType === 'descriptive' && (
                    <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 mt-2">
                      <strong>Expected rubric / answer outline:</strong> {q.correctAnswer}
                    </div>
                  )}

                  {q.explanation && (
                    <p className="text-[11px] text-gray-500 mt-2 italic">
                      <strong>Concept explanation:</strong> {q.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 4. SUBTAB: 3-PART ANALYTICS DASHBOARD */}
      {activeSubTab === 'analytics' && (
        <div className="flex flex-col gap-5">
          {/* Top Analytics Banner */}
          <div className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white rounded-3xl p-6 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded-full bg-purple-400/20 text-purple-200 text-xs font-bold border border-purple-300/30">
                  Comprehensive 3-Part Analytics
                </span>
                <span className="text-xs text-purple-200">•</span>
                <span className="text-xs text-emerald-300 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> k-Anonymity Enforced (n=42 ≥ 5)
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
                {selectedPulseForAnalytics.title}
              </h2>
              <p className="text-xs sm:text-sm text-purple-200 mt-0.5">
                Cohort: {selectedPulseForAnalytics.courseId} ({selectedPulseForAnalytics.sectionId}) • 42 Submissions Evaluated
              </p>
            </div>

            <button
              type="button"
              onClick={() => setGradingModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-white text-purple-900 hover:bg-purple-50 text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer shrink-0"
            >
              <FileText className="w-4 h-4 text-purple-700" />
              Review Descriptive Submissions
            </button>
          </div>

          {/* PART 1: ACADEMIC PERFORMANCE ANALYSIS */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">
                    Category A: Academic Performance Analysis
                  </h3>
                  <p className="text-xs text-gray-500">
                    Objective auto-graded accuracy, score distributions, and question item discrimination.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-purple-50 text-purple-700 font-bold text-xs border border-purple-200">
                Avg: {DEMO_PULSE_ANALYTICS.academicAnalysis.averagePercentage}%
              </span>
            </div>

            {/* Academic Stat Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
              <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-gray-200">
                <span className="text-[11px] text-gray-500 font-medium">Cohort Average</span>
                <div className="text-xl font-bold text-purple-700 mt-0.5">
                  {DEMO_PULSE_ANALYTICS.academicAnalysis.averageScore} / {DEMO_PULSE_ANALYTICS.academicAnalysis.maxMarks}
                </div>
                <span className="text-[10px] text-emerald-600 font-semibold">81.4% accuracy</span>
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-gray-200">
                <span className="text-[11px] text-gray-500 font-medium">Top Score</span>
                <div className="text-xl font-bold text-emerald-600 mt-0.5">
                  {DEMO_PULSE_ANALYTICS.academicAnalysis.highestScore} / {DEMO_PULSE_ANALYTICS.academicAnalysis.maxMarks}
                </div>
                <span className="text-[10px] text-gray-500">3 students scored 100%</span>
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-gray-200">
                <span className="text-[11px] text-gray-500 font-medium">Lowest Score</span>
                <div className="text-xl font-bold text-rose-600 mt-0.5">
                  {DEMO_PULSE_ANALYTICS.academicAnalysis.lowestScore} / {DEMO_PULSE_ANALYTICS.academicAnalysis.maxMarks}
                </div>
                <span className="text-[10px] text-rose-700">Flagged for revision clinic</span>
              </div>
              <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-gray-200">
                <span className="text-[11px] text-gray-500 font-medium">Passing Threshold (≥60%)</span>
                <div className="text-xl font-bold text-blue-600 mt-0.5">92.8%</div>
                <span className="text-[10px] text-blue-700">39 of 42 passed</span>
              </div>
            </div>

            {/* Question-Level Item Analysis Table */}
            <h4 className="text-xs font-bold text-gray-800 mb-2">Question Item Analysis</h4>
            <div className="overflow-x-auto rounded-2xl border border-gray-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F8F9FE] text-gray-600 border-b border-gray-200 font-bold">
                  <tr>
                    <th className="p-3">Question Prompt</th>
                    <th className="p-3">Difficulty</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Marks</th>
                    <th className="p-3">Accuracy Rate</th>
                    <th className="p-3">Discrimination</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {DEMO_PULSE_ANALYTICS.academicAnalysis.itemAnalysis.map((item, i) => (
                    <tr key={item.questionId} className="hover:bg-gray-50 transition-colors">
                      <td className="p-3 font-medium text-gray-900 max-w-md">
                        {item.prompt}
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.difficulty === 'Easy'
                              ? 'bg-emerald-100 text-emerald-800'
                              : item.difficulty === 'Medium'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {item.difficulty}
                        </span>
                      </td>
                      <td className="p-3 uppercase text-gray-500 font-semibold">{item.questionType}</td>
                      <td className="p-3 font-semibold">{item.marks} M</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900">{item.accuracyRate}%</span>
                          <div className="w-16 h-1.5 rounded-full bg-gray-200 overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${item.accuracyRate}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            item.discriminationIndex === 'High'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {item.discriminationIndex}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* PART 2: CLASSROOM FEEDBACK ANALYTICS */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">
                    Category B: Classroom Feedback Analytics
                  </h3>
                  <p className="text-xs text-gray-500">
                    Aggregated lecture delivery insights. Individual student responses are strictly anonymized.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-sky-50 text-sky-700 font-semibold text-xs border border-sky-200 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> 100% Anonymized
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Lecture Pace Distribution */}
              <div className="p-4 rounded-2xl bg-sky-50/50 border border-sky-100">
                <h4 className="text-xs font-bold text-sky-900 mb-3">
                  Perceived Lecture Pace Distribution
                </h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-emerald-700">Just Right (Target Zone)</span>
                      <span>{DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.justRightPct}%</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-gray-200 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.justRightPct}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-amber-700">Too Fast (Need slower whiteboard tracing)</span>
                      <span>{DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.tooFastPct}%</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-gray-200 overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full"
                        style={{ width: `${DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.tooFastPct}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-blue-700">Too Slow (Foundational slides)</span>
                      <span>{DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.tooSlowPct}%</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-gray-200 overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${DEMO_PULSE_ANALYTICS.classroomFeedback.paceDistribution.tooSlowPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Teaching Delivery Ratings */}
              <div className="p-4 rounded-2xl bg-gray-50 border border-gray-200 flex flex-col justify-between">
                <h4 className="text-xs font-bold text-gray-900 mb-2">Teaching Delivery Parameters</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs p-2 bg-white rounded-xl border border-gray-100">
                    <span className="font-medium text-gray-700">Clarity of Algorithmic Explanations</span>
                    <span className="font-bold text-purple-700 text-sm">
                      {DEMO_PULSE_ANALYTICS.classroomFeedback.averageClarityRating} / 5.0
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs p-2 bg-white rounded-xl border border-gray-100">
                    <span className="font-medium text-gray-700">Hands-on Live Coding & Debugging</span>
                    <span className="font-bold text-purple-700 text-sm">
                      {DEMO_PULSE_ANALYTICS.classroomFeedback.averageHandsOnRating} / 5.0
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs p-2 bg-white rounded-xl border border-gray-100">
                    <span className="font-medium text-gray-700">Comfort Asking Questions in Lecture</span>
                    <span className="font-bold text-emerald-700 text-sm">
                      {DEMO_PULSE_ANALYTICS.classroomFeedback.askingQuestionsComfortPct}% Comfort
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-gray-500 mt-3 italic">
                  Privacy Notice: Individual responses are irreversibly aggregated; no faculty member can view individual feedback rows.
                </p>
              </div>
            </div>
          </div>

          {/* PART 3: STUDENT WELLBEING INSIGHTS */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-sm">
                  3
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">
                    Category C: Student Wellbeing & Academic Pressure Insights
                  </h3>
                  <p className="text-xs text-gray-500">
                    Academic motivation, perceived workload pressure, and proactive teaching interventions.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-rose-50 text-rose-700 font-semibold text-xs border border-rose-200">
                Non-diagnostic Phrasing
              </span>
            </div>

            {/* Wellbeing Meters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
              <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-200">
                <span className="text-xs text-purple-900 font-bold block mb-1">
                  Cohort Learning Motivation
                </span>
                <div className="text-2xl font-bold text-purple-700">
                  {DEMO_PULSE_ANALYTICS.wellbeingInsights.cohortMotivationIndex}%
                </div>
                <span className="text-[11px] text-purple-800">High curiosity & engagement</span>
              </div>

              <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200">
                <span className="text-xs text-amber-900 font-bold block mb-1">
                  Elevated Academic Pressure
                </span>
                <div className="text-2xl font-bold text-amber-700">
                  {DEMO_PULSE_ANALYTICS.wellbeingInsights.highPressureStudentPct}%
                </div>
                <span className="text-[11px] text-amber-800">14 of 42 cite exam anxiety</span>
              </div>

              <div className="p-4 rounded-2xl bg-blue-50/60 border border-blue-200">
                <span className="text-xs text-blue-900 font-bold block mb-1">
                  Midterm Exam Confidence
                </span>
                <div className="text-2xl font-bold text-blue-700">
                  {DEMO_PULSE_ANALYTICS.wellbeingInsights.examConfidenceIndex}%
                </div>
                <span className="text-[11px] text-blue-800">Moderate preparation readiness</span>
              </div>
            </div>

            {/* Actionable Faculty Recommendations Card */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50/50 border border-purple-200">
              <div className="flex items-center gap-2 mb-2 text-purple-900 font-bold text-xs">
                <Lightbulb className="w-4 h-4 text-purple-600" />
                Actionable Teaching Recommendations (Generated from Pulse Data)
              </div>
              <ul className="space-y-2">
                {DEMO_PULSE_ANALYTICS.wellbeingInsights.actionableRecommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-1.5 shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* DESCRIPTIVE SUBMISSION REVIEW MODAL / DRAWER */}
      {gradingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-xl border border-gray-200 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div>
                <h3 className="text-base font-bold text-gray-900">
                  Review Descriptive Submissions — Q5: DFS vs BFS
                </h3>
                <p className="text-xs text-gray-500">
                  Student: Asha Verma (B.Tech CSE 3rd Year) • Max Marks: 5.0
                </p>
              </div>
              <button
                type="button"
                onClick={() => setGradingModalOpen(false)}
                className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-700 block mb-1">
                Student Submitted Response:
              </label>
              <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-gray-200 text-xs text-gray-800 leading-relaxed font-sans">
                "DFS explores as deep as possible along each branch before backtracking and inherently relies on a Last-In-First-Out call stack or recursion. In contrast, BFS explores all the neighboring vertices at the present depth before moving on to vertices at the next depth level, using a First-In-First-Out Queue."
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">
                  Awarded Marks (out of 5.0):
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="5"
                  value={descriptiveGrade}
                  onChange={(e) => setDescriptiveGrade(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 text-xs font-bold focus:ring-2 focus:ring-purple-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">
                  Grading Rubric Benchmark:
                </label>
                <div className="text-[11px] text-gray-500 p-2 bg-gray-50 rounded-xl">
                  Stack vs Queue (2M), Level vs Depth Traversal (2M), Visited Set (1M).
                </div>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-700 block mb-1">
                Faculty Constructive Feedback:
              </label>
              <textarea
                rows={2}
                value={descriptiveFeedback}
                onChange={(e) => setDescriptiveFeedback(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-gray-300 text-xs focus:ring-2 focus:ring-purple-400 focus:outline-none font-sans"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setGradingModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 hover:bg-gray-100 cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setGradingModalOpen(false)
                  addToast(
                    'Marks & Feedback Saved! 📝',
                    `Awarded ${descriptiveGrade}/5.0 to Asha Verma for DFS vs BFS.`,
                    'success'
                  )
                }}
                className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-bold hover:bg-purple-700 transition-colors cursor-pointer shadow-2xs"
              >
                Save Evaluation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
