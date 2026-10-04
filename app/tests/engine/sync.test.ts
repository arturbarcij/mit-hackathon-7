import 'fake-indexeddb/auto';
import { IDBFactory } from 'fake-indexeddb';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Check, LeafResult, ReferralRow } from '../../src/engine/types';
import {
  _resetStorageForTests,
  getCheck,
  queueList,
  savePhoto,
  setConsent,
} from '../../src/engine/storage';
import { queueForSync, setSyncSender, syncPending, toReferralRow } from '../../src/engine/sync';

const probs = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
const q = { ok: true, blur: 100, brightness: 120 };
const leaf = (label: LeafResult['label'], confidence: number, abstained = false): LeafResult => ({
  label,
  probs,
  confidence,
  quality: q,
  abstained,
  modelVersion: 'mock',
});

function makeCheck(id: string, over: Partial<Check> = {}): Check {
  return {
    id,
    createdAt: '2026-10-04T09:00:00.000Z',
    lang: 'sw',
    leaves: [leaf('rust', 0.9), leaf('rust', 0.8), leaf('unsure', 0.3, true), leaf('not_leaf', 0.99)],
    summary: {
      n: 4,
      counts: { healthy: 0, rust: 2, cercospora: 0, phoma: 0, miner: 0, not_leaf: 1 },
      uncertain: 2,
      dominant: 'rust',
      affected: 2,
      distinctProblems: 1,
    },
    window: 'pre_short_rains',
    answerId: 'rust_high_pre_rains',
    decision: 'ask',
    memberId: 'OCC0412',
    plotId: '2',
    consentMain: true,
    consentPhotos: false,
    synced: false,
    ...over,
  };
}

const blob = (s: string) => new Blob([s], { type: 'image/jpeg' });

beforeEach(async () => {
  await _resetStorageForTests();
  globalThis.indexedDB = new IDBFactory();
  vi.stubGlobal('navigator', { onLine: true });
  setSyncSender(null);
});

afterEach(() => {
  vi.unstubAllGlobals();
  setSyncSender(null);
});

describe('toReferralRow', () => {
  it('maps fields, no names, mean confidence of accepted leaves', () => {
    const row = toReferralRow(makeCheck('a'));
    expect(row).toEqual({
      member_id: 'OCC0412',
      plot_id: '2',
      check_date: '2026-10-04',
      counts: { healthy: 0, rust: 2, cercospora: 0, phoma: 0, miner: 0, not_leaf: 1 },
      uncertain: 2,
      answer_id: 'rust_high_pre_rains',
      confidence: 0.85,
      decision: 'ask',
      photos_shared: false,
      synthetic: false,
    });
  });

  it('nulls for missing plot, decision and accepted leaves', () => {
    const row = toReferralRow(
      makeCheck('a', { plotId: undefined, decision: undefined, leaves: [leaf('unsure', 0.4, true)] }),
    );
    expect(row.plot_id).toBeNull();
    expect(row.decision).toBeNull();
    expect(row.confidence).toBeNull();
  });
});

describe('queueForSync', () => {
  it('needs main consent on the check', async () => {
    await queueForSync(makeCheck('a', { consentMain: false }));
    expect(await queueList()).toEqual([]);
    expect(await getCheck('a')).toBeUndefined();
  });

  it('saves and de-duplicates, keeping order', async () => {
    await queueForSync(makeCheck('a'));
    await queueForSync(makeCheck('b'));
    await queueForSync(makeCheck('a'));
    expect(await queueList()).toEqual(['a', 'b']);
    expect(await getCheck('a')).toBeDefined();
  });
});

