import React from 'react'
import { useSession } from '../../lib/auth/SessionProvider'
import { HeaderTools } from '../common/HeaderTools'
import { useT } from '../../i18n'

interface StudentHeaderProps {
  title?: string
  subtitle?: string
}

export function StudentHeader({
  title,
  subtitle,
}: StudentHeaderProps) {
  const t = useT()
  const { user } = useSession()
  const name = user?.full_name?.split(' ')[0] ?? ''

  return (
    <header className="flex flex-col gap-3 font-sans select-none mb-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 sm:gap-2.5">

        </div>

        <HeaderTools />
      </div>

      {/* Page Title & Subtitle */}
      <div>
        {title ? (
          <h1 className="font-display text-[30px] leading-tight tracking-tight text-ink">
            {t(title)}
          </h1>
        ) : (
          <h1 className="font-display text-[30px] leading-tight tracking-tight text-ink flex items-center gap-1.5">
            <span>Hi, {name}!</span>
            
          </h1>
        )}
        <p className="text-xs text-muted font-medium mt-0.5">
          {subtitle || ""}
        </p>
      </div>
    </header>
  )
}

