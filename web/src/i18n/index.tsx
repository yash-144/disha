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

// Common dynamic phrase replacement rules for Hindi
const PHRASE_RULES: [RegExp, string][] = [
  // Templates with numbers
  [/(\d+)\s+of\s+(\d+)\s+student-courses\s+need\s+attention\s+this\s+week/gi, 'इस सप्ताह $2 में से $1 छात्र-पाठ्यक्रमों पर ध्यान देने की आवश्यकता है'],
  [/We\s+flag\s+students\s+a\s+median\s+of\s+(\d+)\s+days\s+before\s+they\s+leave\.?/gi, 'हम छात्रों के संस्थान छोड़ने से औसतन $1 दिन पहले ही चेतावनी दे देते हैं।'],
  [/Typically\s+(\d+)\s+to\s+(\d+)\s+days\.?/gi, 'आमतौर पर $1 से $2 दिन।'],
  [/We\s+spot\s+(\d+)\s+of\s+every\s+10\s+students\s+who\s+go\s+on\s+to\s+struggle\.?/gi, 'हम संघर्ष करने वाले हर 10 में से $1 छात्रों को पहले ही पहचान लेते हैं।'],
  [/(\d+)\s+of\s+every\s+10\s+flagged\s+students\s+really\s+needed\s+help\.?/gi, 'चिह्नित हर 10 में से $1 छात्रों को वास्तव में सहायता की आवश्यकता थी।'],
  [/(\d+)%\s+of\s+recorded\s+support\s+outcomes\s+showed\s+improvement\.?/gi, 'दर्ज किए गए सहायता परिणामों में से $1% में सुधार देखा गया।'],
  [/(\d+)\s+of\s+(\d+)\s+outcomes\s+recorded\.?/gi, 'दर्ज किए गए $2 में से $1 परिणाम।'],
  [/On\s+track\s+grew\s+from\s+(\d+)\s+to\s+(\d+)\s+student-courses\.?/gi, 'सही दिशा वाले छात्र $1 से बढ़कर $2 हो गए।'],
  [/has\s+the\s+most\s+students\s+who\s+need\s+help/gi, 'में सबसे अधिक छात्रों को सहायता की ज़रूरत है'],
  [/(\d+)\s+active\s+students/gi, '$1 सक्रिय छात्र'],
  [/(\d+)\s+got\s+worse/gi, '$1 की स्थिति बिगड़ी'],
  [/(\d+)\s+improved/gi, '$1 में सुधार हुआ'],
  [/([+-]?\d+)\s+since\s+last\s+week/gi, 'पिछले सप्ताह से $1'],
  [/(\d+)\s+(?:in|of)\s+10\b/gi, '10 में से $1'],
  [/Week\s+(\d+)/gi, 'सप्ताह $1'],
  [/Term\s+Week\s+(\d+)/gi, 'सत्र का सप्ताह $1'],
  [/Day\s+(\d+)/gi, 'दिन $1'],
  [/Student\s+([A-Za-z0-9_-]+)/gi, 'छात्र $1'],

  // Recurring UI sentences
  [/Click\s+a\s+student\s+to\s+see\s+why\.?/gi, 'कारण देखने के लिए किसी छात्र पर क्लिक करें।'],
  [/No\s+change\s+since\s+last\s+week/gi, 'पिछले सप्ताह से कोई बदलाव नहीं'],
  [/None\s+this\s+week\.?/gi, 'इस सप्ताह कोई नहीं।'],
  [/Needs\s+at\s+least\s+two\s+weekly\s+checks\.?/gi, 'कम से कम दो साप्ताहिक जाँच आवश्यक हैं।'],
  [/student-courses/gi, 'छात्र-पाठ्यक्रम'],
  [/Search\s+by\s+student\s+or\s+owner/gi, 'छात्र या ज़िम्मेदार के अनुसार खोजें'],
  [/No\s+cases\s+yet/gi, 'अभी तक कोई केस नहीं'],
  [/No\s+cases\s+match/gi, 'कोई मेल खाता केस नहीं'],
  [/No\s+owner\s+yet/gi, 'अभी कोई ज़िम्मेदार नहीं'],
  [/Not\s+available\s+yet\.?/gi, 'अभी उपलब्ध नहीं है।'],
  [/Shown\s+once\s+counsellors\s+record\s+how\s+support\s+went\.?/gi, 'काउंसलर द्वारा सहायता दर्ज करने के बाद दिखाई देगा।'],
  [/Groups\s+smaller\s+than\s+5\s+show\s+as\s+“<5”\s+to\s+protect\s+student\s+privacy\.?/gi, 'छात्र गोपनीयता की रक्षा के लिए 5 से छोटे समूह “<5” के रूप में दिखाए जाते हैं।'],
  [/“8\s+in\s+10”\s+means\s+a\s+high\s+chance\s+this\s+student\s+struggles,\s+fails\s+or\s+drops\s+out\.?/gi, '“10 में से 8” का अर्थ है कि इस छात्र के संघर्ष करने, अनुत्तीर्ण होने या छोड़ने की उच्च संभावना है।'],
  [/Share\s+of\s+students\s+in\s+each\s+course\s+who\s+need\s+help\s+now\s+or\s+a\s+closer\s+look\.?/gi, 'प्रत्येक पाठ्यक्रम में उन छात्रों का अनुपात जिन्हें अभी सहायता या निगरानी की आवश्यकता है।'],
  [/Each\s+bar\s+is\s+one\s+weekly\s+check\s+of\s+every\s+student\.\s*Red\s+and\s+orange\s+shrinking\s+means\s+support\s+is\s+working\.?/gi, 'प्रत्येक बार हर छात्र की एक साप्ताहिक जाँच है। लाल और नारंगी का घटना सहायता के प्रभावी होने का संकेत है।'],
  [/Every\s+flagged\s+student\s+becomes\s+a\s+case\.\s*Counts\s+show\s+how\s+many\s+sit\s+at\s+each\s+step\.?/gi, 'प्रत्येक चिह्नित छात्र एक केस बन जाता है। संख्याएँ दर्शाती हैं कि कितने छात्र प्रत्येक चरण में हैं।'],
  [/Cases\s+with\s+no\s+owner\s+yet\s+need\s+someone\s+to\s+take\s+them\.?/gi, 'जिन केसों का अभी कोई ज़िम्मेदार नहीं है, उन्हें किसी को लेने की आवश्यकता है।'],
  [/Older\s+cases\s+need\s+attention\s+first\.?/gi, 'पुराने केसों पर पहले ध्यान देने की आवश्यकता है।'],
  [/Planned\s+check-ins\s+and\s+whether\s+they\s+happened\.?/gi, 'नियोजित चेक-इन और क्या वे संपन्न हुए।'],
  [/Import\s+your\s+student\s+data,\s+then\s+run\s+the\s+weekly\s+check\s+to\s+see\s+who\s+needs\s+support\.?/gi, 'अपने छात्र डेटा को आयात करें, फिर यह देखने के लिए साप्ताहिक जाँच चलाएँ कि किसे सहायता की आवश्यकता है।'],
  [/Cases\s+appear\s+when\s+the\s+weekly\s+check\s+flags\s+a\s+student\s+or\s+a\s+student\s+asks\s+for\s+help\.?/gi, 'केस तब दिखाई देते हैं जब साप्ताहिक जाँच किसी छात्र को चिह्नित करती है या कोई छात्र सहायता माँगता है।'],
]

