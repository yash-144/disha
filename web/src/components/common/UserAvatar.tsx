import React from 'react'

export function initialsOf(name: string | null | undefined): string {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase()
}

/** Initials avatar (the API has no profile photo). */
export function UserAvatar({ name, className = 'w-8 h-8 text-xs' }: { name?: string | null; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-accent font-semibold text-white ${className}`}
    >
      {initialsOf(name)}
    </span>
  )
}
