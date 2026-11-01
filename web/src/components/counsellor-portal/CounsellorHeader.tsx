import React from 'react'
import { HeaderTools } from '../common/HeaderTools'
import { useT } from '../../i18n'

interface CounsellorHeaderProps {
  pageTitle?: string
  subtitle?: string
  showPageTitle?: boolean
}

export function CounsellorHeader({
  pageTitle,
  subtitle,
  showPageTitle = false,
}: CounsellorHeaderProps) {
  const t = useT()
    return (
    <header className="flex flex-col gap-3 font-sans select-none mb-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 sm:gap-2.5">

        </div>

        <HeaderTools />
      </div>

      {/* Page Title & Subtitle for subpages (if showPageTitle is true) */}
      {showPageTitle && pageTitle && (
        <div className="mt-1">
          <h1 className="font-display text-[30px] leading-tight tracking-tight text-ink">
            {t(pageTitle)}
          </h1>
          {subtitle && (
            <p className="text-xs text-muted font-medium mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      )}
    </header>
  )
}
