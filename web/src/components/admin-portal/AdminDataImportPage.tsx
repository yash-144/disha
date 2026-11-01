import React, { useRef, useState } from 'react'
import { CheckCircle2, FileSpreadsheet, FileText, UploadCloud, X, AlertTriangle } from 'lucide-react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage, ApiError } from '../../lib/api/errors'
import { useCreateImport, useImports, useIngestionSchema } from '../../lib/api/endpoints/admin.hooks'
import type { ImportBatch, ImportIssue } from '../../lib/api/endpoints/admin'
import { Button, Card, InfoTip, Pill, Tabs, fmtDateTime, pretty } from '../common/ui'

function IssueList({ title, issues, tone }: { title: string; issues: ImportIssue[]; tone: string }) {
  if (!issues?.length) return null
  return (
    <div className={`mt-3 rounded-xl p-3 ${tone}`}>
      <p className="text-xs font-bold">{title} ({issues.length})</p>
      <ul className="mt-1 space-y-1 text-xs">
        {issues.slice(0, 8).map((i, k) => (
          <li key={k}><span className="font-semibold">{pretty(i.table)}</span>: {i.message}{i.count > 1 ? ` (${i.count} rows)` : ''}</li>
        ))}
        {issues.length > 8 && <li>…and {issues.length - 8} more</li>}
      </ul>
    </div>
  )
}

function BatchSummary({ batch, label, dry }: { batch: ImportBatch; label: string; dry?: boolean }) {
  const failed = (batch.validation_errors?.length ?? 0) > 0 || batch.status === 'failed' || batch.status === 'rejected'
  return (
    <div className="rounded-2xl border border-line bg-white p-4 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        {failed ? <AlertTriangle className="h-4 w-4 text-rose-500" /> : <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
        <p className="text-sm font-bold text-ink">{label}</p>
        <Pill tone={failed ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}>{pretty(batch.status)}</Pill>
        {dry && <Pill>Nothing was saved</Pill>}
        {batch.duplicate && <Pill tone="bg-amber-50 text-amber-700">Same as an earlier upload</Pill>}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.entries(batch.row_counts ?? {}).map(([t, n]) => (
          <div key={t} className="rounded-xl bg-gray-50 p-2.5"><p className="text-base font-semibold tabular-nums">{n as number}</p><p className="text-xs text-muted">{pretty(t)}</p></div>
        ))}
        <div className="rounded-xl bg-gray-50 p-2.5"><p className="text-base font-semibold tabular-nums">{batch.linked_students}</p><p className="text-xs text-muted">Students matched</p></div>
        <div className="rounded-xl bg-gray-50 p-2.5"><p className="text-base font-semibold tabular-nums">{batch.unlinked_students}</p><p className="text-xs text-muted">Not matched</p></div>
      </div>
      <IssueList title="Fix these first" issues={batch.validation_errors} tone="bg-rose-50 text-rose-800" />
      <IssueList title="Worth a look" issues={batch.warnings} tone="bg-amber-50 text-amber-900" />
    </div>
  )
}

function FilePick({ name, hint, accept, file, onFile }: { name: string; hint?: string; accept: string; file?: File; onFile: (f?: File) => void }) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div className={`flex items-center gap-3 rounded-xl border border-dashed p-3 text-xs ${file ? 'border-emerald-300 bg-emerald-50/50' : 'border-line bg-white'}`}>
      {file ? <FileText className="h-5 w-5 shrink-0 text-emerald-600" /> : <FileSpreadsheet className="h-5 w-5 shrink-0 text-muted" />}
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{pretty(name)}</p>
        <p className="truncate text-xs text-muted">{file ? file.name : hint}</p>
      </div>
      <input ref={ref} type="file" accept={accept} className="sr-only" aria-label={`Choose file for ${name}`} onChange={(e) => onFile(e.target.files?.[0])} />
      {file ? (
        <button type="button" aria-label="Remove file" onClick={() => { onFile(undefined); if (ref.current) ref.current.value = '' }} className="rounded-full p-1 text-gray-500 hover:bg-black/5"><X className="h-4 w-4" /></button>
      ) : (
        <Button variant="ghost" onClick={() => ref.current?.click()}>Choose file</Button>
      )}
    </div>
  )
}

