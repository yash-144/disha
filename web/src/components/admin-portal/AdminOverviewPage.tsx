import React, { useState } from 'react'
import {
  Users,
  ShieldAlert,
  Clock,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  FileCheck,
  Award,
  Layers,
  Sparkles,
  ExternalLink,
  RefreshCw,
  Sliders,
  ChevronRight,
  UserCheck,
} from 'lucide-react'
import {
  INITIAL_CASES,
  INITIAL_STUDENTS,
  INITIAL_DOCUMENTS,
  INITIAL_REDEMPTIONS,
} from './adminData'
import { useApp } from '../../context/AppContext'

interface AdminOverviewPageProps {
  onNavigateTab: (tab: string) => void
}

export function AdminOverviewPage({ onNavigateTab }: AdminOverviewPageProps) {
  const { addToast } = useApp()
  const [isRefreshing, setIsRefreshing] = useState(false)

  const activeStudentsCount = INITIAL_STUDENTS.filter((s) => s.enrollmentStatus === 'active').length
  const activeCases = INITIAL_CASES.filter((c) => c.state !== 'closed')
  const overdueCases = INITIAL_CASES.filter((c) => c.isOverdue || c.isEscalated)
  const pendingRedemptions = INITIAL_REDEMPTIONS.filter((r) => r.status === 'requested')
  const anchoredDocs = INITIAL_DOCUMENTS.filter((d) => d.status === 'anchored')

  const handleRefreshPulse = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setIsRefreshing(false)
      addToast('System Synchronized', 'Institutional operational state updated from database.', 'info')
    }, 600)
  }

  return (
    <div className="flex flex-col gap-5 font-sans select-none">
      {/* 1. TOP INSTITUTIONAL COMMAND CENTRE METRICS */}
      <section aria-label="Institutional KPIs" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* KPI 1: Active Population */}
        <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col justify-between hover:shadow-xs transition">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
              98.2% Enrolled
            </span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-black tracking-tight text-[#1E2433]">1,420</span>
            <p className="text-xs font-semibold text-[#64748B] mt-0.5">
              Authorized Student Population
            </p>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-[#717E95]">
            <span>Active Roster: {activeStudentsCount * 284}</span>
            <span className="font-semibold text-blue-600">Apex Campus</span>
          </div>
        </div>

        {/* KPI 2: Active Support Cases */}
        <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col justify-between hover:shadow-xs transition">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-[#FEF9C3] text-[#A16207] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100">
              12 High Priority
            </span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-black tracking-tight text-[#1E2433]">{activeCases.length + 34}</span>
            <p className="text-xs font-semibold text-[#64748B] mt-0.5">
              Active Support Cases
            </p>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-[#717E95]">
            <span>Intervention SLA: 94.6%</span>
            <button
              type="button"
              onClick={() => onNavigateTab('case-management')}
              className="font-bold text-[#6366F1] hover:underline cursor-pointer"
            >
              Workbench →
            </button>
          </div>
        </div>

        {/* KPI 3: Overdue & Escalated Cases */}
        <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col justify-between hover:shadow-xs transition">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-[#FEE2E2] text-[#DC2626] flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-100">
              Action Required
            </span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-black tracking-tight text-[#1E2433]">{overdueCases.length}</span>
            <p className="text-xs font-semibold text-[#64748B] mt-0.5">
              Escalated Deadlines
            </p>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-[#717E95]">
            <span>Automated Worker: Active</span>
            <span className="font-semibold text-rose-600">Supervisor SLA</span>
          </div>
        </div>

        {/* KPI 4: Document Integrity & Anchoring */}
        <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col justify-between hover:shadow-xs transition">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-[#ECFDF5] text-[#059669] flex items-center justify-center">
              <FileCheck className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
              100% Cryptographic Match
            </span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-black tracking-tight text-[#1E2433]">{anchoredDocs.length + 18}</span>
            <p className="text-xs font-semibold text-[#64748B] mt-0.5">
              Anchored Official Attestations
            </p>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-[#717E95]">
            <span>Chain: Base Sepolia</span>
            <button
              type="button"
              onClick={() => onNavigateTab('document-integrity')}
              className="font-bold text-emerald-600 hover:underline cursor-pointer"
            >
              Verify →
            </button>
          </div>
        </div>
      </section>

      {/* 2. MAIN WORKSPACE: OPERATIONAL PULSE & PENDING ACTIONS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* LEFT: Institutional Domain Distribution & Case Pipeline (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* Section A: Institutional Early Warning Distribution */}
          <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 md:p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-gray-100">
              <div>
                <h3 className="text-base font-bold text-[#1E2433] tracking-tight">
                  Institutional Signal Detection by Domain
                </h3>
                <p className="text-xs text-[#717E95] mt-0.5">
                  Aggregated review of observation domains processed by Policy v2.4 (Deterministic Evaluation)
                </p>
              </div>
              <button
                type="button"
                onClick={handleRefreshPulse}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition cursor-pointer self-start sm:self-center"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-purple-600' : 'text-gray-500'}`} />
                <span>Sync State</span>
              </button>
            </div>

            {/* Domain Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mt-4">
              {[
                { domain: 'Attendance', alerts: 24, percent: 78, color: 'bg-amber-500', bg: 'bg-amber-50' },
                { domain: 'Academic', alerts: 18, percent: 84, color: 'bg-blue-500', bg: 'bg-blue-50' },
                { domain: 'Participation', alerts: 9, percent: 91, color: 'bg-purple-500', bg: 'bg-purple-50' },
                { domain: 'Skills', alerts: 6, percent: 94, color: 'bg-emerald-500', bg: 'bg-emerald-50' },
                { domain: 'Faculty Feedback', alerts: 12, percent: 81, color: 'bg-indigo-500', bg: 'bg-indigo-50' },
              ].map((d) => (
                <div key={d.domain} className={`p-3 rounded-2xl ${d.bg} border border-black/5 flex flex-col justify-between`}>
                  <span className="text-xs font-semibold text-gray-700 truncate">{d.domain}</span>
                  <div className="my-2">
                    <span className="text-xl font-bold text-[#1E2433]">{d.alerts}</span>
                    <span className="text-[10px] text-gray-500 ml-1">signals</span>
                  </div>
                  <div>
                    <div className="w-full bg-black/10 rounded-full h-1.5 overflow-hidden">
                      <div className={`h-full ${d.color} rounded-full`} style={{ width: `${d.percent}%` }} />
                    </div>
                    <span className="text-[10px] font-medium text-gray-500 mt-1 block">Health: {d.percent}%</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Principles Reminder Banner per Blueprint §1 ("No Alert Without Action") */}
            <div className="mt-4 p-3.5 rounded-2xl bg-gradient-to-r from-purple-50 to-indigo-50/60 border border-purple-100 flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
                <span className="text-purple-950 font-medium">
                  <strong>Operating Invariant:</strong> Every accepted early warning signal leads to an owned human decision with a strict completion deadline.
                </span>
              </div>
              <button
                type="button"
                onClick={() => onNavigateTab('interventions')}
                className="text-xs font-bold text-purple-700 hover:text-purple-900 shrink-0 cursor-pointer"
              >
                Rule Policies →
              </button>
            </div>
          </div>

          {/* Section B: Active Cases Requiring Governance */}
          <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 md:p-6">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div>
                <h3 className="text-base font-bold text-[#1E2433] tracking-tight">
                  High-Priority Case Governance
                </h3>
                <p className="text-xs text-[#717E95] mt-0.5">
                  Multi-departmental intervention cases requiring administrative review or deadline monitoring
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigateTab('case-management')}
                className="text-xs font-bold text-[#6366F1] hover:underline cursor-pointer"
              >
                View All Cases
              </button>
            </div>

            <div className="divide-y divide-gray-100 mt-2">
              {INITIAL_CASES.map((c) => (
                <div key={c.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-gray-50/50 rounded-xl px-2 transition">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                      c.isEscalated
                        ? 'bg-rose-100 text-rose-700'
                        : c.state === 'closed'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-purple-100 text-purple-700'
                    }`}>
                      {c.isEscalated ? <AlertTriangle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#1E2433]">{c.caseNumber}</span>
                        <span className="text-xs text-gray-500">• {c.studentName} ({c.cohort})</span>
                        {c.isEscalated && (
                          <span className="text-[10px] bg-rose-50 text-rose-700 font-bold px-2 py-0.2 rounded-full border border-rose-200">
                            Escalated
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#64748B] mt-0.5">
                        Intervention: {c.interventionLabel} • Primary Owner: {c.primaryOwnerName}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 self-end sm:self-center">
                    <span className="text-[11px] text-gray-500 font-medium">Due: {c.dueAt}</span>
                    <button
                      type="button"
                      onClick={() => onNavigateTab('case-management')}
                      className="px-3 py-1 rounded-full text-xs font-semibold bg-[#1E2433] text-white hover:bg-[#2C3549] transition cursor-pointer"
                    >
                      Inspect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: Pending Administrative Actions & Quick Shortcuts (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Card A: Pending Administrative Actions */}
          <div className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5">
            <h3 className="text-base font-bold text-[#1E2433] tracking-tight mb-3">
              Pending Actions
            </h3>

            <div className="flex flex-col gap-2.5">
              {/* Action 1: Counsellor Approval */}
              <div className="p-3 rounded-2xl bg-purple-50/80 border border-purple-100/80 flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-purple-200/80 text-purple-800 flex items-center justify-center shrink-0 mt-0.5">
                  <UserCheck className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-bold text-purple-950 block">Counsellor Verification</span>
                  <p className="text-[11px] text-purple-800 mt-0.5">
                    1 credential awaiting license attestation approval (FR-COU-01).
                  </p>
                  <button
                    type="button"
                    onClick={() => addToast('Credential Verified', 'Dr. Rao profile verification approved.', 'success')}
                    className="mt-2 px-2.5 py-1 rounded-md bg-purple-700 text-white text-[11px] font-bold hover:bg-purple-800 transition cursor-pointer"
                  >
                    Approve Profile
                  </button>
                </div>
              </div>

              {/* Action 2: Reward Redemptions Pending */}
              <div className="p-3 rounded-2xl bg-amber-50/80 border border-amber-100/80 flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-amber-200/80 text-amber-800 flex items-center justify-center shrink-0 mt-0.5">
                  <Award className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-bold text-amber-950 block">Pending Redemptions</span>
                  <p className="text-[11px] text-amber-800 mt-0.5">
                    {pendingRedemptions.length} student reward claims awaiting campus distribution.
                  </p>
                  <button
                    type="button"
                    onClick={() => onNavigateTab('reward-fulfilment')}
                    className="mt-2 px-2.5 py-1 rounded-md bg-amber-700 text-white text-[11px] font-bold hover:bg-amber-800 transition cursor-pointer"
                  >
                    Manage Rewards
                  </button>
                </div>
              </div>

              {/* Action 3: Roster Import */}
              <div className="p-3 rounded-2xl bg-blue-50/80 border border-blue-100/80 flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-blue-200/80 text-blue-800 flex items-center justify-center shrink-0 mt-0.5">
                  <Layers className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-bold text-blue-950 block">Roster Batch Sync</span>
                  <p className="text-[11px] text-blue-800 mt-0.5">
                    Semester 2 attendance & feedback feeds ready for ingest.
                  </p>
                  <button
                    type="button"
                    onClick={() => onNavigateTab('student-directory')}
                    className="mt-2 px-2.5 py-1 rounded-md bg-blue-700 text-white text-[11px] font-bold hover:bg-blue-800 transition cursor-pointer"
                  >
                    Batch Import
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Card B: Quick Navigation Hub */}
          <div className="bg-gradient-to-br from-[#1E2433] to-[#2C3549] text-white rounded-3xl p-5 shadow-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300">
              Institutional Navigation
            </h4>
            <p className="text-xs text-gray-300 mt-1 leading-relaxed">
              Access administrative workspaces configured for Apex University Campus.
            </p>

            <div className="flex flex-col gap-1.5 mt-4">
              {[
                { label: 'Institutional Analytics', tab: 'analytics' },
                { label: 'Interventions & Protocols', tab: 'interventions' },
                { label: 'Document Integrity Ledger', tab: 'document-integrity' },
                { label: 'Campus Review Schedule', tab: 'schedule' },
              ].map((item) => (
                <button
                  key={item.tab}
                  type="button"
                  onClick={() => onNavigateTab(item.tab)}
                  className="w-full flex items-center justify-between p-2 rounded-xl text-xs font-medium hover:bg-white/10 text-gray-200 hover:text-white transition cursor-pointer text-left"
                >
                  <span>{item.label}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

