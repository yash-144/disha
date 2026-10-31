import React, { useState } from 'react'
import {
  Bookmark,
  Shield,
  Layers,
  CheckCircle2,
  AlertCircle,
  CircleHelp,
  Bell,
  Plus,
  ArrowRight,
  Clock,
  Sparkles,
  FileCheck,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

interface ProtocolItem {
  id: string
  code: string
  title: string
  tier: 'Tier 1 Universal' | 'Tier 2 Targeted' | 'Tier 3 Intensive'
  triggerCriteria: string
  duration: string
  activeCases: number
  description: string
  tierColor: 'blue' | 'yellow' | 'purple'
}

const INSTITUTIONAL_PROTOCOLS: ProtocolItem[] = [
  {
    id: 'prot-1',
    code: 'PROT-ATT-01',
    title: 'Attendance Remediation & Makeup Lab',
    tier: 'Tier 2 Targeted',
    triggerCriteria: 'Attendance dips below 75% in consecutive 2-week cycle',
    duration: '2 – 3 Weeks',
    activeCases: 8,
    description: 'Structured 1-on-1 lab check-ins, mandatory missed practical lab hours, and faculty progress attestations.',
    tierColor: 'yellow',
  },
  {
    id: 'prot-2',
    code: 'PROT-ACAD-02',
    title: 'Peer Tutoring & Conceptual Mentorship',
    tier: 'Tier 1 Universal',
    triggerCriteria: 'Quiz score average < 70% or missed assignment submission',
    duration: '3 – 4 Weeks',
    activeCases: 11,
    description: 'Pairing with senior teaching assistant for targeted algorithm reviews, paired coding labs, and weekly review quizzes.',
    tierColor: 'blue',
  },
  {
    id: 'prot-3',
    code: 'PROT-WELL-03',
    title: 'Counselling & Stress Management Coping Plan',
    tier: 'Tier 3 Intensive',
    triggerCriteria: 'Multiple signals flagged + low wellbeing pulse sentiment score',
    duration: '4 – 6 Weeks',
    activeCases: 5,
    description: 'Confidential coordination with campus psychological counselling cell, academic exam accommodations, and mentor check-in.',
    tierColor: 'purple',
  },
  {
    id: 'prot-4',
    code: 'PROT-ADV-04',
    title: 'Faculty Advisor 1-on-1 Learning Contract',
    tier: 'Tier 2 Targeted',
    triggerCriteria: 'Mid-semester cumulative risk index > 0.65',
    duration: '2 Weeks',
    activeCases: 4,
    description: 'Formal academic improvement contract signed by faculty and student establishing minimum assignment milestones.',
    tierColor: 'yellow',
  },
]

export function InterventionsProtocolsPage() {
  const { addToast } = useApp()
  const [protocols, setProtocols] = useState<ProtocolItem[]>(INSTITUTIONAL_PROTOCOLS)
  const [selectedTier, setSelectedTier] = useState<string>('All')
  const [selectedProtocolId, setSelectedProtocolId] = useState<string>('prot-1')

  const activeProtocol = protocols.find((p) => p.id === selectedProtocolId) || protocols[0]

  const filteredProtocols = protocols.filter(
    (p) => selectedTier === 'All' || p.tier.includes(selectedTier)
  )

  const getTierBadge = (tier: ProtocolItem['tier']) => {
    if (tier.includes('Tier 3')) {
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEE2E2] text-[#DC2626]">Tier 3 Intensive</span>
    }
    if (tier.includes('Tier 2')) {
      return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF3C7] text-[#D97706]">Tier 2 Targeted</span>
    }
    return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E1EFFF] text-[#2563EB]">Tier 1 Universal</span>
  }

  return (
    <>
      <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-1">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
              Interventions &amp; Protocols
            </h1>
            <p className="text-xs text-[#717E95] font-medium mt-1">
              Standardized support playbooks, tier escalations, and compliance workflows
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              className="flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] transition"
            >
              <CircleHelp className="w-4 h-4" />
            </button>
            <button
              type="button"
              className="relative flex items-center justify-center w-9 h-9 rounded-full bg-white shadow-xs border border-gray-100 text-[#64748B] hover:text-[#1E2433] transition"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-white" />
            </button>
            <img
              src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80"
              alt="Prof. Sharma"
              className="w-8 h-8 rounded-full object-cover ring-2 ring-white shadow-2xs ml-1"
            />
          </div>
        </header>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          <div className="bg-[#E5EEFB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#284873]">Approved Protocols</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">8</span>
              <span className="text-[11px] font-medium text-gray-500 ml-2">Evidence-Based</span>
            </div>
          </div>

          <div className="bg-[#FDF2D5] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#614F23]">Active Student Interventions</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">24</span>
              <span className="text-[11px] font-bold text-[#16A34A] ml-2">Across 4 Tracks</span>
            </div>
          </div>

          <div className="bg-[#E6F8EE] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#16A34A]">Intervention Success Rate</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">88.5%</span>
              <span className="text-[11px] font-bold text-[#16A34A] ml-2">Restored Benchmark</span>
            </div>
          </div>
        </div>

        {/* Tier Filter Tabs */}
        <div className="flex items-center gap-2 bg-white rounded-2xl p-2.5 px-3.5 shadow-2xs border border-gray-100/70">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mr-1">Filter Tier:</span>
          {['All', 'Tier 1', 'Tier 2', 'Tier 3'].map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                selectedTier === tier
                  ? 'bg-[#1E2433] text-white font-semibold shadow-xs'
                  : 'text-[#64748B] hover:text-[#1E2433] hover:bg-gray-100'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>

        {/* Protocols Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filteredProtocols.map((protocol) => {
            const isSelected = protocol.id === activeProtocol.id
            return (
              <div
                key={protocol.id}
                onClick={() => setSelectedProtocolId(protocol.id)}
                className={`bg-white rounded-2xl p-4.5 shadow-sm border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'border-[#2563EB] ring-2 ring-[#2563EB]/10'
                    : 'border-gray-100/70 hover:border-gray-300'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between pb-2">
                    <span className="text-xs font-mono font-bold text-gray-500">
                      {protocol.code}
                    </span>
                    {getTierBadge(protocol.tier)}
                  </div>

                  <h3 className="text-sm font-bold text-[#1E2433] mt-1 leading-snug">
                    {protocol.title}
                  </h3>

                  <p className="text-xs text-[#505D75] mt-2 leading-relaxed">
                    {protocol.description}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Duration: <strong className="text-[#1E2433]">{protocol.duration}</strong></span>
                  </div>
                  <span className="font-semibold text-[#2563EB] bg-[#EBF3FC] px-2 py-0.5 rounded-full text-[10px]">
                    {protocol.activeCases} Active Cases
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </main>

      {/* Right-Side Protocol Deployment & Compliance Console */}
      <aside className="w-76 xl:w-84 shrink-0 flex flex-col gap-3.5 font-sans">
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-xs font-mono font-bold text-[#2563EB] bg-[#EBF3FC] px-2.5 py-0.5 rounded-full">
                {activeProtocol.code}
              </span>
              {getTierBadge(activeProtocol.tier)}
            </div>

            <h3 className="text-sm font-bold text-[#1E2433] mt-3">
              {activeProtocol.title}
            </h3>

            {/* Trigger Criteria */}
            <div className="mt-3.5 p-3 rounded-2xl bg-[#F8F9FD] border border-gray-100">
              <span className="text-[10px] font-bold text-[#717E95] uppercase">
                Trigger Criteria
              </span>
              <p className="text-xs text-gray-800 font-medium mt-1">
                {activeProtocol.triggerCriteria}
              </p>
            </div>

            {/* Institutional Compliance Checklist */}
            <div className="mt-4">
              <h4 className="text-xs font-bold text-[#1E2433] mb-2 flex items-center gap-1.5">
                <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>Protocol Quality Safeguards</span>
              </h4>
              <div className="space-y-1.5 text-xs text-gray-700">
                <div className="flex items-center gap-2 p-2 rounded-xl bg-gray-50">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Human faculty review required before case open</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded-xl bg-gray-50">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Cryptographic hash logged on every milestone</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded-xl bg-gray-50">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Small-group privacy suppression active (&lt;5 students)</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2 mt-5 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => addToast('Protocol Initiated', `Launched "${activeProtocol.title}" workflow for selected cohort.`, 'success')}
                className="w-full py-2.5 px-3 rounded-2xl bg-[#1E2433] text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs hover:bg-[#2B3347] transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Deploy Protocol to Case</span>
              </button>

              <button
                type="button"
                onClick={() => addToast('Exporting Dossier', 'Downloaded institutional protocol handbook (PDF).', 'info')}
                className="w-full py-2.5 px-3 rounded-2xl bg-white border border-gray-200 text-[#1E2433] text-xs font-semibold flex items-center justify-center gap-2 shadow-2xs hover:bg-gray-50 transition"
              >
                <Bookmark className="w-3.5 h-3.5 text-gray-500" />
                <span>Download Protocol Guide</span>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