export function AdminDataImportPage() {
  const schema = useIngestionSchema()
  const imports = useImports()
  const create = useCreateImport()
  const [mode, setMode] = useState<'workbook' | 'csv'>('workbook')
  const [files, setFiles] = useState<Record<string, File>>({})
  const [result, setResult] = useState<{ batch: ImportBatch; label: string; dry: boolean } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const setFile = (k: string, f?: File) => setFiles((prev) => { const n = { ...prev }; if (f) n[k] = f; else delete n[k]; return n })
  const active = mode === 'workbook' ? (files.workbook ? { workbook: files.workbook } : {}) : Object.fromEntries(Object.entries(files).filter(([k]) => k !== 'workbook'))
  const ready = Object.keys(active).length > 0

  const submit = (dry: boolean) => {
    setError(null)
    setResult(null)
    create.mutate({ files: active as Record<string, File>, dryRun: dry }, {
      onSuccess: (batch) => setResult({ batch, label: dry ? 'Check finished' : 'Import finished', dry }),
      onError: (e) => {
        const body = e instanceof ApiError ? (e.body as { validation_errors?: unknown } | undefined) : undefined
        if (body && typeof body === 'object' && 'validation_errors' in body) setResult({ batch: body as unknown as ImportBatch, label: 'We found problems', dry })
        else setError(errorMessage(e))
      },
    })
  }

  return (
    <div className="flex flex-col gap-4 font-sans">
      <Card title="Upload campus data" tip="Upload one Excel file with a sheet for each kind of data, or one CSV file for each. Run the check first: it looks for problems without saving anything.">
        <Tabs value={mode} onChange={setMode} items={[{ id: 'workbook', label: 'One Excel file' }, { id: 'csv', label: 'CSV per table' }]} />
        <div className="mt-4">
          <QueryState query={schema} isEmpty={(d) => !d.tables.length} empty={<EmptyState title="We could not load the file layout" message="Try again in a moment." />}>
            {(sc) =>
              mode === 'workbook' ? (
                <div className="space-y-3">
                  <FilePick name="workbook" hint="An .xlsx file with one sheet for each kind of data" accept=".xlsx" file={files.workbook} onFile={(f) => setFile('workbook', f)} />
                  <p className="text-xs text-muted">Sheets to include: {sc.tables.map((t) => `${pretty(t.name)}${t.required ? '*' : ''}`).join(', ')} (* must have)</p>
                </div>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {sc.tables.map((t) => (
                    <FilePick key={t.name} name={`${t.name}${t.required ? ' *' : ''}`} hint={`Needs columns: ${t.required_columns.join(', ')}`} accept=".csv" file={files[t.name]} onFile={(f) => setFile(t.name, f)} />
                  ))}
                </div>
              )
            }
          </QueryState>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button variant="ghost" disabled={create.isPending || !ready} onClick={() => submit(true)}>Check files first</Button>
          <Button disabled={create.isPending || !ready} onClick={() => submit(false)}><UploadCloud className="h-3.5 w-3.5" /> {create.isPending ? 'Working…' : 'Import'}</Button>
          <InfoTip text="After importing, open Early warning and run the weekly check so the new data is used." />
        </div>
        {error && <p role="alert" className="mt-3 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
        {result && <div className="mt-3"><BatchSummary batch={result.batch} label={result.label} dry={result.dry} /></div>}
      </Card>

      <Card title="Past imports">
        <QueryState query={imports} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="No imports yet" message="Your first upload will show up here." />}>
          {(page) => (
            <div className="space-y-2">{page.items.map((b) => <BatchSummary key={b.id} batch={b} label={fmtDateTime(b.created_at)} />)}</div>
          )}
        </QueryState>
      </Card>
    </div>
  )
}
