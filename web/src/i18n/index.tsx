import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { HI } from './hi'

/**
 * Tiny UI-string translation. English text is the key, so untranslated strings simply show in English.
 * Only short UI labels are translated; data from the API is shown as received.
 */
export type Lang = 'en' | 'hi'
export const LANGUAGES: { id: Lang; label: string; native: string }[] = [
  { id: 'en', label: 'English', native: 'English' },
  { id: 'hi', label: 'Hindi', native: 'हिन्दी' },
]
const DICTS: Record<Lang, Record<string, string>> = { en: {}, hi: HI }
const KEY = 'disha_lang'

function initial(): Lang {
  try {
    const v = localStorage.getItem(KEY)
    if (v === 'en' || v === 'hi') return v
  } catch { /* storage unavailable */ }
  return 'en'
}

interface Ctx { lang: Lang; setLang: (l: Lang) => void; t: (s: string) => string }
const I18nContext = createContext<Ctx>({ lang: 'en', setLang: () => {}, t: (s) => s })

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initial)
  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    try { localStorage.setItem(KEY, l) } catch { /* ignore */ }
  }, [])
  useEffect(() => { document.documentElement.lang = lang }, [lang])
  const t = useCallback((s: string) => DICTS[lang][s] ?? s, [lang])
  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)
export const useT = () => useContext(I18nContext).t
