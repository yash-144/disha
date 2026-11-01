import React from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { Button, Card, Pill, fmtDate, pretty } from '../common/ui'
import { useCatalogue } from '../../lib/api/endpoints/admin.hooks'
import { usePolicies, usePublishPolicy } from '../../lib/api/endpoints/adminExtensions.hooks'
import { errorMessage } from '../../lib/api/errors'

const STATUS_TONE: Record<string, string> = { active: 'bg-emerald-50 text-emerald-700', draft: 'bg-amber-50 text-amber-700', archived: 'bg-sunken text-ink-2' }

function Policy() {
  const q = usePolicies()
  const publish = usePublishPolicy()
  return (
    <Card title="Flagging policy" tip="Rules that decide which risk scores become case suggestions. Only one version is active at a time.">
      <QueryState query={q} empty={<EmptyState title="No policy versions yet" message="Without an active policy, scoring runs do not create case suggestions." />}>
        {(rows) => (
          <ul className="divide-y divide-line text-xs">
            {[...rows].sort((a, b) => b.version_number - a.version_number).map((v) => (
              <li key={v.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                <span className="flex items-center gap-2">
                  <span className="font-semibold">Version {v.version_number}</span>
                  <Pill tone={STATUS_TONE[v.status] ?? STATUS_TONE.archived}>{pretty(v.status)}</Pill>
                  <span className="text-muted">{v.published_at ? `Published ${fmtDate(v.published_at)}` : `Created ${fmtDate(v.created_at)}`}</span>
                </span>
                {v.status === 'draft' && (
                  <Button variant="ghost" disabled={publish.isPending} onClick={() => publish.mutate(v.id)}>Publish</Button>
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
      <Card title="Intervention catalogue" tip="The support actions counsellors can choose from when working a case.">
        <QueryState query={q} empty={<EmptyState title="No interventions in the catalogue" />}>
          {(rows) => (
            <ul className="divide-y divide-line text-xs">
              {rows.map((i) => (
                <li key={i.id} className="flex items-start justify-between gap-3 py-2.5">
                  <span>
                    <span className="font-semibold">{i.name}</span>
                    {i.description && <span className="block text-muted">{i.description}</span>}
                  </span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    {i.category && <Pill>{pretty(i.category)}</Pill>}
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
