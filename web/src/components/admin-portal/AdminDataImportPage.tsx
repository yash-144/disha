import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useCreateImport, useImports, useIngestionSchema } from '../../lib/api/endpoints/admin.hooks'
import type { ImportBatch, ImportIssue } from '../../lib/api/endpoints/admin'
import { ApiError } from '../../lib/api/errors'

function IssueList({ title, issues }: { title: string; issues: ImportIssue[] }) {
  if (!issues.length) return null
  return (
    <div className="mt-2">
      <p className="text-xs font-bold text-[#1E2433]">{title} ({issues.length})</p>
      <ul className="mt-1 space-y-1 text-xs text-[#4A5568]">
        {issues.map((i, k) => (
          <li key={k}>
            <span className="font-mono">{i.table}</span> [{i.code}] {i.message}
            {i.count > 1 ? ` (x${i.count})` : ''}
          </li>
        ))}
      </ul>
    </div>
  )
}

function BatchSummary({ batch, label }: { batch: ImportBatch; label: string }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-4 text-xs">
      <p className="text-sm font-bold text-[#1E2433]">
        {label}: {batch.status}
        {batch.duplicate ? ' (identical to an earlier upload)' : ''}
      </p>
      <p className="mt-1 text-[#4A5568]">
        Rows: {Object.entries(batch.row_counts).map(([t, n]) => `${t} ${n}`).join(', ') || 'none'}. Linked students{' '}
        {batch.linked_students}, unlinked {batch.unlinked_students}.
      </p>
      <IssueList title="Validation errors" issues={batch.validation_errors} />
      <IssueList title="Warnings" issues={batch.warnings} />
    </div>
  )
}

export function AdminDataImportPage() {
  const schema = useIngestionSchema()
  const imports = useImports()
  const create = useCreateImport()
  const [files, setFiles] = useState<Record<string, File>>({})
  const [result, setResult] = useState<{ batch: ImportBatch; label: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const submit = (dryRun: boolean) => {
    setError(null)
    setResult(null)
    create.mutate(
      { files, dryRun },
      {
        onSuccess: (batch) => setResult({ batch, label: dryRun ? 'Dry run (nothing stored)' : 'Import' }),
        onError: (e) => {
          const body = e instanceof ApiError ? (e.body as { validation_errors?: unknown } | undefined) : undefined
          if (body && typeof body === 'object' && 'validation_errors' in body) {
            setResult({ batch: body as unknown as ImportBatch, label: 'Validation failed' })
          } else setError(errorMessage(e))
        },
      },
    )
  }

  return (
    <div className="flex flex-col gap-4 font-sans">
      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Upload canonical tables</h2>
        <QueryState query={schema} empty={<EmptyState title="No schema" />} isEmpty={(d) => !d.tables.length}>
          {(sc) => (
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {sc.tables.map((t) => (
                <label key={t.name} className="flex flex-col gap-1 text-xs">
                  <span className="font-semibold text-[#1E2433]">
                    {t.name} {t.required ? '(required)' : '(optional)'}
                  </span>
                  <span className="text-[#717E95]">
                    Columns: {[...t.required_columns, ...t.optional_columns.map((c) => `${c}?`)].join(', ')}
                  </span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      const f = e.target.files?.[0]
                      setFiles((prev) => {
                        const next = { ...prev }
                        if (f) next[t.name] = f
                        else delete next[t.name]
                        return next
                      })
                    }}
                  />
                </label>
              ))}
              {sc.notes.length > 0 && (
                <ul className="md:col-span-2 list-disc pl-5 text-xs text-[#717E95]">
                  {sc.notes.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
              )}
            </div>
          )}
        </QueryState>
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            disabled={create.isPending || Object.keys(files).length === 0}
            onClick={() => submit(true)}
            className="rounded-full border border-gray-200 px-4 py-2 text-xs font-semibold disabled:opacity-50"
          >
            Validate only (dry run)
          </button>
          <button
            type="button"
            disabled={create.isPending || Object.keys(files).length === 0}
            onClick={() => submit(false)}
            className="rounded-full bg-purple-700 px-4 py-2 text-xs font-bold text-white disabled:opacity-50"
          >
            {create.isPending ? 'Uploading...' : 'Import'}
          </button>
        </div>
        {error && <p role="alert" className="mt-3 text-xs text-red-600">{error}</p>}
        {result && <div className="mt-3"><BatchSummary batch={result.batch} label={result.label} /></div>}
      </section>

      <section className="rounded-3xl border border-gray-100 bg-white p-5">
        <h2 className="text-sm font-bold text-[#1E2433]">Import history</h2>
        <div className="mt-3">
          <QueryState query={imports} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="No imports yet" />}>
            {(page) => (
              <div className="space-y-2">
                {page.items.map((b) => (
                  <BatchSummary key={b.id} batch={b} label={new Date(b.created_at).toLocaleString()} />
                ))}
              </div>
            )}
          </QueryState>
        </div>
      </section>
    </div>
  )
}
