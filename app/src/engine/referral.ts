import type { Check, Decision, ParsedReferral } from './types.ts'

const REFERRAL_RE =
  /^JANI1 M:([A-Z0-9]+) P:([A-Z0-9]+) D:(\d{8}) N:(\d+) R:(\d+) C:(\d+) H:(\d+) L:(\d+) U:(\d+) A:([a-z0-9_]+) Q:(\d{1,3}) X:(act|wait|ask)$/

export function buildReferral(check: Check): string {
  const member = gsm(check.memberId || 'NA', 12)
  const plot = gsm(check.plotId || 'NA', 8)
  const day = yyyymmdd(check.createdAt)
  const counts = check.summary.counts
  const decision: Decision = check.decision ?? 'ask'
  const confidence = confidencePct(check)
  const answerId = check.answerId.replace(/[^a-z0-9_]/g, '').slice(0, 32) || 'ask_officer'
  const body = [
    'JANI1',
    `M:${member}`,
    `P:${plot}`,
    `D:${day}`,
    `N:${check.summary.n}`,
    `R:${counts.rust}`,
    `C:${counts.cercospora}`,
    `H:${counts.phoma}`,
    `L:${counts.miner}`,
    `U:${check.summary.uncertain}`,
    `A:${answerId}`,
    `Q:${confidence}`,
    `X:${decision}`,
  ].join(' ')
  if (body.length > 160) {
    throw new Error(`Referral is ${body.length} characters`)
  }
  return body
}

export function smsLink(number: string, body: string): string {
  const cleaned = number.replace(/[^\d+]/g, '')
  return `sms:${cleaned}?body=${encodeURIComponent(body)}`
}

export function parseReferral(text: string): ParsedReferral | null {
  const match = REFERRAL_RE.exec(text.trim())
  if (!match) return null
  return {
    memberId: match[1] ?? '',
    plotId: match[2] ?? '',
    date: match[3] ?? '',
    n: Number(match[4]),
    rust: Number(match[5]),
    cercospora: Number(match[6]),
    phoma: Number(match[7]),
    miner: Number(match[8]),
    uncertain: Number(match[9]),
    answerId: match[10] ?? '',
    confidence: Number(match[11]),
    decision: (match[12] ?? 'ask') as Decision,
  }
}

export function confidencePct(check: Check): number {
  const accepted = check.leaves.filter((leaf) => !leaf.abstained)
  if (!accepted.length) return 0
  const mean = accepted.reduce((sum, leaf) => sum + leaf.confidence, 0) / accepted.length
  return Math.max(0, Math.min(100, Math.round(mean * 100)))
}

function gsm(value: string, max: number): string {
  const cleaned = value.toUpperCase().replace(/[^A-Z0-9]/g, '')
  return (cleaned || 'NA').slice(0, max)
}

function yyyymmdd(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '19700101'
  const y = date.getFullYear().toString().padStart(4, '0')
  const m = (date.getMonth() + 1).toString().padStart(2, '0')
  const d = date.getDate().toString().padStart(2, '0')
  return `${y}${m}${d}`
}
