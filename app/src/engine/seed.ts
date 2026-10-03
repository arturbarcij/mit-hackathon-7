import { listReferrals, saveReferral, type StoredReferral } from './storage.ts'

const ROWS: Array<Omit<StoredReferral, 'id' | 'createdAt'>> = [
  row('SYN01', '2', '20261001', 6, 0, 0, 0, 1, 'rust_high_pre_rains', 88, 'ask'),
  row('SYN02', '1', '20261002', 2, 0, 0, 0, 0, 'rust_low', 81, 'wait'),
  row('SYN03', '4', '20260928', 0, 0, 0, 0, 4, 'too_many_unsure', 40, 'ask'),
  row('SYN04', '3', '20261003', 0, 5, 0, 0, 0, 'cercospora', 76, 'ask'),
  row('SYN05', '1', '20260920', 0, 0, 4, 0, 1, 'phoma', 70, 'ask'),
  row('SYN06', '5', '20261001', 0, 0, 0, 6, 0, 'miner', 84, 'ask'),
  row('SYN07', '2', '20260915', 3, 3, 0, 0, 0, 'mixed_problems', 73, 'ask'),
  row('SYN08', '6', '20261002', 0, 0, 0, 0, 0, 'healthy_all', 91, 'wait'),
  row('SYN09', '1', '20260712', 7, 0, 0, 0, 0, 'rust_high_dry', 86, 'ask'),
  row('SYN10', '8', '20261004', 4, 0, 0, 1, 2, 'rust_high_pre_rains', 79, 'act'),
  row('SYN11', '3', '20261112', 5, 0, 0, 0, 0, 'rust_high_in_rains', 83, 'wait'),
  row('SYN12', '7', '20261003', 0, 0, 0, 0, 6, 'too_many_unsure', 22, 'ask'),
  row('SYN13', '2', '20260225', 4, 0, 0, 0, 0, 'rust_high_pre_rains', 85, 'act'),
  row('SYN14', '9', '20260930', 1, 0, 0, 0, 0, 'rust_low', 77, 'wait'),
  row('SYN15', '4', '20261002', 0, 0, 0, 2, 1, 'miner', 68, 'ask'),
  row('SYN16', '1', '20260802', 0, 0, 0, 0, 1, 'ask_officer', 30, 'ask'),
]

function row(
  memberId: string,
  plotId: string,
  checkDate: string,
  rust: number,
  cercospora: number,
  phoma: number,
  miner: number,
  uncertain: number,
  answerId: string,
  confidence: number,
  decision: StoredReferral['decision'],
): Omit<StoredReferral, 'id' | 'createdAt'> {
  const n = 10
  const healthy = Math.max(0, n - rust - cercospora - phoma - miner - uncertain)
  const sms = `JANI1 M:${memberId} P:${plotId} D:${checkDate} N:${n} R:${rust} C:${cercospora} H:${phoma} L:${miner} U:${uncertain} A:${answerId} Q:${confidence} X:${decision}`
  return {
    memberId,
    plotId,
    checkDate,
    counts: { rust, cercospora, phoma, miner, healthy, not_leaf: 0 },
    uncertain,
    answerId,
    confidence,
    photosShared: false,
    status: 'new',
    synthetic: true,
    sms,
    decision,
  }
}

export async function seedReferralsIfEmpty(): Promise<void> {
  const existing = await listReferrals()
  const ids = new Set(existing.map((item) => item.id))
  for (let i = 0; i < ROWS.length; i++) {
    const item = ROWS[i]
    if (!item) continue
    const id = `syn-${String(i + 1).padStart(2, '0')}`
    if (ids.has(id)) continue
    await saveReferral({
      ...item,
      id,
      createdAt: `${item.checkDate.slice(0, 4)}-${item.checkDate.slice(4, 6)}-${item.checkDate.slice(6, 8)}T08:00:00.000Z`,
    })
  }
}

export function urgency(referral: StoredReferral): number {
  let score = 0
  if (referral.uncertain >= 3 || referral.answerId === 'ask_officer' || referral.answerId === 'too_many_unsure') score += 2
  if (referral.counts.rust >= 3) score += 1
  if (referral.status === 'new') score += 1
  return score
}