function applyHindiTranslation(text: string, dict: Record<string, string>): string {
  const trimmed = text.trim()
  if (!trimmed) return text

  // 1. Direct dictionary match
  if (dict[trimmed]) {
    const leading = text.match(/^\s*/)?.[0] ?? ''
    const trailing = text.match(/\s*$/)?.[0] ?? ''
    return leading + dict[trimmed] + trailing
  }

  // 2. Trailing punctuation like ":" or "."
  const withoutPunct = trimmed.replace(/[:.?!]$/, '')
  if (dict[withoutPunct]) {
    const punct = trimmed.slice(withoutPunct.length)
    const leading = text.match(/^\s*/)?.[0] ?? ''
    const trailing = text.match(/\s*$/)?.[0] ?? ''
    return leading + dict[withoutPunct] + punct + trailing
  }

  // 3. Trailing numbers/counts, e.g. "Open 12", "Cases (4)", "Resolved 5"
  const countMatch = trimmed.match(/^(.*?)\s*(\(?\d+\)?)$/)
  if (countMatch && dict[countMatch[1].trim()]) {
    const translatedPrefix = dict[countMatch[1].trim()]
    const count = countMatch[2]
    const leading = text.match(/^\s*/)?.[0] ?? ''
    const trailing = text.match(/\s*$/)?.[0] ?? ''
    return leading + translatedPrefix + ' ' + count + trailing
  }

  // 4. Leading numbers, e.g. "84 active students", "3 got worse"
  const leadingNumMatch = trimmed.match(/^(\d+)\s+(.+)$/)
  if (leadingNumMatch && dict[leadingNumMatch[2].trim()]) {
    const num = leadingNumMatch[1]
    const translatedSuffix = dict[leadingNumMatch[2].trim()]
    const leading = text.match(/^\s*/)?.[0] ?? ''
    const trailing = text.match(/\s*$/)?.[0] ?? ''
    return leading + num + ' ' + translatedSuffix + trailing
  }

  // 5. Dynamic regex phrases
  let updated = text
  for (const [regex, replacement] of PHRASE_RULES) {
    if (regex.test(updated)) {
      updated = updated.replace(regex, replacement)
    }
  }

  return updated
}

