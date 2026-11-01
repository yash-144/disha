import React, { useCallback, useRef, useState } from 'react'
import { Check, ChevronDown, Globe, Repeat } from 'lucide-react'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { LANGUAGES, useI18n } from '../../i18n'
import { Popover, useMembershipOptions } from './AccountMenu'

const CHIP = 'flex h-8 items-center gap-1.5 rounded-md border border-line bg-panel px-2.5 text-xs font-semibold text-ink transition hover:bg-sunken'

export function LanguageSwitcher() {
  const { lang, setLang, t } = useI18n()
  const [open, setOpen] = useState(false)
  const btn = useRef<HTMLButtonElement>(null)
  const close = useCallback(() => setOpen(false), [])
  const cur = LANGUAGES.find((l) => l.id === lang)!
  return (
    <>
      <button ref={btn} type="button" onClick={() => setOpen((o) => !o)} aria-haspopup="dialog" aria-expanded={open} aria-label={`${t('Language')}: ${cur.label}`} className={CHIP}>
        <Globe className="h-3.5 w-3.5" /> <span>{cur.native}</span> <ChevronDown className="h-3 w-3 opacity-60" />
      </button>
      <Popover anchor={btn} open={open} onClose={close} align="end" width={192} label={t('Language')}>
        <ul className="p-1.5">
          {LANGUAGES.map((l) => (
            <li key={l.id}>
              <button type="button" onClick={() => { setLang(l.id); close() }} aria-pressed={l.id === lang} className="flex w-full items-center justify-between rounded-md px-2.5 py-2 text-left text-xs hover:bg-sunken">
                <span><span className="font-semibold">{l.native}</span> <span className="text-muted">{l.label}</span></span>
                {l.id === lang && <Check className="h-4 w-4 text-accent" />}
              </button>
            </li>
          ))}
        </ul>
      </Popover>
    </>
  )
}

/** Static badge for one membership; a switcher for several. Switching re-resolves the portal without a reload. */
export function RoleSwitcher() {
  const { membership, setActiveRole } = useSession()
  const { t } = useI18n()
  const options = useMembershipOptions()
  const [open, setOpen] = useState(false)
  const btn = useRef<HTMLButtonElement>(null)
  const close = useCallback(() => setOpen(false), [])
  const label = t(roleLabel(membership?.role))
  if (options.length <= 1) {
    return <span className="flex h-8 items-center rounded-md border border-line bg-sunken/60 px-2.5 text-xs font-semibold text-ink-2" title={t('Role')}>{label}</span>
  }
  return (
    <>
      <button ref={btn} type="button" onClick={() => setOpen((o) => !o)} aria-haspopup="dialog" aria-expanded={open} aria-label={`${t('Switch role')}: ${label}`} className={CHIP}>
        <Repeat className="h-3.5 w-3.5" /> <span>{label}</span> <ChevronDown className="h-3 w-3 opacity-60" />
      </button>
      <Popover anchor={btn} open={open} onClose={close} align="end" width={272} label={t('Switch role')}>
        <ul className="p-1.5">
          {options.map((o) => (
            <li key={o.key}>
              <button type="button" onClick={() => { close(); setActiveRole(o.campusId, o.role) }} aria-pressed={o.current} className="flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-2 text-left text-xs hover:bg-sunken">
                <span className="min-w-0"><span className="block truncate font-semibold">{t(roleLabel(o.role))}</span><span className="block truncate text-xs text-muted">{o.campusName}</span></span>
                {o.current && <Check className="h-4 w-4 text-accent" />}
              </button>
            </li>
          ))}
        </ul>
      </Popover>
    </>
  )
}
