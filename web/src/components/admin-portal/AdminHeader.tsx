import React from 'react'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { HeaderTools } from '../common/HeaderTools'
import { useT } from '../../i18n'

interface AdminHeaderProps {
  pageTitle?: string
  subtitle?: string
}

export function AdminHeader({ pageTitle, subtitle }: AdminHeaderProps) {
  const { user, role } = useSession()
  const t = useT()
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 font-sans">
      <div>
        <h1 className="font-display text-[34px] leading-tight font-normal tracking-tight text-ink">{pageTitle ? t(pageTitle) : `${t('Welcome back')}, ${user?.full_name ?? ''}`}</h1>
        {(subtitle || roleLabel(role)) && <p className="text-xs text-muted font-medium mt-1">{subtitle || t(roleLabel(role))}</p>}
      </div>
      <HeaderTools />
    </header>
  )
}
