import React, { useState } from 'react'
import {
  Sliders,
  Plus,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  Sparkles,
  X,
  Search,
} from 'lucide-react'
import { INITIAL_INTERVENTIONS, InterventionCatalogItem } from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminInterventionsPage() {
  const { addToast } = useApp()
  const [catalog, setCatalog] = useState<InterventionCatalogItem[]>(INITIAL_INTERVENTIONS)
  const [activeTab, setActiveTab] = useState<'catalog' | 'policy'>('catalog')
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  // New intervention form state
  const [displayLabel, setDisplayLabel] = useState('')
  const [domain, setDomain] = useState<InterventionCatalogItem['domain']>('academic')
  const [description, setDescription] = useState('')
  const [requiredPurposeKey, setRequiredPurposeKey] = useState('academic_support')

  const filteredCatalog = catalog.filter(
    (item) =>
      !searchQuery ||
      item.displayLabel.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.domain.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleToggleActive = (id: string) => {
    setCatalog((prev) =>
      prev.map((item) => (item.id === id ? { ...item, active: !item.active } : item))
    )
    addToast('Catalogue Updated', 'Intervention active state updated.', 'info')
  }

  const handleCreateIntervention = (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayLabel.trim() || !description.trim()) {
      addToast('Missing Fields', 'Please provide a display label and description.', 'info')
      return
    }

    const newItem: InterventionCatalogItem = {
      id: `int-${Date.now()}`,
      interventionKey: displayLabel.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      domain,
      displayLabel,
      description,
      recipientRole: domain === 'counselling' ? 'counsellor' : 'student',
      requiredPurposeKey,
      requiresHumanApproval: true,
      active: true,
      version: 1,
      activeCasesCount: 0,
    }

    setCatalog([newItem, ...catalog])
    setIsModalOpen(false)
    setDisplayLabel('')
    setDescription('')
    addToast('Protocol Registered', `Intervention "${displayLabel}" added to campus catalogue.`, 'success')
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. PROTOCOL ENGINE HEADER */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Intervention Protocols &amp; Rules Engine
            </h2>
            <p className="text-xs text-[#717E95]">
              Configure campus intervention catalogue, purpose requirements, and immutable policy versions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Tab Switcher */}
          <div className="flex items-center bg-gray-100 p-1 rounded-full text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveTab('catalog')}
              className={`px-3 py-1 rounded-full transition cursor-pointer ${
                activeTab === 'catalog'
                  ? 'bg-white text-[#1E2433] shadow-xs font-bold'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Intervention Catalogue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('policy')}
              className={`px-3 py-1 rounded-full transition cursor-pointer ${
                activeTab === 'policy'
                  ? 'bg-white text-[#1E2433] shadow-xs font-bold'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Policy Versions (v2.4)
            </button>
          </div>

          {activeTab === 'catalog' && (
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition shadow-xs cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Intervention</span>
            </button>
          )}
        </div>
      </section>

      {/* 2. TAB: INTERVENTION CATALOGUE */}
      {activeTab === 'catalog' && (
        <div className="flex flex-col gap-4">
          <div className="relative max-w-md">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search catalogue by protocol name or domain..."
              className="w-full text-xs pl-9 pr-4 py-2 bg-white rounded-full border border-gray-200 focus:outline-none shadow-2xs"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {filteredCatalog.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-gray-100/90 shadow-2xs p-5 flex flex-col justify-between gap-3 hover:shadow-xs transition"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-purple-50 text-purple-700">
                      {item.domain}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleToggleActive(item.id)}
                      className="cursor-pointer"
                      title={item.active ? 'Deactivate Protocol' : 'Activate Protocol'}
                    >
                      {item.active ? (
                        <ToggleRight className="w-6 h-6 text-emerald-600" />
                      ) : (
                        <ToggleLeft className="w-6 h-6 text-gray-300" />
                      )}
                    </button>
                  </div>

                  <h4 className="text-sm font-bold text-[#1E2433] mt-2">
                    {item.displayLabel}
                  </h4>
                  <p className="text-xs text-[#64748B] mt-1 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-[#717E95]">
                  <span>Purpose: <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">{item.requiredPurposeKey}</code></span>
                  <span className="font-semibold text-purple-700">
                    {item.activeCasesCount} active cases
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. TAB: POLICY VERSIONS & RULES ENGINE (Blueprint §5 & §6) */}
      {activeTab === 'policy' && (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs p-6 flex flex-col gap-5">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#1E2433]">Policy Key: early_warning_benchmark</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
                  PUBLISHED (IMMUTABLE)
                </span>
              </div>
              <p className="text-xs text-[#717E95] mt-0.5">
                Evaluator Version: 2.4.0 • Published: 01 Oct 2025 • Immutable checksum verified
              </p>
            </div>
            <div className="text-right text-[11px] font-mono text-gray-400">
              SHA-256: 4f9b8c2d1e0a...3b7a
            </div>
          </div>

          {/* Rule Definitions List */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
              Deterministic Rules Evaluated by System
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="p-4 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex flex-col justify-between">
                <div>
                  <span className="font-bold text-gray-800 block">Rule: ATTENDANCE_DROP_CRITICAL</span>
                  <p className="text-[11px] text-gray-500 mt-1">
                    Triggers when verified attendance across 2 consecutive lab sessions drops below 75%.
                  </p>
                </div>
                <div className="mt-3 text-[10px] text-purple-700 font-semibold">
                  Yields: attention_suggested (Action Required)
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex flex-col justify-between">
                <div>
                  <span className="font-bold text-gray-800 block">Rule: WORKLOAD_DENSITY_STRESS</span>
                  <p className="text-[11px] text-gray-500 mt-1">
                    Triggers when assignment backlogs coincide with self-reported pulse dip below threshold 50.
                  </p>
                </div>
                <div className="mt-3 text-[10px] text-purple-700 font-semibold">
                  Yields: attention_suggested (Intervention: Workload Pacing)
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#FAFBFD] border border-gray-100 flex flex-col justify-between">
                <div>
                  <span className="font-bold text-gray-800 block">Rule: MISSING_EVIDENCE_GUARD</span>
                  <p className="text-[11px] text-gray-500 mt-1">
                    Missing or stale evidence yields &apos;unknown&apos;, strictly forbidding imputed predictions (FR-SIG-03).
                  </p>
                </div>
                <div className="mt-3 text-[10px] text-gray-500 font-semibold">
                  Yields: unknown (No rule triggered)
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CREATE INTERVENTION MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <Sliders className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E2433]">Register Intervention Protocol</h3>
                  <p className="text-[11px] text-[#717E95]">Campus Catalogue Management</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateIntervention} className="p-5 flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Protocol Display Label *</label>
                <input
                  type="text"
                  value={displayLabel}
                  onChange={(e) => setDisplayLabel(e.target.value)}
                  placeholder="e.g. Peer Buddy Onboarding Cohort Sync"
                  className="p-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Domain</label>
                  <select
                    value={domain}
                    onChange={(e) => setDomain(e.target.value as any)}
                    className="p-2.5 rounded-xl border border-gray-200 bg-white"
                  >
                    <option value="academic">Academic</option>
                    <option value="mentor">Mentor</option>
                    <option value="counselling">Counselling</option>
                    <option value="finance">Finance</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-bold text-[#1E2433]">Required Purpose Key</label>
                  <select
                    value={requiredPurposeKey}
                    onChange={(e) => setRequiredPurposeKey(e.target.value)}
                    className="p-2.5 rounded-xl border border-gray-200 bg-white"
                  >
                    <option value="academic_support">academic_support</option>
                    <option value="early_warning">early_warning</option>
                    <option value="counselling_referral">counselling_referral</option>
                    <option value="emergency_response">emergency_response</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-bold text-[#1E2433]">Protocol Description *</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detailed criteria, expected milestones and staff review cadence..."
                  className="p-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="p-4 bg-gray-50 border-t border-gray-100 -mx-5 -mb-5 mt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-200/60 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-full font-bold text-white bg-purple-700 hover:bg-purple-800 transition"
                >
                  Save to Catalogue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

