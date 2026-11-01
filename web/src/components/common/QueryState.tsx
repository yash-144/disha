import React from 'react'
import { AlertTriangle, Inbox, RefreshCw } from 'lucide-react'
import { ApiError, errorMessage } from '../../lib/api/errors'

/** Minimal shape shared by TanStack Query results (useQuery, useInfiniteQuery, ...). */
interface QueryLike<T> {
  data: T | undefined
  isPending: boolean
  isError: boolean
  error: unknown
  refetch: () => unknown
  isFetching?: boolean
}

export function LoadingSkeleton({ rows = 3, className = '' }: { rows?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`} role="status" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading</span>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-2xl bg-gray-200/70" />
      ))}
    </div>
  )
}

export function EmptyState({
  title = 'Nothing here yet',
  message,
  action,
}: {
  title?: string
  message?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line bg-white/60 px-6 py-10 text-center">
      <Inbox className="h-6 w-6 text-muted" aria-hidden="true" />
      <p className="text-sm font-bold text-ink">{title}</p>
      {message && <p className="max-w-sm text-xs text-muted">{message}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const forbidden = error instanceof ApiError && error.isForbidden
  const title = forbidden ? 'You do not have access to this' : 'Could not load this'
  const requestId = error instanceof ApiError ? error.requestId : null
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-red-100 bg-red-50/70 px-6 py-10 text-center"
    >
      <AlertTriangle className="h-6 w-6 text-red-500" aria-hidden="true" />
      <p className="text-sm font-bold text-ink">{title}</p>
      <p className="max-w-sm text-xs text-muted">{errorMessage(error)}</p>
      {requestId && <p className="font-mono text-[10px] text-muted">Reference: {requestId}</p>}
      {onRetry && !forbidden && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-gray-50"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Try again
        </button>
      )}
    </div>
  )
}

interface QueryStateProps<T> {
  query: QueryLike<T>
  /** Treat the loaded data as empty (default: empty array / null / undefined). */
  isEmpty?: (data: T) => boolean
  loading?: React.ReactNode
  empty?: React.ReactNode
  /** Rendered only when data is loaded and non-empty. */
  children: (data: T) => React.ReactNode
}

function defaultIsEmpty(data: unknown): boolean {
  return data == null || (Array.isArray(data) && data.length === 0)
}

/**
 * Standard loading / error / empty / data switch for any query. Use this
 * instead of hand-rolled spinners so every portal behaves the same.
 */
export function QueryState<T>({ query, isEmpty = defaultIsEmpty, loading, empty, children }: QueryStateProps<T>) {
  if (query.isPending) return <>{loading ?? <LoadingSkeleton />}</>
  if (query.isError) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />
  const data = query.data as T
  if (isEmpty(data)) return <>{empty ?? <EmptyState />}</>
  return <>{children(data)}</>
}
