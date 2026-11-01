import React from 'react'
import { HeaderTools } from '../common/HeaderTools'
import { useT } from '../../i18n'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'

interface TeacherHeaderProps {
  subtitle?: string
}

export function TeacherHeader({ subtitle }: TeacherHeaderProps) {
  const { user, role } = useSession()
  const t = useT()
  const name = user?.full_name ?? ''
  subtitle = subtitle ?? t(roleLabel(role))
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 font-sans select-none">
      <div>
        <h1 className="font-display text-[34px] leading-tight font-normal tracking-tight text-ink">
          {t('Welcome back')}, {name}!
        </h1>
        <p className="text-xs text-muted font-medium mt-1">
          {subtitle}
        </p>
      </div>

      <HeaderTools />
    </header>
  )
}


