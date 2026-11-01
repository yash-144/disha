import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { Button, Card, Pill, fmtDate, pretty } from '../common/ui'
import { useCatalogue } from '../../lib/api/endpoints/admin.hooks'
import { usePolicies, usePublishPolicy } from '../../lib/api/endpoints/adminExtensions.hooks'
import { categoryLabel } from '../../lib/labels'
import { errorMessage } from '../../lib/api/errors'

const STATUS_TONE: Record<string, string> = { active: 'bg-emerald-50 text-emerald-700', draft: 'bg-amber-50 text-amber-700', archived: 'bg-sunken text-ink-2' }
const POLICY_STATUS: Record<string, string> = { active: 'In use', draft: 'Draft', archived: 'Retired' }

function Policy() {
  const q = usePolicies()
  const publish = usePublishPolicy()
  return (
    <Card title="When to open a case" tip="Rules that decide which flagged students become suggested cases. Only one version is in use at a time.">
      <QueryState query={q} empty={<EmptyState title="No case rules yet" message="Until one is switched on, the weekly check will not suggest cases." />}>
        {(rows) => (
          <ul className="divide-y divide-line text-xs">
            {[...rows].sort((a, b) => b.version_number - a.version_number).map((v) => (
              <li key={v.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                <span className="flex items-center gap-2">
                  <span className="font-semibold">Version {v.version_number}</span>
                  <Pill tone={STATUS_TONE[v.status] ?? STATUS_TONE.archived}>{POLICY_STATUS[v.status] ?? pretty(v.status)}</Pill>
                  <span className="text-muted">{v.published_at ? `Switched on ${fmtDate(v.published_at)}` : `Created ${fmtDate(v.created_at)}`}</span>
                </span>
                {v.status === 'draft' && (
                  <Button variant="ghost" disabled={publish.isPending} onClick={() => publish.mutate(v.id)}>Switch on</Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
      {publish.isError && <p role="alert" className="mt-2 text-xs text-tier-high">{errorMessage(publish.error)}</p>}
    </Card>
  )
}

export function AdminInterventionsPage() {
  const q = useCatalogue()
  return (
    <div className="flex flex-col gap-4 font-sans">
      <Policy />
      <Card title="Support options" tip="The kinds of help counsellors can choose from when working a case.">
        <QueryState query={q} empty={<EmptyState title="No support options yet" />}>
          {(rows) => (
            <ul className="divide-y divide-line text-xs">
              {rows.map((i) => (
                <li key={i.id} className="flex items-start justify-between gap-3 py-2.5">
                  <span>
                    <span className="font-semibold">{i.name}</span>
                    {i.description && <span className="block text-muted">{i.description}</span>}
                  </span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    {i.category && <Pill>{categoryLabel(i.category)}</Pill>}
                    {!i.is_active && <Pill tone="bg-amber-50 text-amber-700">Inactive</Pill>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </QueryState>
      </Card>
    </div>
  )
}