function translateNode(node: Node, dict: Record<string, string>) {
  if (node.nodeType === Node.TEXT_NODE) {
    let original = originalTextMap.get(node)
    if (original === undefined) {
      original = node.nodeValue ?? ''
      originalTextMap.set(node, original)
    }
    const target = applyHindiTranslation(original, dict)
    if (node.nodeValue !== target) {
      node.nodeValue = target
    }
    return
  }

  const el = node as Element
  const tag = el.tagName
  if (
    tag === 'SCRIPT' ||
    tag === 'STYLE' ||
    tag === 'CODE' ||
    tag === 'PRE'
  ) {
    return
  }

  if (tag === 'INPUT' || tag === 'TEXTAREA') {
    const ph = el.getAttribute('placeholder')
    if (ph && dict[ph.trim()]) {
      el.setAttribute('placeholder', dict[ph.trim()])
    }
    return
  }

  if (el.getAttribute) {
    const titleAttr = el.getAttribute('title')
    if (titleAttr && dict[titleAttr.trim()]) {
      el.setAttribute('title', dict[titleAttr.trim()])
    }
  }

  for (let i = 0; i < node.childNodes.length; i++) {
    translateNode(node.childNodes[i], dict)
  }
}

function restoreNode(node: Node) {
  if (node.nodeType === Node.TEXT_NODE) {
    const original = originalTextMap.get(node)
    if (original !== undefined && node.nodeValue !== original) {
      node.nodeValue = original
    }
    return
  }
  const el = node as Element
  const tag = el.tagName
  if (tag === 'SCRIPT' || tag === 'STYLE') return
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
      let isTranslating = false
      const observer = new MutationObserver((mutations) => {
        if (isTranslating) return
        isTranslating = true
        try {
          for (const m of mutations) {
            if (m.type === 'childList') {
              m.addedNodes.forEach((n) => translateNode(n, HI))
            } else if (m.type === 'characterData' && m.target) {
              translateNode(m.target, HI)
            }
          }
        } finally {
          isTranslating = false
        }
      })
      observer.observe(document.body, { childList: true, subtree: true, characterData: true })
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