describe('syncPending', () => {
  it('returns 0 without a sender', async () => {
    await queueForSync(makeCheck('a'));
    expect(await syncPending()).toBe(0);
    expect(await queueList()).toEqual(['a']);
  });

  it('returns 0 offline or without navigator', async () => {
    const send = vi.fn(async () => {});
    setSyncSender(send);
    await queueForSync(makeCheck('a'));
    vi.stubGlobal('navigator', { onLine: false });
    expect(await syncPending()).toBe(0);
    vi.stubGlobal('navigator', undefined);
    expect(await syncPending()).toBe(0);
    expect(send).not.toHaveBeenCalled();
    expect(await queueList()).toEqual(['a']);
  });

  it('sends rows in order, marks synced and drains the queue', async () => {
    const rows: ReferralRow[] = [];
    setSyncSender(async (row) => {
      rows.push(row);
    });
    await queueForSync(makeCheck('a', { memberId: 'M1' }));
    await queueForSync(makeCheck('b', { memberId: 'M2' }));
    expect(await syncPending()).toBe(2);
    expect(rows.map((r) => r.member_id)).toEqual(['M1', 'M2']);
    expect((await getCheck('a'))?.synced).toBe(true);
    expect((await getCheck('b'))?.synced).toBe(true);
    expect(await queueList()).toEqual([]);
    expect(await syncPending()).toBe(0);
  });

  it('stops at the first error and keeps the rest queued in order', async () => {
    const seen: string[] = [];
    setSyncSender(async (row) => {
      seen.push(row.member_id!);
      if (row.member_id === 'M2') throw new Error('network');
    });
    for (const [id, m] of [['a', 'M1'], ['b', 'M2'], ['c', 'M3']]) {
      await queueForSync(makeCheck(id, { memberId: m }));
    }
    expect(await syncPending()).toBe(1);
    expect(seen).toEqual(['M1', 'M2']);
    expect(await queueList()).toEqual(['b', 'c']);
    expect((await getCheck('b'))?.synced).toBe(false);
  });

  it('never sends photos without the second consent', async () => {
    await setConsent({ main: true, photos: false });
    await queueForSync(makeCheck('a', { consentPhotos: false }));
    await savePhoto('a', 0, blob('p0'));
    const send = vi.fn(async (_row: ReferralRow, _photos: Blob[]) => {});
    setSyncSender(send);
    expect(await syncPending()).toBe(1);
    expect(send.mock.calls[0][1]).toEqual([]);
    expect(send.mock.calls[0][0].photos_shared).toBe(false);
  });

  it('sends photos in leaf order with the second consent', async () => {
    await setConsent({ main: true, photos: true });
    await queueForSync(makeCheck('a', { consentPhotos: true }));
    await savePhoto('a', 1, blob('p1'));
    await savePhoto('a', 0, blob('p0'));
    const send = vi.fn(async (_row: ReferralRow, _photos: Blob[]) => {});
    setSyncSender(send);
    expect(await syncPending()).toBe(1);
    const photos = send.mock.calls[0][1];
    expect(await Promise.all(photos.map((b) => b.text()))).toEqual(['p0', 'p1']);
    expect(send.mock.calls[0][0].photos_shared).toBe(true);
  });

  it('drops photos if the second consent was withdrawn after queueing', async () => {
    await setConsent({ main: true, photos: true });
    await queueForSync(makeCheck('a', { consentPhotos: true }));
    await savePhoto('a', 0, blob('p0'));
    await setConsent({ main: true, photos: false });
    const send = vi.fn(async (_row: ReferralRow, _photos: Blob[]) => {});
    setSyncSender(send);
    expect(await syncPending()).toBe(1);
    expect(send.mock.calls[0][1]).toEqual([]);
    expect(send.mock.calls[0][0].photos_shared).toBe(false);
  });

  it('does not double-send when called twice at once', async () => {
    const send = vi.fn(async () => {});
    setSyncSender(send);
    await queueForSync(makeCheck('a'));
    const [x, y] = await Promise.all([syncPending(), syncPending()]);
    expect(x).toBe(1);
    expect(y).toBe(1);
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('payload carries no name', async () => {
    const send = vi.fn(async (_row: ReferralRow, _photos: Blob[]) => {});
    setSyncSender(send);
    await queueForSync({ ...makeCheck('a'), name: 'Noor' } as Check);
    await syncPending();
    expect(JSON.stringify(send.mock.calls[0][0])).not.toContain('Noor');
  });
});
