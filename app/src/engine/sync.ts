import { checkDate, meanConfidencePercent } from './referral';
import { getCheck, getConsent, markSynced, outboxIds } from './storage';
import type { Check } from './types';

/** Row shape of the `referrals` table (see kb/agents/ui.md). */
export interface ReferralRow {
  created_at: string;
  member_id: string | null;
  plot_id: string | null;
  check_date: string;
  counts: Record<string, number>;
  uncertain: number;
  answer_id: string;
  confidence: number;
  photos_shared: boolean;
  photo_urls: string[];
  status: 'new';
  synthetic: false;
}

export interface SyncTarget {
  /** Inserts one referral row. Must reject on any failure so the check stays queued. */
  insert(row: ReferralRow): Promise<void>;
  /** Optional. Only called when both the check and the stored consent allow photo sharing. Returns public URLs. */
  uploadPhotos?(check: Check): Promise<string[]>;
}

let target: SyncTarget | null = null;

export function configureSync(t: SyncTarget | null): void {
  target = t;
}

/**
 * Default target: Supabase REST insert into `referrals`, using the public (publishable) key,
 * which is meant to be shipped to browsers. Row level security lets the farmer app insert only.
 */
function defaultTarget(): SyncTarget | null {
  const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
  const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;
  if (!url || !key) return null;
  return {
    async insert(row) {
      const res = await fetch(`${url.replace(/\/$/, '')}/rest/v1/referrals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          apikey: key,
          Authorization: `Bearer ${key}`,
          Prefer: 'return=minimal',
        },
        body: JSON.stringify(row),
      });
      if (!res.ok) throw new Error(`Sync failed: HTTP ${res.status}`);
    },
  };
}

export function toReferralRow(check: Check, photoUrls: string[]): ReferralRow {
  return {
    created_at: check.createdAt,
    member_id: check.memberId ?? null,
    plot_id: check.plotId ?? null,
    check_date: checkDate(check.createdAt),
    counts: { ...check.summary.counts },
    uncertain: check.summary.uncertain,
    answer_id: check.answerId,
    confidence: meanConfidencePercent(check) / 100,
    photos_shared: photoUrls.length > 0,
    photo_urls: photoUrls,
    status: 'new',
    synthetic: false,
  };
}

/**
 * Store and forward. Pushes queued checks when the browser is online and the main consent is on.
 * A check is only queued when the farmer chose "ask the officer" (see storage.isSyncEligible).
 * Photos are uploaded only if the farmer gave the second consent, both stored and on the check.
 * Returns how many checks were synced. Failures leave the check queued for the next try.
 */
export async function syncPending(): Promise<number> {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) return 0;
  const t = target ?? defaultTarget();
  if (!t) return 0;
  const consent = await getConsent();
  if (!consent.main) return 0;

  let synced = 0;
  for (const id of await outboxIds()) {
    const check = await getCheck(id);
    if (!check || !check.consentMain || check.decision !== 'ask' || check.synced) continue;
    try {
      let urls: string[] = [];
      if (consent.photos && check.consentPhotos && t.uploadPhotos) urls = await t.uploadPhotos(check);
      await t.insert(toReferralRow(check, urls));
      await markSynced(id);
      synced += 1;
    } catch {
      // Keep it queued; try again next time we are online.
    }
  }
  return synced;
}
