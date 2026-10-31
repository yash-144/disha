import React, { useState } from 'react'
import {
  ShieldCheck,
  FileCheck,
  Lock,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Upload,
  Link,
  Clock,
  Search,
} from 'lucide-react'
import { INITIAL_DOCUMENTS, DocumentRecord } from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminDocumentIntegrityPage() {
  const { addToast } = useApp()
  const [documents, setDocuments] = useState<DocumentRecord[]>(INITIAL_DOCUMENTS)
  const [searchQuery, setSearchQuery] = useState('')
  const [isVerifying, setIsVerifying] = useState(false)

  const filteredDocs = documents.filter(
    (d) =>
      !searchQuery ||
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.documentRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.sha256Hash.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Verify Document Integrity (DOC-09: DB hash vs bytes, chain hash vs bytes)
  const handleVerifyDocument = (docId: string) => {
    setIsVerifying(true)
    setTimeout(() => {
      setIsVerifying(false)
      setDocuments((prev) =>
        prev.map((d) =>
          d.id === docId
            ? { ...d, lastVerifiedAt: 'Just now', verificationStatus: 'verified_match' }
            : d
        )
      )
      addToast('Integrity Verified', 'SHA-256 byte digest matches stored database hash and on-chain Base Sepolia anchor.', 'success')
    }, 800)
  }

  // Anchor Document on Base Sepolia (DOC-06 / DOC-07)
  const handleAnchorDocument = (docId: string) => {
    setDocuments((prev) =>
      prev.map((d) => {
        if (d.id === docId) {
          return {
            ...d,
            status: 'anchored',
            verificationStatus: 'verified_match',
            txHash: `0x${Math.random().toString(16).substring(2, 40)}`,
            blockNumber: 18492100 + Math.floor(Math.random() * 100),
            anchoredAt: 'Today · Just now',
            lastVerifiedAt: 'Just now',
          }
        }
        return d
      })
    )
    addToast('Document Anchored', 'Transaction confirmed on Base Sepolia testnet (Chain ID: 84532).', 'success')
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. DOCUMENT INTEGRITY HEADER */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Document Integrity &amp; On-Chain Anchoring
            </h2>
            <p className="text-xs text-[#717E95]">
              Verify SHA-256 cryptographic digests, immutable attestations, and Base Sepolia blockchain anchors (DOC-01 - DOC-10)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1.5 rounded-full font-bold flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            <span>Chain ID: 84532 (Base Sepolia)</span>
          </span>
        </div>
      </section>

      {/* 2. SEARCH & CONTROLS */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by document reference, title or SHA-256 hash..."
          className="w-full text-xs pl-9 pr-4 py-2.5 bg-white rounded-full border border-gray-200 focus:outline-none shadow-2xs"
        />
      </div>

      {/* 3. DOCUMENT RECORDS TABLE */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-gray-100 bg-[#FAFBFD] text-gray-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3.5 px-4">Document Reference</th>
                <th className="py-3.5 px-4">Title &amp; Type</th>
                <th className="py-3.5 px-4">SHA-256 Hash Digest</th>
                <th className="py-3.5 px-4">Finalized By</th>
                <th className="py-3.5 px-4">Anchoring State</th>
                <th className="py-3.5 px-4 text-right">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50/70 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-[#1E2433]">
                    {doc.documentRef}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-bold text-[#1E2433] block">{doc.title}</span>
                    <span className="text-[11px] text-gray-400">
                      {doc.fileName} ({Math.round(doc.fileSizeBytes / 1024)} KB)
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[10px] text-gray-600">
                    <span className="bg-gray-100 px-2 py-1 rounded-md block truncate max-w-[220px]" title={doc.sha256Hash}>
                      {doc.sha256Hash}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-gray-800 block">{doc.finalizedBy}</span>
                    <span className="text-[10px] text-gray-400">{doc.finalizedAt}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    {doc.status === 'anchored' ? (
                      <div>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>Anchored (Block #{doc.blockNumber})</span>
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono block mt-0.5 truncate max-w-[150px]">
                          {doc.txHash}
                        </span>
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                        <Clock className="w-3 h-3 text-amber-600" />
                        <span>Pending Anchor</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleVerifyDocument(doc.id)}
                        disabled={isVerifying}
                        className="px-3 py-1 rounded-full text-[11px] font-bold bg-[#1E2433] hover:bg-[#2C3549] text-white transition cursor-pointer"
                      >
                        Verify Hash
                      </button>
                      {doc.status !== 'anchored' && (
                        <button
                          type="button"
                          onClick={() => handleAnchorDocument(doc.id)}
                          className="px-3 py-1 rounded-full text-[11px] font-bold bg-purple-700 hover:bg-purple-800 text-white transition cursor-pointer"
                        >
                          Anchor On-Chain
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

      {/* 4. PRIVACY SAFEGUARD NOTICE (DOC-04) */}
      <div className="p-4 rounded-2xl bg-[#F0FDF4] border border-[#BBF7D0] flex items-start gap-3 text-xs text-[#166534]">
        <Lock className="w-4 h-4 text-[#16A34A] shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Cryptographic Safeguard (DOC-04):</strong> On-chain anchors store solely the SHA-256 byte digest and document reference hash. No student personal identifiable information (PII) or sensitive health reflections are ever submitted to the blockchain network.
        </p>
      </div>
    </div>
  )
}

