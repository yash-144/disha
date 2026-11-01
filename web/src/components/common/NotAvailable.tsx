import React from 'react'
import { EmptyState } from './QueryState'

/** Honest placeholder for a feature that has no backend endpoint yet. */
export function NotAvailable({ title, message }: { title: string; message?: string }) {
  return <EmptyState title={`${title}: not available yet`} message={message ?? 'This feature is not connected to the server yet.'} />
}
