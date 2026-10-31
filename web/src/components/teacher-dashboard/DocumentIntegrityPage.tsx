import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useAnchoringStatus, useDocuments, useUploadDocument, useVerifyDocument } from '../../lib/api/endpoints/documents.hooks'

export function DocumentIntegrityPage() {
  const docs = useDocuments()
  const anchoring = useAnchoringStatus()
  const upload = useUploadDocument()
  const verify = useVerifyDocument()
  const [file, setFile] = useState<File | null>(null)
  const [kind, setKind] = useState('evidence')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const doUpload = () => {
    if (!file) return
    setMsg(null)
    upload.mutate({ file, kind }, {
      onSuccess: (d) => { setMsg({ ok: true, text: `Uploaded ${d.filename} (sha256 ${d.sha256.slice(0, 12)}...)` }); setFile(null) },
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  const doVerify = (id: string) => {
    setMsg(null)
    verify.mutate(id, {
      onSuccess: (v) => setMsg({ ok: v.ok, text: `${v.document_ref}: ${v.ok ? 'verified' : 'verification failed'} (${v.status})` }),
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }

  return (
    <main className="flex-1 p-4 font-sans flex flex-col gap-4">
      <h1 className="text-lg font-bold text-[#1E2433]">Document Integrity</h1>
      <p className="text-xs text-[#717E95]">
        Blockchain anchoring: {anchoring.isPending ? 'checking...' : anchoring.data?.enabled ? 'enabled' : `not configured${anchoring.data?.message ? ` (${anchoring.data.message})` : ''}`}
      </p>
      <section className="flex flex-wrap items-end gap-3 rounded-2xl border border-gray-100 bg-white p-4 text-xs">
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <label className="flex flex-col gap-1">Kind
          <input value={kind} onChange={(e) => setKind(e.target.value)} className="rounded-lg border border-gray-200 px-2 py-1" />
        </label>
        <button type="button" disabled={!file || upload.isPending} onClick={doUpload} className="rounded-full bg-purple-700 px-4 py-2 font-bold text-white disabled:opacity-50">
          {upload.isPending ? 'Uploading...' : 'Upload'}
        </button>
      </section>
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</p>}
      <QueryState query={docs} empty={<EmptyState title="No documents" />}>
        {(rows) => (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white text-xs">
            {rows.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-3 p-3">
                <span>{d.filename} <span className="text-[#717E95]">v{d.version}, {d.status}</span></span>
                <span className="font-mono text-[#717E95]">{d.sha256.slice(0, 12)}</span>
                <button type="button" disabled={verify.isPending} onClick={() => doVerify(d.id)} className="rounded-full border border-gray-200 px-3 py-1 font-semibold disabled:opacity-50">Verify</button>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </main>
  )
}
