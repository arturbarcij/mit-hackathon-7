import { listChecks, saveCheck } from './storage.ts'

/**
 * Store-and-forward. Photos leave the phone only when consentPhotos is set.
 * If VITE_SYNC_URL is empty, nothing is sent and the checks stay on the phone.
 * There is no automatic send: the caller is a tap that already saved the check.
 */
export async function syncPending(): Promise<number> {
  const url = import.meta.env.VITE_SYNC_URL
  if (!url || (typeof navigator !== 'undefined' && !navigator.onLine)) return 0
  const pending = (await listChecks()).filter((check) => !check.synced && check.consentMain)
  let synced = 0
  for (const check of pending) {
    const body = {
      id: check.id,
      createdAt: check.createdAt,
      memberId: check.memberId,
      plotId: check.plotId,
      answerId: check.answerId,
      decision: check.decision,
      summary: check.summary,
      window: check.window,
      consentPhotos: check.consentPhotos,
      synthetic: check.synthetic,
      leaves: check.consentPhotos ? check.leaves : check.leaves.map((leaf) => ({ ...leaf })),
    }
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) continue
      await saveCheck({ ...check, synced: true })
      synced++
    } catch {
      continue
    }
  }
  return synced
}
