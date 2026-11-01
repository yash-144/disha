import re

file_path = r'web\src\components\teacher-dashboard\TeacherAssessmentsPage.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
old_import = "  INITIAL_PULSE_ASSIGNMENTS,\n  DEMO_PULSE_ANALYTICS,\n  generateRandomizedPulseQuestions,\n} from '../student-portal/studentPulseData'"
new_import = "  INITIAL_PULSE_ASSIGNMENTS,\n  DEMO_PULSE_ANALYTICS,\n  generateRandomizedPulseQuestions,\n  DEMO_PEER_MENTOR_POOL,\n  PULSE_DEMO_SCENARIOS,\n} from '../student-portal/studentPulseData'"

content = content.replace(old_import, new_import)

# 2. Update activeSubTab state type
old_tab_state = "const [activeSubTab, setActiveSubTab] = useState<'list' | 'create' | 'analytics'>('list')"
new_tab_state = "const [activeSubTab, setActiveSubTab] = useState<'list' | 'create' | 'analytics' | 'interventions'>('list')"

content = content.replace(old_tab_state, new_tab_state)

# 3. Add tab button
old_button = """          <button
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
          </button>"""

new_button = """          <button
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
          <button
            type="button"
            onClick={() => setActiveSubTab('interventions')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'interventions'
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Users className="w-4 h-4" />
            Interventions & Mentors
          </button>"""

content = content.replace(old_button, new_button)

