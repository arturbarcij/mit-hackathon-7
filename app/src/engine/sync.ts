import type { Check, LeafResult } from './types.ts';
import { getConsent, listChecks, saveCheck } from './storage.ts';

type LeafRecord = LeafResult & { photo?: Blob };

export function canSync(online: boolean, consent: { main: boolean; photos: boolean }, url: string | undefined): boolean {
  return online && consent.main && consent.photos && typeof url === 'string' && url.length > 0;
}

export function withoutPhotos(check: Check): Check {
  return {
    ...check,
    leaves: check.leaves.map((leaf) => {
      const copy = { ...leaf } as LeafRecord;
      delete copy.photo;
      return copy;
    }),
  };
}

function isOnline(): boolean {
  if (typeof navigator === 'undefined' || typeof navigator.onLine !== 'boolean') return false;
  return navigator.onLine;
}

function syncEndpoint(): string {
  const url = import.meta.env.VITE_SYNC_URL;
  return typeof url === 'string' ? url : '';
}

export async function syncPending(): Promise<number> {
  const consent = await getConsent();
  const url = syncEndpoint();
  if (!canSync(isOnline(), consent, url)) return 0;
  const pending = (await listChecks()).filter((check) => !check.synced);
  if (pending.length === 0) return 0;
  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ checks: pending.map(withoutPhotos) }),
    });
  } catch {
    return 0;
  }
  if (!response.ok) return 0;
  for (const check of pending) await saveCheck({ ...check, synced: true });
  return pending.length;
}
