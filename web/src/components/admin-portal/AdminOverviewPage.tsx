import React from 'react'
import { AdminAnalyticsPage } from './AdminAnalyticsPage'

export function AdminOverviewPage({ onNavigateTab }: { onNavigateTab: (tab: string) => void }) {
  return (
    <div className="flex flex-col gap-4">
      <AdminAnalyticsPage />
      <div className="flex gap-2 text-xs">
        <button type="button" onClick={() => onNavigateTab('data-import')} className="rounded-full border border-gray-200 bg-white px-4 py-2 font-semibold">Import data</button>
        <button type="button" onClick={() => onNavigateTab('risk-model')} className="rounded-full border border-gray-200 bg-white px-4 py-2 font-semibold">Risk model</button>
        <button type="button" onClick={() => onNavigateTab('case-management')} className="rounded-full border border-gray-200 bg-white px-4 py-2 font-semibold">Cases</button>
      </div>
    </div>
  )
}
