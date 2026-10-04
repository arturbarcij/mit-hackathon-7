import { useEffect, useState } from 'react'
import { checkPin, clearPin, hasPin, listChecks, setPin, type Check } from '../engine/index.ts'
import { t } from '../i18n.ts'
import { useLang } from '../lang.tsx'

const UNLOCK = 'jani-unlocked'

export function HistoryPage() {
  const { lang } = useLang()
  const [rows, setRows] = useState<Check[] | null>(null)
  const [locked, setLocked] = useState(false)
  const [pinOn, setPinOn] = useState(false)
  const [pin, setPinValue] = useState('')
  const [error, setError] = useState(false)
  const [draft, setDraft] = useState('')

  async function load() {
    const enabled = await hasPin()
    setPinOn(enabled)
    const open = sessionStorage.getItem(UNLOCK) === 'yes'
    if (enabled && !open) {
      setLocked(true)
      setRows([])
      return
    }
    setLocked(false)
    setRows(await listChecks())
  }

  useEffect(() => {
    void load()
  }, [])

  async function unlock() {
    const ok = await checkPin(pin)
    setError(!ok)
    if (!ok) return
    sessionStorage.setItem(UNLOCK, 'yes')
    setPinValue('')
    await load()
  }

  async function saveNewPin() {
    if (!/^\d{4}$/.test(draft)) return
    await setPin(draft)
    setDraft('')
    sessionStorage.setItem(UNLOCK, 'yes')
    await load()
  }

  return (
    <section>
      <h1>{t(lang, 'history_title')}</h1>
      {locked && (
        <>
          <label>
            {t(lang, 'pin_enter')}
            <input value={pin} onChange={(event) => setPinValue(event.target.value)} inputMode="numeric" maxLength={4} />
          </label>
          <button type="button" className="primary" onClick={() => void unlock()}>
            {t(lang, 'unlock')}
          </button>
          {error && <p className="note warn">{t(lang, 'pin_wrong')}</p>}
        </>
      )}
      {!locked && rows && rows.length === 0 && <p className="lead">{t(lang, 'history_empty')}</p>}
      {!locked && rows && rows.length > 0 && (
        <ul className="queue">
          {rows.map((row) => (
            <li key={row.id} className="plain">
              <p>
                {new Date(row.createdAt).toLocaleDateString(lang === 'en' ? 'en-GB' : 'sw-KE')} · {row.answerId}
              </p>
              <p className="note">
                {row.decision ?? ''} · {row.summary.affected}/{row.summary.n} · {row.window}
                {row.synthetic ? ` · ${t(lang, 'synthetic')}` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
      {!locked && (
        <>
          <h2>{t(lang, 'pin_set')}</h2>
          <p className="note">{t(lang, 'pin_optional')}</p>
          <label>
            {t(lang, 'pin_enter')}
            <input value={draft} onChange={(event) => setDraft(event.target.value)} inputMode="numeric" maxLength={4} />
          </label>
          <button type="button" className="secondary" onClick={() => void saveNewPin()}>
            {t(lang, 'pin_save')}
          </button>
          {pinOn && (
            <button
              type="button"
              className="secondary"
              onClick={() => {
                void clearPin().then(() => {
                  sessionStorage.removeItem(UNLOCK)
                  return load()
                })
              }}
            >
              {t(lang, 'clear_pin')}
            </button>
          )}
        </>
      )}
    </section>
  )
}
