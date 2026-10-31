import React, { useState } from 'react'
import {
  GraduationCap,
  Search,
  Filter,
  UserCheck,
  UserX,
  Plus,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  ChevronRight,
  X,
  ExternalLink,
} from 'lucide-react'
import { INITIAL_STUDENTS, StudentRecord } from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminStudentDirectoryPage() {
  const { addToast } = useApp()
  const [students, setStudents] = useState<StudentRecord[]>(INITIAL_STUDENTS)
  const [searchQuery, setSearchQuery] = useState('')
  const [cohortFilter, setCohortFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Selected student drawer/modal
  const [selectedStudent, setSelectedStudent] = useState<StudentRecord | null>(null)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [importCounts, setImportCounts] = useState<{ accepted: number; duplicates: number; rejected: number } | null>(null)

  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      !searchQuery ||
      s.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.externalRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.cohortCode.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCohort = cohortFilter === 'all' || s.cohortCode === cohortFilter
    const matchesStatus = statusFilter === 'all' || s.enrollmentStatus === statusFilter

    return matchesSearch && matchesCohort && matchesStatus
  })

  // Verify Account Link action (FR-TEN-04: admin-verified link, no email-prefix guessing)
  const handleVerifyAccountLink = (studentId: string) => {
    setStudents((prev) =>
      prev.map((s) => {
        if (s.id === studentId) {
          return {
            ...s,
            accountLinked: true,
            linkedUserId: `usr-verified-${studentId}`,
          }
        }
        return s
      })
    )
    if (selectedStudent && selectedStudent.id === studentId) {
      setSelectedStudent({
        ...selectedStudent,
        accountLinked: true,
        linkedUserId: `usr-verified-${studentId}`,
      })
    }
    addToast('Account Link Verified', 'Verified user account explicitly linked to student identity record (FR-TEN-04).', 'success')
  }

  // Toggle enrolment status
  const handleToggleStatus = (studentId: string, newStatus: StudentRecord['enrollmentStatus']) => {
    setStudents((prev) =>
      prev.map((s) => (s.id === studentId ? { ...s, enrollmentStatus: newStatus } : s))
    )
    if (selectedStudent && selectedStudent.id === studentId) {
      setSelectedStudent({ ...selectedStudent, enrollmentStatus: newStatus })
    }
    addToast('Enrolment Status Updated', `Student status changed to ${newStatus}.`, 'info')
  }

  // Simulate Batch Import (FR-OBS-01, FR-OBS-05)
  const handleSimulateImport = () => {
    setImportCounts({ accepted: 142, duplicates: 8, rejected: 0 })
    addToast('Batch Ingest Completed', 'Imported 142 student records, 8 duplicates ignored (FR-OBS-05).', 'success')
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. DIRECTORY HEADER & ACTIONS */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Campus Student Directory &amp; Roster
            </h2>
            <p className="text-xs text-[#717E95]">
              Manage enrolled student records, cohort associations, and admin-verified account linking (FR-TEN-04)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setImportCounts(null)
              setIsImportModalOpen(true)
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition shadow-2xs cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-purple-600" />
            <span>Batch Import (CSV)</span>
          </button>
        </div>
      </section>

      {/* 2. SEARCH & FILTER TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by student name, external reference (STU-...) or cohort..."
            className="w-full text-xs pl-9 pr-4 py-2.5 bg-white rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200 shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Cohort Select */}
          <select
            value={cohortFilter}
            onChange={(e) => setCohortFilter(e.target.value)}
            className="text-xs py-2 px-3 bg-white rounded-full border border-gray-200 focus:outline-none shadow-2xs text-gray-700 font-medium"
          >
            <option value="all">All Cohorts</option>
            <option value="2025-CS">2025-CS</option>
            <option value="2024-ECE">2024-ECE</option>
            <option value="2025-MECH">2025-MECH</option>
            <option value="2025-EE">2025-EE</option>
          </select>

          {/* Enrolment Status Select */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs py-2 px-3 bg-white rounded-full border border-gray-200 focus:outline-none shadow-2xs text-gray-700 font-medium"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Enrolment</option>
            <option value="inactive">Inactive</option>
            <option value="graduated">Graduated</option>
          </select>
        </div>
      </div>

      {/* 3. ROSTER TABLE */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-gray-100 bg-[#FAFBFD] text-gray-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3.5 px-4">Student ID (External Ref)</th>
                <th className="py-3.5 px-4">Display Name</th>
                <th className="py-3.5 px-4">Cohort</th>
                <th className="py-3.5 px-4">Academic Avg</th>
                <th className="py-3.5 px-4">Account Linking</th>
                <th className="py-3.5 px-4">Enrolment Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredStudents.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50/70 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-[#1E2433]">
                    {s.externalRef}
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-gray-800">
                    {s.displayName}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-mono text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md font-semibold">
                      {s.cohortCode}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-gray-700">
                    {s.academicAverage}%
                  </td>
                  <td className="py-3.5 px-4">
                    {s.accountLinked ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Verified Link</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100">
                        <AlertCircle className="w-3 h-3 text-amber-600" />
                        <span>Unlinked User</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                      s.enrollmentStatus === 'active'
                        ? 'bg-emerald-50 text-emerald-700'
                        : s.enrollmentStatus === 'graduated'
                        ? 'bg-blue-50 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {s.enrollmentStatus}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => setSelectedStudent(s)}
                      className="px-3 py-1 rounded-full text-xs font-semibold bg-[#1E2433] hover:bg-[#2C3549] text-white transition cursor-pointer"
                    >
                      Manage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* STUDENT DETAILS & VERIFICATION MODAL */}
      {selectedStudent && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">{selectedStudent.displayName}</h3>
                  <p className="text-[11px] text-[#717E95]">{selectedStudent.externalRef} • {selectedStudent.cohortCode}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedStudent(null)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4 text-xs">
              {/* Account Linking Status per FR-TEN-04 */}
              <div className="p-3.5 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#1E2433]">Account Linking Status (FR-TEN-04)</span>
                  {selectedStudent.accountLinked ? (
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Active Link
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      Pending Verification
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#64748B] leading-relaxed">
                  Student accounts must be verified by an administrator before granting student portal access. Similarity matching by email prefix is strictly prohibited.
                </p>
                {!selectedStudent.accountLinked && (
                  <button
                    type="button"
                    onClick={() => handleVerifyAccountLink(selectedStudent.id)}
                    className="mt-1 self-start px-3 py-1.5 rounded-full bg-purple-700 text-white font-bold hover:bg-purple-800 transition cursor-pointer"
                  >
                    Verify &amp; Link Account
                  </button>
                )}
              </div>

              {/* Processing Authorizations / Purpose Keys */}
              <div className="flex flex-col gap-1.5">
                <span className="font-bold text-[#1E2433]">Processing Authorizations</span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  {[
                    { key: 'early_warning', label: 'Early Warning Evaluation', status: 'Active' },
                    { key: 'counselling_referral', label: 'Counselling Support Referral', status: 'Active' },
                    { key: 'rewards_points', label: 'Wellbeing Points & Rewards', status: 'Active' },
                    { key: 'academic_support', label: 'Department Academic Pacing', status: 'Active' },
                  ].map((auth) => (
                    <div key={auth.key} className="p-2.5 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between">
                      <span className="text-gray-700">{auth.label}</span>
                      <span className="text-emerald-600 font-bold">✓</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status Controls */}
              <div className="flex flex-col gap-1.5">
                <span className="font-bold text-[#1E2433]">Update Enrolment Status</span>
                <div className="flex items-center gap-2">
                  {(['active', 'inactive', 'graduated'] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => handleToggleStatus(selectedStudent.id, st)}
                      className={`px-3 py-1.5 rounded-xl capitalize font-semibold border transition cursor-pointer ${
                        selectedStudent.enrollmentStatus === st
                          ? 'bg-[#1E2433] text-white border-[#1E2433]'
                          : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 border-t border-gray-100 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedStudent(null)}
                className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BATCH IMPORT MODAL (FR-OBS-02, FR-OBS-05) */}
      {isImportModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Batch Roster Import</h3>
                  <p className="text-[11px] text-[#717E95]">CSV / JSON Observation Ingestion</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsImportModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4 text-xs">
              <div className="border-2 border-dashed border-gray-200 rounded-2xl p-6 text-center hover:border-purple-300 transition cursor-pointer">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="font-semibold text-gray-700">Drop student roster CSV here</p>
                <p className="text-[11px] text-gray-400 mt-0.5">Supports: external_ref, display_name, cohort_code, enrollment_status</p>
              </div>

              {importCounts && (
                <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-emerald-950 flex flex-col gap-1 text-[11px]">
                  <span className="font-bold">Import Batch Results (FR-OBS-05):</span>
                  <span>• Accepted Rows: {importCounts.accepted}</span>
                  <span>• Duplicate Records Skipped: {importCounts.duplicates}</span>
                  <span>• Rejected Rows: {importCounts.rejected}</span>
                </div>
              )}
            </div>

            <div className="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-2 text-xs">
              <button
                type="button"
                onClick={() => setIsImportModalOpen(false)}
                className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleSimulateImport}
                className="px-5 py-2 rounded-full font-bold text-white bg-purple-700 hover:bg-purple-800 transition"
              >
                Process Ingestion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