# 4. Add interventions subtab before gradingModalOpen
interventions_view = '''
      {/* 4. SUBTAB: INTERVENTIONS & PEER MENTORSHIP WORKSPACE */}
      {activeSubTab === 'interventions' && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-150">
          {/* Header Banner */}
          <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-br from-purple-50 via-indigo-50/40 to-blue-50 border border-purple-200/80 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-full bg-purple-200 text-purple-900 text-xs font-bold">
                  Intervention Engine
                </span>
                <span className="text-xs text-gray-500 font-medium">Operational Threshold: 60.0% (v1.0-operational)</span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-gray-900">
                Student Pulse Support & Mentorship Pipeline
              </h2>
              <p className="text-xs sm:text-sm text-gray-600 mt-1">
                Evaluates Academic, Feedback, and Wellbeing scores independently through the 8-row intervention matrix.
              </p>
            </div>

            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl border border-gray-200 shadow-2xs text-xs font-bold text-gray-700 shrink-0">
              <Users className="w-4 h-4 text-purple-600" />
              <span>3 Volunteer Mentors in Pool</span>
            </div>
          </div>

          {/* 8-Row Matrix Quick Reference */}
          <div className="bg-white rounded-3xl p-5 border border-gray-200 shadow-2xs">
            <h3 className="text-xs font-bold text-gray-900 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-600" />
              8-Row Deterministic Intervention Matrix (Threshold = 60%)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500 font-semibold bg-gray-50/60">
                    <th className="py-2.5 px-3 rounded-l-lg">Academic</th>
                    <th className="py-2.5 px-3">Classroom Feedback</th>
                    <th className="py-2.5 px-3">Student Wellbeing</th>
                    <th className="py-2.5 px-3 rounded-r-lg">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-medium">
                  <tr>
                    <td className="py-2 px-3 text-amber-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold text-[11px]">Peer Mentor Invitation</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-amber-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-rose-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold text-[11px] mr-1">Peer Mentor</span><span className="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold text-[11px]">Faculty Review</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-amber-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-purple-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold text-[11px] mr-1">Peer Mentor</span><span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-bold text-[11px]">Counsellor Offer</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-amber-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-rose-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-purple-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold text-[11px] mr-1">Peer Mentor</span><span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-bold text-[11px] mr-1">Counsellor Offer</span><span className="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold text-[11px]">Faculty Review</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-rose-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold text-[11px]">Faculty Review</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-purple-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-bold text-[11px]">Counsellor Offer</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-rose-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3 text-purple-700 font-bold">Low (&lt;60%)</td>
                    <td className="py-2 px-3"><span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-bold text-[11px] mr-1">Counsellor Offer</span><span className="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold text-[11px]">Faculty Review</span></td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-emerald-700">Good (≥60%)</td>
                    <td className="py-2 px-3 text-gray-400 italic">No intervention required</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Volunteer Peer Mentor Pool */}
          <div className="bg-white rounded-3xl p-5 border border-gray-200 shadow-2xs">
            <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-600" />
                Active Peer Mentor Pool (Volunteers)
              </span>
              <span className="text-xs font-semibold text-gray-500">Academic Support Only • No Wellbeing Data Access</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {DEMO_PEER_MENTOR_POOL.map((mentor) => (
                <div key={mentor.id} className="p-4 rounded-2xl bg-[#F8F9FE] border border-gray-200 flex flex-col justify-between gap-3">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-900">{mentor.studentName}</span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                        {mentor.availability}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-500 mt-0.5">GPA: {mentor.gpa} • {mentor.volunteerStatus}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {mentor.eligibleCourses.map((c) => (
                        <span key={c} className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="text-[11px] text-gray-600 flex items-center justify-between pt-2 border-t border-gray-200/60">
                    <span>Active Capacity:</span>
                    <span className="font-bold text-gray-900">{mentor.activeMenteesCount} / {mentor.maxCapacity} Mentees</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Interventions Table */}
          <div className="bg-white rounded-3xl p-5 border border-gray-200 shadow-2xs">
            <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-purple-600" />
                Evaluated Student Pulse Interventions (Recent)
              </span>
              <span className="text-xs font-medium text-purple-700">Deduplicated & Versioned</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500 font-semibold bg-gray-50/60">
                    <th className="py-2.5 px-3 rounded-l-lg">Case ID</th>
                    <th className="py-2.5 px-3">Course</th>
                    <th className="py-2.5 px-3">Scores (Acad / Feed / Well)</th>
                    <th className="py-2.5 px-3">Triggered Actions</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 rounded-r-lg">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr className="hover:bg-gray-50/50">
                    <td className="py-3 px-3 font-bold text-purple-900">INTV-CS201-081</td>
                    <td className="py-3 px-3 font-semibold text-gray-800">CS201</td>
                    <td className="py-3 px-3">
                      <span className="text-amber-700 font-bold">45%</span> / <span className="text-emerald-700 font-bold">82%</span> / <span className="text-emerald-700 font-bold">78%</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-bold text-[11px]">Peer Mentor (Arjun Singh)</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">CONNECTED</span>
                    </td>
                    <td className="py-3 px-3 text-gray-500">Today, 10:15</td>
                  </tr>
                  <tr className="hover:bg-gray-50/50">
                    <td className="py-3 px-3 font-bold text-purple-900">INTV-CS202-042</td>
                    <td className="py-3 px-3 font-semibold text-gray-800">CS202</td>
                    <td className="py-3 px-3">
                      <span className="text-emerald-700 font-bold">78%</span> / <span className="text-rose-700 font-bold">48%</span> / <span className="text-emerald-700 font-bold">75%</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold text-[11px]">Faculty Review (Pace Alert)</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold text-[10px]">REVIEW PENDING</span>
                    </td>
                    <td className="py-3 px-3 text-gray-500">Yesterday</td>
                  </tr>
                  <tr className="hover:bg-gray-50/50">
                    <td className="py-3 px-3 font-bold text-purple-900">INTV-CS201-079</td>
                    <td className="py-3 px-3 font-semibold text-gray-800">CS201</td>
                    <td className="py-3 px-3">
                      <span className="text-emerald-700 font-bold">85%</span> / <span className="text-emerald-700 font-bold">80%</span> / <span className="text-purple-700 font-bold">42%</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-bold text-[11px]">Counsellor Offer (Private)</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-bold text-[10px]">OFFER DISPATCHED</span>
                    </td>
                    <td className="py-3 px-3 text-gray-500">28 Oct, 2026</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
'''

modal_marker = "{/* DESCRIPTIVE SUBMISSION REVIEW MODAL / DRAWER */}"
content = content.replace(modal_marker, interventions_view + "\n      " + modal_marker)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("TeacherAssessmentsPage.tsx successfully updated!")

