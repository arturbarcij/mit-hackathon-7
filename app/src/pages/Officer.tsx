import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { AppFrame } from '../components/AppFrame'
import { parseReferral } from '../engine'

type OfficerStatus = 'new' | 'confirmed' | 'visit'

interface QueueItem {
  id: string
  memberId: string
  plotId: string
  date: string
  n: number
  rust: number
  cercospora: number
  phoma: number
  miner: number
  unsure: number
  answerId: string
  confidence: number
  decision: string
  synthetic: boolean
  status: OfficerStatus
}

const SEED: QueueItem[] = [
  {
    id: 'seed-occ0001',
    memberId: 'OCC0001',
    plotId: '1',
    date: '20261001',
    n: 10,
    rust: 2,
    cercospora: 0,
    phoma: 0,
    miner: 0,
    unsure: 1,
    answerId: 'rust_low',
    confidence: 70,
    decision: 'wait',
    synthetic: true,
    status: 'new',
  },
  {
    id: 'seed-occ0002',
    memberId: 'OCC0002',
    plotId: '2',
    date: '20261002',
    n: 10,
    rust: 8,
    cercospora: 0,
    phoma: 0,
    miner: 0,
    unsure: 1,
    answerId: 'rust_high_pre_rains',
    confidence: 84,
    decision: 'ask',
    synthetic: true,
    status: 'new',
  },
  {
    id: 'seed-occ0003',
    memberId: 'OCC0003',
    plotId: '3',
    date: '20261003',
    n: 10,
    rust: 4,
    cercospora: 1,
    phoma: 0,
    miner: 0,
    unsure: 2,
    answerId: 'mixed_problems',
    confidence: 61,
    decision: 'ask',
    synthetic: true,
    status: 'new',
  },
]

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return null
}

function pickString(record: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function pickNumber(record: Record<string, unknown>, keys: string[]): number {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) {
      return Number(value)
    }
  }
  return 0
}

function toQueueItem(parsed: unknown, synthetic: boolean): QueueItem | null {
  const record = asRecord(parsed)
  if (!record) return null
  const summary = asRecord(record.summary)
  const counts = asRecord(record.counts) ?? (summary ? asRecord(summary.counts) : null) ?? record
  const source = summary ?? record
  return {
    id: `paste-${Date.now()}-${Math.floor(Math.random() * 10000)}`,
    memberId: pickString(record, ['memberId', 'member', 'm']),
    plotId: pickString(record, ['plotId', 'plot', 'p']),
    date: pickString(record, ['date', 'checkDate', 'd', 'createdAt']),
    n: pickNumber(source, ['n']) || pickNumber(record, ['n']),
    rust: pickNumber(counts, ['rust', 'r']),
    cercospora: pickNumber(counts, ['cercospora', 'cerco', 'c']),
    phoma: pickNumber(counts, ['phoma', 'h']),
    miner: pickNumber(counts, ['miner', 'l']),
    unsure:
      pickNumber(record, ['unsure', 'uncertain', 'u']) ||
      pickNumber(source, ['uncertain', 'unsure']),
    answerId: pickString(record, ['answerId', 'answer', 'a']),
    confidence: pickNumber(record, ['confidence', 'conf', 'q']),
    decision: pickString(record, ['decision', 'x']),
    synthetic,
    status: 'new',
  }
}

function formatReferralDate(value: string): string {
  const match = /^(\d{4})(\d{2})(\d{2})$/.exec(value)
  if (!match) return value
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function statusLine(status: OfficerStatus): string {
  if (status === 'confirmed') return 'Confirmed'
  if (status === 'visit') return 'Needs a visit'
  return 'New'
}

export default function OfficerPage() {
  const [items, setItems] = useState<QueueItem[]>(SEED)
  const [paste, setPaste] = useState('')
  const [syntheticPaste, setSyntheticPaste] = useState(true)
  const [error, setError] = useState('')

  function onParse() {
    const parsed = parseReferral(paste)
    if (!parsed) {
      setError('The message was not understood.')
      return
    }
    const item = toQueueItem(parsed, syntheticPaste)
    if (!item) {
      setError('The message was not understood.')
      return
    }
    setError('')
    setItems((current) => [item, ...current])
    setPaste('')
  }

  function setStatus(id: string, status: OfficerStatus) {
    setItems((current) => current.map((item) => (item.id === id ? { ...item, status } : item)))
  }

  const sorted = [...items].sort((a, b) => b.rust - a.rust)

  return (
    <AppFrame>
      <p className="warn">Simulated officer view. Not a live extension system.</p>
      <h1>Referrals</h1>
      <p>Simulated SMS path. Paste a message. Nothing is sent on a network.</p>
      <label className="field">
        <span>Paste the SMS</span>
        <textarea
          value={paste}
          onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setPaste(event.target.value)}
          rows={4}
          spellCheck={false}
          autoComplete="off"
        />
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={syntheticPaste}
          onChange={(event) => setSyntheticPaste(event.target.checked)}
        />
        <span>This sample is synthetic</span>
      </label>
      <button type="button" className="btn btn-primary" onClick={onParse}>
        Parse
      </button>
      {error ? <p role="alert">{error}</p> : null}
      <ul className="list">
        {sorted.map((item) => (
          <li key={item.id}>
            <article className="card">
              <p>Member {item.memberId || 'No member number'}</p>
              <p>Plot {item.plotId || 'No plot'}</p>
              <p>Date {formatReferralDate(item.date) || 'No date'}</p>
              <p>
                Rust {item.rust} of {item.n}. Brown eye spot {item.cercospora}. Phoma {item.phoma}. Leaf miner{' '}
                {item.miner}. Not sure {item.unsure}.
              </p>
              {item.answerId ? <p>Answer {item.answerId}</p> : null}
              <p>Confidence {item.confidence}</p>
              <p>Status {statusLine(item.status)}</p>
              {item.synthetic ? <p className="tag">synthetic</p> : null}
              <div className="actions">
                <button type="button" className="btn btn-primary" onClick={() => setStatus(item.id, 'confirmed')}>
                  Confirm
                </button>
                <button type="button" className="btn btn-quiet" onClick={() => setStatus(item.id, 'visit')}>
                  Needs a visit
                </button>
              </div>
            </article>
          </li>
        ))}
      </ul>
      <p>Map not in this build.</p>
    </AppFrame>
  )
}
