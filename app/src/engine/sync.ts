// Store-and-forward to the officer dashboard. The UI owns the Supabase client and injects a sender.
// Nothing here runs on import or on a timer: the UI calls queueForSync after Noor taps
// "Ask the officer" and confirms sharing, and calls syncPending itself.
// Rows carry the member number, never a name. Photos go only with the second consent.
import type { Check, ReferralRow, SyncSender } from './types';
import { getCheck, getConsent, markSynced, queueAdd, queueList, queueRemove, readPhotos, saveCheck } from './storage';
import { cleanId } from './referral';

let sender: SyncSender | null = null;
let running: Promise<number> | null = null;

export function setSyncSender(fn: SyncSender | null): void {
  sender = fn;
}

/** Save the check and queue it once. No-op without main consent. */
export async function queueForSync(c: Check): Promise<void> {
  if (!c.consentMain) return;
  await saveCheck(c);
  await queueAdd(c.id);
}

function localDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Mean confidence of accepted leaves (not unsure, not abstained, not not_leaf), 2 decimals, or null. */
function meanConfidence(c: Check): number | null {
  const ok = c.leaves.filter((l) => !l.abstained && l.label !== 'unsure' && l.label !== 'not_leaf');
  if (ok.length === 0) return null;
  const mean = ok.reduce((s, l) => s + l.confidence, 0) / ok.length;
  return Math.round(mean * 100) / 100;
}

/** Same normalisation as the SMS (uppercase A-Z 0-9 '-', max 12), so row and parsed SMS match. */
function rowId(v: string | undefined): string | null {
  const id = cleanId(v);
  return id === '-' ? null : id;
}

/** Explicit field list so nothing else on the check (and never a name) reaches the backend. */
export function toReferralRow(c: Check): ReferralRow {
  return {
    member_id: rowId(c.memberId),
    plot_id: rowId(c.plotId),
    check_date: localDate(c.createdAt),
    counts: { ...c.summary.counts },
    uncertain: c.summary.uncertain,
    answer_id: c.answerId,
    confidence: meanConfidence(c),
    decision: c.decision ?? null,
    photos_shared: c.consentPhotos,
    synthetic: false,
  };
}

async function drain(send: SyncSender): Promise<number> {
  let n = 0;
  const consent = await getConsent();
  for (const id of await queueList()) {
    const c = await getCheck(id);
    if (!c || !c.consentMain) {
      await queueRemove(id);
      continue;
    }
    // Photos need the second consent on the check and still in force now.
    const share = c.consentPhotos && consent.photos;
    const photos = share ? await readPhotos(id) : [];
    try {
      await send(toReferralRow({ ...c, consentPhotos: share }), photos);
    } catch {
      break; // keep this and the rest queued, in order
    }
    await markSynced(id);
    n++;
  }
  return n;
}

/** Push queued checks in order. Returns how many were sent; 0 without a sender or when offline. */
export async function syncPending(): Promise<number> {
  const send = sender;
  if (!send) return 0;
  if (typeof navigator === 'undefined' || navigator.onLine === false) return 0;
  if (running) return running; // one drain at a time, so nothing is sent twice
  running = drain(send).finally(() => {
    running = null;
  });
  return running;
}
