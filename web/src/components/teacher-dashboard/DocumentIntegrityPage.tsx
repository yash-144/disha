import React, { useState } from 'react'
import {
  ShieldCheck,
  CheckCircle,
  FileText,
  Lock,
  Copy,
  CircleHelp,
  Bell,
  RefreshCw,
  ExternalLink,
  Search,
  KeyRound,
  FileCheck,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

interface DocumentItem {
  id: string
  docRef: string
  title: string
  student: string
  docType: 'Intervention Plan' | 'Staff Attestation' | 'Case Outcome'
  sha256: string
  date: string
  verified: boolean
}

const INITIAL_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-1',
    docRef: 'DOC-PLAN-2026-001',
    title: 'Intervention Plan: Attendance Remediation (Fall 2025)',
    student: 'Asha Verma',
    docType: 'Intervention Plan',
    sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    date: '14 Oct 2026, 17:30',
    verified: true,
  },
  {
    id: 'doc-2',
    docRef: 'DOC-ATTEST-2026-014',
    title: 'Faculty Attestation: Makeup Lab 3 Signed Clearance',
    student: 'Tanvi Verma',
    docType: 'Staff Attestation',
    sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    date: '10 Oct 2026, 14:15',
    verified: true,
  },
  {
    id: 'doc-3',
    docRef: 'DOC-OUTCOME-2026-009',
    title: 'Concluded Case Outcome: Academic Support Restored',
    student: 'Rohan Mehta',
    docType: 'Case Outcome',
    sha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    date: '08 Oct 2026, 16:40',
    verified: true,
  },
  {
    id: 'doc-4',
    docRef: 'DOC-PLAN-2026-004',
    title: 'Tier 3 Psychological Support Referral Agreement',
    student: 'Rohan Mehta',
    docType: 'Intervention Plan',
    sha256: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
    date: '06 Oct 2026, 11:20',
    verified: true,
  },
]

