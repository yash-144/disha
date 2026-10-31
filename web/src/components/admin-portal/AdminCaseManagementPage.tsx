import React, { useState } from 'react'
import {
  FolderKanban,
  Search,
  Filter,
  User,
  AlertTriangle,
  Clock,
  CheckCircle2,
  MoreVertical,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  X,
  History,
  Edit3,
  Check,
} from 'lucide-react'
import { INITIAL_CASES, CaseRecord } from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminCaseManagementPage() {
  const { addToast } = useApp()
  const [cases, setCases] = useState<CaseRecord[]>(INITIAL_CASES)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [domainFilter, setDomainFilter] = useState('all')
  const [selectedCase, setSelectedCase] = useState<CaseRecord | null>(null)

  // Administrative Action Modals
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false)
  const [isReopenModalOpen, setIsReopenModalOpen] = useState(false)
  const [isReassignModalOpen, setIsReassignModalOpen] = useState(false)

  // Override Form State
  const [overrideTargetState, setOverrideTargetState] = useState<CaseRecord['state']>('support_in_progress')
  const [reasonCode, setReasonCode] = useState('ADMIN_INTERVENTION_OVERRIDE')
  const [rationale, setRationale] = useState('')

  // Reassign Form State
  const [newOwner, setNewOwner] = useState('Dr. Rao (Counsellor)')

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      !searchQuery ||
      c.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.caseNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.interventionLabel.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && c.state !== 'closed') ||
      (statusFilter === 'escalated' && c.isEscalated) ||
      c.state === statusFilter

    const matchesDomain = domainFilter === 'all' || c.domain === domainFilter

    return matchesSearch && matchesStatus && matchesDomain
  })

  // Administrative Override Handler (FR-CASE-06)
  const handleExecuteOverride = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCase) return
    if (!rationale.trim()) {
      addToast('Rationale Required', 'Administrative override requires documented rationale for the audit trail.', 'info')
      return
    }

    setCases((prev) =>
      prev.map((c) => {
        if (c.id === selectedCase.id) {
          return {
            ...c,
            state: overrideTargetState,
            version: c.version + 1,
            isEscalated: overrideTargetState === 'escalated',
            lastAction: `Administrative override: Moved to ${overrideTargetState.replace('_', ' ')} (${reasonCode})`,
          }
        }
        return c
      })
    )

    setIsOverrideModalOpen(false)
    setRationale('')
    addToast('Override Executed', `Case ${selectedCase.caseNumber} transitioned with append-only audit entry.`, 'success')
  }

  // Administrative Reopen Handler (FR-CASE-06)
  const handleExecuteReopen = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCase) return

    setCases((prev) =>
      prev.map((c) => {
        if (c.id === selectedCase.id) {
          return {
            ...c,
            state: 'reopened',
            version: c.version + 1,
            lastAction: 'Reopened by Administrator with follow-up action plan',
          }
        }
        return c
      })
    )

    setIsReopenModalOpen(false)
    addToast('Case Reopened', `Case ${selectedCase.caseNumber} cycle reopened successfully.`, 'success')
  }

  // Administrative Reassign Handler (FR-CASE-02)
  const handleExecuteReassign = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCase) return

    setCases((prev) =>
      prev.map((c) => {
        if (c.id === selectedCase.id) {
          return {
            ...c,
            primaryOwnerName: newOwner,
            version: c.version + 1,
            lastAction: `Reassigned to ${newOwner} by Administrator`,
          }
        }
        return c
      })
    )

    setIsReassignModalOpen(false)
    addToast('Primary Owner Reassigned', `Case ${selectedCase.caseNumber} assigned to ${newOwner}.`, 'success')
  }

  const getStateBadge = (state: CaseRecord['state']) => {
    switch (state) {
      case 'support_in_progress':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">In Progress</span>
      case 'escalated':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Escalated</span>
      case 'closed':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Closed</span>
      case 'reopened':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Reopened</span>
      case 'assigned':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">Assigned</span>
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 text-gray-700">{state}</span>
    }
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. WORKBENCH HEADER & SUMMARY */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
            <FolderKanban className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Administrative Case Management Workbench
            </h2>
            <p className="text-xs text-[#717E95]">
              Cross-departmental case oversight, administrative overrides, and SLA escalation governance
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full font-semibold">
            Total Cases: {cases.length}
          </span>
          <span className="text-xs bg-rose-50 text-rose-700 border border-rose-200 px-3 py-1.5 rounded-full font-bold">
            Escalations: {cases.filter((c) => c.isEscalated).length}
          </span>
        </div>
      </section>

      {/* 2. SEARCH & FILTER TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by student name, case reference (CASE-...) or intervention..."
            className="w-full text-xs pl-9 pr-4 py-2.5 bg-white rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200 shadow-2xs"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: 'all', label: 'All Cases' },
            { id: 'active', label: 'Active (Open)' },
            { id: 'escalated', label: 'Escalated SLA' },
            { id: 'closed', label: 'Closed' },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setStatusFilter(f.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition cursor-pointer whitespace-nowrap ${
                statusFilter === f.id
                  ? 'bg-[#1E2433] text-white shadow-2xs'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. CASE WORKBENCH TABLE */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-gray-100 bg-[#FAFBFD] text-gray-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3.5 px-4">Case Reference</th>
                <th className="py-3.5 px-4">Student &amp; Cohort</th>
                <th className="py-3.5 px-4">Intervention Protocol</th>
                <th className="py-3.5 px-4">Domain</th>
                <th className="py-3.5 px-4">Primary Owner</th>
                <th className="py-3.5 px-4">Due Date</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredCases.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50/70 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-[#1E2433]">
                    {c.caseNumber}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-bold text-[#1E2433] block">{c.studentName}</span>
                    <span className="text-[11px] text-gray-400">{c.cohort}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-gray-800 block truncate max-w-[200px]">
                      {c.interventionLabel}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Tasks: {c.tasksCount.completed}/{c.tasksCount.total} done
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="capitalize font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-md">
                      {c.domain}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-gray-800 block">{c.primaryOwnerName}</span>
                    <span className="text-[10px] text-gray-400">{c.primaryOwnerRole}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`font-semibold ${c.isOverdue ? 'text-rose-600 font-bold' : 'text-gray-700'}`}>
                      {c.dueAt}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {getStateBadge(c.state)}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCase(c)
                          setIsOverrideModalOpen(true)
                        }}
                        className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-purple-50 text-purple-700 hover:bg-purple-100 transition cursor-pointer"
                        title="Administrative Override (FR-CASE-06)"
                      >
                        Override
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCase(c)
                          setIsReassignModalOpen(true)
                        }}
                        className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-gray-100 text-gray-700 hover:bg-gray-200 transition cursor-pointer"
                        title="Reassign Primary Owner"
                      >
                        Reassign
                      </button>
                      {c.state === 'closed' && (
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedCase(c)
                            setIsReopenModalOpen(true)
                          }}
                          className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-amber-50 text-amber-700 hover:bg-amber-100 transition cursor-pointer"
                        >
                          Reopen
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ADMINISTRATIVE OVERRIDE MODAL (FR-CASE-06) */}
      {isOverrideModalOpen && selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Administrative Case Override</h3>
                  <p className="text-[11px] text-[#717E95]">{selectedCase.caseNumber} (v{selectedCase.version})</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsOverrideModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleExecuteOverride} className="p-5 flex flex-col gap-4 text-xs">
              <div className="p-3 bg-purple-50 rounded-xl text-purple-900 text-[11px] leading-relaxed border border-purple-100">
                <strong>Audit Compliance:</strong> Case overrides record prior state and reason codes into an append-only audit trail with version increments (NFR-CONC-01).
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Target State</label>
                <select
                  value={overrideTargetState}
                  onChange={(e) => setOverrideTargetState(e.target.value as any)}
                  className="p-2.5 rounded-xl border border-gray-200 bg-white"
                >
                  <option value="support_in_progress">Support in Progress</option>
                  <option value="escalated">Escalated to Supervisor</option>
                  <option value="closed">Direct Closure (Resolved)</option>
                  <option value="assigned">Re-assigned for Intake</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Reason Code</label>
                <select
                  value={reasonCode}
                  onChange={(e) => setReasonCode(e.target.value)}
                  className="p-2.5 rounded-xl border border-gray-200 bg-white"
                >
                  <option value="ADMIN_INTERVENTION_OVERRIDE">ADMIN_INTERVENTION_OVERRIDE</option>
                  <option value="SUPERVISOR_DIRECTIVE">SUPERVISOR_DIRECTIVE</option>
                  <option value="STUDENT_STATUS_RESOLVED">STUDENT_STATUS_RESOLVED</option>
                  <option value="WELFARE_COMMITTEE_DECISION">WELFARE_COMMITTEE_DECISION</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Documented Rationale *</label>
                <textarea
                  rows={3}
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  placeholder="Detail why this administrative override is required and cite any supporting institutional committee decisions..."
                  className="p-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="p-4 bg-gray-50 border-t border-gray-100 -mx-5 -mb-5 mt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsOverrideModalOpen(false)}
                  className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-full font-bold text-white bg-purple-700 hover:bg-purple-800 transition"
                >
                  Confirm Override
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REASSIGN MODAL */}
      {isReassignModalOpen && selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Reassign Primary Owner</h3>
                  <p className="text-[11px] text-[#717E95]">{selectedCase.caseNumber}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsReassignModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleExecuteReassign} className="p-5 flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Current Primary Owner</label>
                <input
                  type="text"
                  disabled
                  value={`${selectedCase.primaryOwnerName} (${selectedCase.primaryOwnerRole})`}
                  className="p-2.5 rounded-xl border border-gray-200 bg-gray-50 text-gray-600"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Assign to Staff Lead</label>
                <select
                  value={newOwner}
                  onChange={(e) => setNewOwner(e.target.value)}
                  className="p-2.5 rounded-xl border border-gray-200 bg-white"
                >
                  <option value="Prof. Sharma (Faculty Mentor)">Prof. Sharma (Faculty Mentor)</option>
                  <option value="Dr. Rao (Senior Counsellor)">Dr. Rao (Senior Counsellor)</option>
                  <option value="Meera K. (Wellbeing Specialist)">Meera K. (Wellbeing Specialist)</option>
                  <option value="Dr. Mukherjee (HOD Mechanical)">Dr. Mukherjee (HOD Mechanical)</option>
                </select>
              </div>

              <div className="p-4 bg-gray-50 border-t border-gray-100 -mx-5 -mb-5 mt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsReassignModalOpen(false)}
                  className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-full font-bold text-white bg-[#1E2433] hover:bg-[#2C3549] transition"
                >
                  Save Assignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

