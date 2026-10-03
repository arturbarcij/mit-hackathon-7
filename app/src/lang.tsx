import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Lang } from './engine/types.ts'

const KEY = 'jani-lang'

interface LangValue {
  lang: Lang
  setLang: (lang: Lang) => void
}

const LangContext = createContext<LangValue>({ lang: 'sw', setLang: () => undefined })

function storedLang(): Lang {
  if (typeof localStorage === 'undefined') return 'sw'
  const value = localStorage.getItem(KEY)
  if (value === 'sw' || value === 'kik' || value === 'en') return value
  return 'sw'
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(storedLang)
  function setLang(next: Lang) {
    localStorage.setItem(KEY, next)
    setLangState(next)
  }
  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>
}

export function useLang(): LangValue {
  return useContext(LangContext)
}
