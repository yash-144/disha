import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { HI } from './hi'

export type Lang = 'en' | 'hi'
export const LANGUAGES: { id: Lang; label: string; native: string }[] = [
  { id: 'en', label: 'English', native: 'English' },
  { id: 'hi', label: 'Hindi', native: 'हिन्दी' },
]
const DICTS: Record<Lang, Record<string, string>> = { en: {}, hi: HI }
const KEY = 'disha_lang'

const originalTextMap = new WeakMap<Node, string>()

function translateNode(node: Node, dict: Record<string, string>) {
  if (node.nodeType === Node.TEXT_NODE) {
    let original = originalTextMap.get(node)
    if (original === undefined) {
      original = node.nodeValue ?? ''
      originalTextMap.set(node, original)
    }
    const trimmed = original.trim()
    if (trimmed && dict[trimmed]) {
      const leading = original.match(/^\s*/)?.[0] ?? ''
      const trailing = original.match(/\s*$/)?.[0] ?? ''
      node.nodeValue = leading + dict[trimmed] + trailing
    }
    return
  }
  const tag = (node as Element).tagName
  if (
    tag === 'SCRIPT' ||
    tag === 'STYLE' ||
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'CODE' ||
    tag === 'PRE'
  ) {
    return
  }
  for (let i = 0; i < node.childNodes.length; i++) {
    translateNode(node.childNodes[i], dict)
  }
}

function restoreNode(node: Node) {
  if (node.nodeType === Node.TEXT_NODE) {
    const original = originalTextMap.get(node)
    if (original !== undefined) {
      node.nodeValue = original
    }
    return
  }
  const tag = (node as Element).tagName
  if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'INPUT' || tag === 'TEXTAREA') {
    return
  }
  for (let i = 0; i < node.childNodes.length; i++) {
    restoreNode(node.childNodes[i])
  }
}

function initial(): Lang {
  try {
    const v = localStorage.getItem(KEY)
    if (v === 'en' || v === 'hi') return v
  } catch {
    /* storage unavailable */
  }
  return 'en'
}

interface Ctx {
  lang: Lang
  setLang: (l: Lang) => void
  t: (s: string) => string
}
const I18nContext = createContext<Ctx>({ lang: 'en', setLang: () => {}, t: (s) => s })

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initial)
  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    try {
      localStorage.setItem(KEY, l)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    if (lang === 'hi') {
      translateNode(document.body, HI)
      const observer = new MutationObserver((mutations) => {
        for (const m of mutations) {
          if (m.type === 'childList') {
            m.addedNodes.forEach((n) => translateNode(n, HI))
          }
        }
      })
      observer.observe(document.body, { childList: true, subtree: true })
      return () => observer.disconnect()
    } else {
      restoreNode(document.body)
    }
  }, [lang])

  const t = useCallback((s: string) => DICTS[lang][s] ?? s, [lang])
  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)
export const useT = () => useContext(I18nContext).t