export function DocumentIntegrityPage() {
  const { addToast } = useApp()
  const [documents, setDocuments] = useState<DocumentItem[]>(INITIAL_DOCUMENTS)
  const [verifyingId, setVerifyingId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const handleVerify = (doc: DocumentItem) => {
    setVerifyingId(doc.id)
    setTimeout(() => {
      setVerifyingId(null)
      addToast(
        'Integrity Check: VALID',
        `SHA-256 cryptographic signature for ${doc.docRef} matches immutable ledger. Untampered.`,
        'success'
      )
    }, 600)
  }

  const copyHash = (hash: string) => {
    navigator.clipboard?.writeText?.(hash)
    addToast('Hash Copied', 'SHA-256 digest copied to clipboard.', 'info')
  }

  const filteredDocs = documents.filter(
    (d) =>
      !searchQuery ||
      d.docRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.student.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <>
      <main className="flex-1 flex flex-col gap-3.5 lg:gap-4 min-w-0 pt-0.5 font-sans">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-1">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1E2433]">
              Document Integrity
            </h1>
            <p className="text-xs text-[#717E95] font-medium mt-1">
              Tamper-evident cryptographic verification, SHA-256 audit chaining, and verified case records
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
            <span className="text-xs font-bold text-[#284873]">Verified Intervention Records</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">42</span>
              <span className="text-[11px] font-medium text-gray-500 ml-2">Cryptographically Hashed</span>
            </div>
          </div>

          <div className="bg-[#E6F8EE] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#16A34A]">Tamper Audit Pass Rate</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">100%</span>
              <span className="text-[11px] font-bold text-[#16A34A] ml-2">Zero Signature Breaches</span>
            </div>
          </div>

          <div className="bg-[#ECE8FB] rounded-2xl p-4 flex flex-col justify-between shadow-2xs">
            <span className="text-xs font-bold text-[#524077]">Audit Chain Block Height</span>
            <div className="mt-3 flex items-baseline">
              <span className="text-3xl font-bold text-[#1E2433]">#128</span>
              <span className="text-[11px] font-mono text-[#7C3AED] ml-2">SHA-256 Chained</span>
            </div>
          </div>
        </div>

        {/* Search & Action Bar */}
        <div className="flex items-center justify-between gap-3 bg-white rounded-2xl p-2.5 px-3.5 shadow-2xs border border-gray-100/70">
          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by Doc Ref, title, student..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-gray-200 text-xs text-[#1E2433] focus:outline-none focus:border-[#3B82F6]"
            />
          </div>

          <button
            type="button"
            onClick={() => {
              addToast('Audit Scan Completed', 'All 42 document digests verified against cryptographic root.', 'success')
            }}
            className="px-3.5 py-1.5 rounded-xl bg-[#1E2433] text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs hover:bg-[#2B3347] transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Verify All Hash Roots</span>
          </button>
        </div>

        {/* Verifiable Documents Table */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/70 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] font-semibold text-[#94A3B8]">
                  <th className="pb-2.5 font-medium">Document Ref</th>
                  <th className="pb-2.5 font-medium">Document Title</th>
                  <th className="pb-2.5 font-medium">Student</th>
                  <th className="pb-2.5 font-medium">Type</th>
                  <th className="pb-2.5 font-medium">SHA-256 Fingerprint</th>
                  <th className="pb-2.5 font-medium text-right">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50/50 transition">
                    <td className="py-3 pr-3 text-xs font-mono font-bold text-[#2563EB]">
                      {doc.docRef}
                    </td>
                    <td className="py-3 pr-3">
                      <p className="text-xs font-bold text-[#1E2433] leading-tight">
                        {doc.title}
                      </p>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {doc.date}
                      </span>
                    </td>
                    <td className="py-3 pr-3 text-xs font-medium text-[#1E2433]">
                      {doc.student}
                    </td>
                    <td className="py-3 pr-3 text-xs text-[#505D75]">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-700">
                        {doc.docType}
                      </span>
                    </td>
                    <td className="py-3 pr-3">
                      <div className="flex items-center gap-1.5">
                        <code className="text-[10px] font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded-lg border border-gray-100 truncate max-w-[130px]">
                          {doc.sha256}
                        </code>
                        <button
                          type="button"
                          onClick={() => copyHash(doc.sha256)}
                          title="Copy full SHA-256 hash"
                          className="p-1 rounded text-gray-400 hover:text-black hover:bg-gray-100 transition"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleVerify(doc)}
                        disabled={verifyingId === doc.id}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold bg-[#EAF7EE] text-[#16A34A] border border-[#BBF7D0] hover:bg-[#DCFCE7] transition"
                      >
                        {verifyingId === doc.id ? (
                          <RefreshCw className="w-3 h-3 animate-spin" />
                        ) : (
                          <CheckCircle className="w-3 h-3" />
                        )}
                        <span>{verifyingId === doc.id ? 'Checking...' : 'Verified'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Right-Side Cryptographic Hash-Chain Inspector */}
      <aside className="w-76 xl:w-84 shrink-0 flex flex-col gap-3.5 font-sans">
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-xs font-bold text-[#1E2433] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#2563EB]" />
                <span>Hash-Chain Inspector</span>
              </span>
              <span className="text-[10px] font-bold text-[#16A34A] bg-[#EAF7EE] px-2 py-0.5 rounded-full">
                Ledger Live
              </span>
            </div>

            <p className="text-xs text-[#717E95] mt-2.5 leading-relaxed">
              Every case milestone incorporates the SHA-256 digest of the previous block, ensuring an immutable institutional audit trail.
            </p>

            {/* Block Chain Visualization */}
            <div className="mt-4 space-y-2">
              <div className="p-3 rounded-2xl bg-[#F8F9FD] border border-gray-100">
                <div className="flex items-center justify-between text-[10px] font-bold text-[#2563EB]">
                  <span>EVENT BLOCK #128</span>
                  <span className="text-gray-400">14 Oct, 17:30</span>
                </div>
                <p className="text-xs font-bold text-[#1E2433] mt-1">
                  CASE_TRANSITION: In Progress
                </p>
                <div className="mt-1.5 text-[9px] font-mono text-gray-500 break-all bg-white p-1.5 rounded-lg border border-gray-100">
                  <span className="text-gray-400">prev: </span>d9ca43a789...
                  <br />
                  <span className="text-emerald-600 font-bold">hash: </span>81ef3ab27f...
                </div>
              </div>

              <div className="p-3 rounded-2xl bg-[#F8F9FD] border border-gray-100">
                <div className="flex items-center justify-between text-[10px] font-bold text-[#2563EB]">
                  <span>EVENT BLOCK #127</span>
                  <span className="text-gray-400">14 Oct, 17:28</span>
                </div>
                <p className="text-xs font-bold text-[#1E2433] mt-1">
                  FOLLOW_UP: Staff Attestation
                </p>
                <div className="mt-1.5 text-[9px] font-mono text-gray-500 break-all bg-white p-1.5 rounded-lg border border-gray-100">
                  <span className="text-gray-400">prev: </span>5b7d656022...
                  <br />
                  <span className="text-emerald-600 font-bold">hash: </span>d9ca43a789...
                </div>
              </div>
            </div>

            {/* Verification Badge */}
            <div className="mt-4 p-3 rounded-2xl bg-[#EAF7EE] border border-[#BBF7D0] flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#16A34A] shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-bold text-[#14532D]">
                  Cryptographic Integrity Verified
                </p>
                <p className="text-[10px] text-[#16A34A]">
                  Zero chain reorganizations or hash mismatches detected.
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2 mt-5 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => addToast('Audit Ledger Exported', 'Downloaded complete SHA-256 compliance manifest (JSON).', 'info')}
                className="w-full py-2.5 px-3 rounded-2xl bg-[#1E2433] text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs hover:bg-[#2B3347] transition"
              >
                <FileCheck className="w-3.5 h-3.5" />
                <span>Export Audit Ledger</span>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

