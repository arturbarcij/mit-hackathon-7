import { useEffect, useState } from 'react'
import { LABELS, parseReferral, type Label } from '../engine/index.ts'
import { seedReferralsIfEmpty, urgency } from '../engine/seed.ts'
import {
  listCorrections,
  listReferrals,
  saveCorrection,
  saveReferral,
  type Correction,
  type StoredReferral,
} from '../engine/storage.ts'
import { t } from '../i18n.ts'
import { useLang } from '../lang.tsx'

export function OfficerPage() {
  const { lang } = useLang()
  const [rows, setRows] = useState<StoredReferral[]>([])
  const [corrections, setCorrections] = useState<Correction[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [paste, setPaste] = useState('')
  const [pasteError, setPasteError] = useState(false)
  const [officerId, setOfficerId] = useState('officer')
  const [leafIndex, setLeafIndex] = useState(1)
  const [modelLabel, setModelLabel] = useState<string>('rust')
  const [officerLabel, setOfficerLabel] = useState<string>('rust')
  const [savedNote, setSavedNote] = useState(false)

  async function reload() {
    const [referrals, notes] = await Promise.all([listReferrals(), listCorrections()])
    referrals.sort((a, b) => urgency(b) - urgency(a) || (a.createdAt < b.createdAt ? 1 : -1))
    setRows(referrals)
    setCorrections(notes)
  }

  useEffect(() => {
    void seedReferralsIfEmpty().then(reload)
  }, [])

  const current = rows.find((row) => row.id === selected) ?? null

  async function addPasted() {
    const parsed = parseReferral(paste)
    if (!parsed) {
      setPasteError(true)
      return
    }
    setPasteError(false)
    await saveReferral({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      memberId: parsed.memberId,
      plotId: parsed.plotId,
      checkDate: parsed.date,
      counts: {
        rust: parsed.rust,
        cercospora: parsed.cercospora,
        phoma: parsed.phoma,
        miner: parsed.miner,
        healthy: 0,
        not_leaf: 0,
      },
      uncertain: parsed.uncertain,
      answerId: parsed.answerId,
      confidence: parsed.confidence,
      photosShared: false,
      status: 'new',
      synthetic: parsed.memberId.startsWith('SYN'),
      sms: paste.trim(),
      decision: parsed.decision,
    })
    setPaste('')
    await reload()
  }

  async function setStatus(status: StoredReferral['status']) {
    if (!current) return
    await saveReferral({ ...current, status })
    await reload()
  }

  async function correct() {
    if (!current) return
    await saveCorrection({
      id: crypto.randomUUID(),
      referralId: current.id,
      leafIndex,
      modelLabel,
      officerLabel,
      officerId: officerId.trim() || 'officer',
      createdAt: new Date().toISOString(),
    })
    setSavedNote(true)
    await reload()
  }

  function exportCsv() {
    const header = 'referral_id,leaf_index,model_label,officer_label,officer_id,created_at'
    const lines = corrections.map((item) =>
      [item.referralId, item.leafIndex, item.modelLabel, item.officerLabel, item.officerId, item.createdAt].join(','),
    )
    const blob = new Blob([[header, ...lines].join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'jani-corrections.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  if (current) {
    return (
      <section>
        <p className="banner">{t(lang, 'officer_sim')}</p>
        <button type="button" className="secondary" onClick={() => setSelected(null)}>
          {t(lang, 'back_queue')}
        </button>
        <h1>
          {current.memberId} / {current.plotId}
        </h1>
        {current.synthetic && <p className="pill mock">{t(lang, 'synthetic')}</p>}
        <p className="note">{t(lang, 'simulated_tag')}</p>
        <p className="lead">
          {current.checkDate} · {current.answerId} · {t(lang, 'confidence')} {current.confidence}% · {t(lang, 'uncertain_count')}{' '}
          {current.uncertain}
        </p>
        <p className="sms">{current.sms}</p>
        <p className="note">{t(lang, 'no_gps')}</p>
        <p className="note">{t(lang, 'photos_kept')}</p>
        <div className="stack">
          <button type="button" className="primary" onClick={() => void setStatus('confirmed')}>
            {t(lang, 'confirm')}
          </button>
          <button type="button" className="danger" onClick={() => void setStatus('visit')}>
            {t(lang, 'visit')}
          </button>
        </div>
        <h2>{t(lang, 'correct')}</h2>
        <label>
          {t(lang, 'officer_name')}
          <input value={officerId} onChange={(event) => setOfficerId(event.target.value)} />
        </label>
        <label>
          {t(lang, 'leaf_index')}
          <input
            type="number"
            min={1}
            max={10}
            value={leafIndex}
            onChange={(event) => setLeafIndex(Number(event.target.value))}
          />
        </label>
        <label>
          {t(lang, 'model_label')}
          <select value={modelLabel} onChange={(event) => setModelLabel(event.target.value)}>
            {options()}
          </select>
        </label>
        <label>
          {t(lang, 'officer_label')}
          <select value={officerLabel} onChange={(event) => setOfficerLabel(event.target.value)}>
            {options()}
          </select>
        </label>
        <button type="button" className="primary" onClick={() => void correct()}>
          {t(lang, 'save_correction')}
        </button>
        {savedNote && <p className="note">{t(lang, 'correction_saved')}</p>}
      </section>
    )
  }

  return (
    <section>
      <h1>{t(lang, 'nav_officer')}</h1>
      <p className="banner">{t(lang, 'officer_sim')}</p>
      <p className="note">{t(lang, 'no_gps')}</p>
      <h2>{t(lang, 'paste_label')}</h2>
      <label>
        {t(lang, 'paste_sms')}
        <textarea value={paste} onChange={(event) => setPaste(event.target.value)} rows={3} />
      </label>
      <button type="button" className="secondary" onClick={() => void addPasted()}>
        {t(lang, 'add_pasted')}
      </button>
      {pasteError && <p className="note warn">{t(lang, 'parse_fail')}</p>}
      {rows.length === 0 && <p className="lead">{t(lang, 'officer_empty')}</p>}
      <ul className="queue">
        {rows.map((row) => (
          <li key={row.id}>
            <button type="button" className="secondary" onClick={() => setSelected(row.id)}>
              <span>
                {row.memberId} · {row.plotId} · {statusText(lang, row.status)}
              </span>
              <span>
                R{row.counts.rust} U{row.uncertain} {row.answerId}
              </span>
              {row.synthetic && <span className="pill mock">{t(lang, 'synthetic')}</span>}
            </button>
          </li>
        ))}
      </ul>
      <h2>{t(lang, 'export')}</h2>
      {corrections.length === 0 && <p className="note">{t(lang, 'no_corrections')}</p>}
      <button type="button" className="secondary" onClick={exportCsv} disabled={corrections.length === 0}>
        {t(lang, 'export')}
      </button>
    </section>
  )
}

function options() {
  const labels: Array<Label | 'unsure'> = [...LABELS, 'unsure']
  return labels.map((label) => (
    <option key={label} value={label}>
      {label}
    </option>
  ))
}

function statusText(lang: Parameters<typeof t>[0], status: StoredReferral['status']): string {
  if (status === 'confirmed') return t(lang, 'status_confirmed')
  if (status === 'visit') return t(lang, 'status_visit')
  return t(lang, 'status_new')
}
