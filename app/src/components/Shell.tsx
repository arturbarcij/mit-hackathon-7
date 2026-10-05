import { useState, type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { play } from '../engine/audio.ts'
import { useEngine } from '../hooks/useEngine.ts'
import { t } from '../i18n.ts'
import { useLang } from '../lang.tsx'
import { Mark } from './Icons.tsx'

export function Shell({ children }: { children: ReactNode }) {
  const { lang } = useLang()
  const { online, model } = useEngine()
  return (
    <div className="app">
      <header className="top">
        <p className="brand">Jani</p>
        <p className={online ? 'pill ok' : 'pill off'}>{online ? t(lang, 'online') : t(lang, 'offline')}</p>
        {model.mock && <p className="pill mock">{t(lang, 'mock_badge')}</p>}
        {lang === 'kik' && <p className="banner">{t(lang, 'kik_review')}</p>}
      </header>
      <main>{children}</main>
      <nav className="tabs">
        <NavLink to="/" end>
          {t(lang, 'nav_check')}
        </NavLink>
        <NavLink to="/history">{t(lang, 'nav_history')}</NavLink>
        <NavLink to="/sources">{t(lang, 'nav_sources')}</NavLink>
        <NavLink to="/officer">{t(lang, 'nav_officer')}</NavLink>
      </nav>
    </div>
  )
}

export function Speak({ answerId }: { answerId: string }) {
  const { lang } = useLang()
  const [missing, setMissing] = useState(false)
  return (
    <div className="speak">
      <button
        type="button"
        className="secondary"
        onClick={() => {
          void play(answerId, lang).then((ok) => setMissing(!ok))
        }}
      >
        <Mark kind="speaker" />
        <span>{t(lang, 'play')}</span>
      </button>
      {missing && <p className="note">{t(lang, 'audio_missing')}</p>}
    </div>
  )
}
