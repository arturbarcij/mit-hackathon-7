import { beforeEach, describe, expect, it, vi } from 'vitest';
import { configureSync, syncPending, toReferralRow, type ReferralRow } from '../../src/engine/sync';
import { clearAll, getCheck, outboxIds, resetStorageHandle, saveCheck, setConsent } from '../../src/engine/storage';
import { makeCheck } from './helpers';

beforeEach(async () => {
  await clearAll();
  await resetStorageHandle();
  configureSync(null);
});

describe('syncPending', () => {
  it('does nothing without a target', async () => {
    await setConsent({ main: true, photos: false });
    await saveCheck(makeCheck({ id: 's1', decision: 'ask' }));
    expect(await syncPending()).toBe(0);
    expect(await outboxIds()).toEqual(['s1']);
  });

  it('does nothing without the main consent', async () => {
    const insert = vi.fn(async () => {});
    configureSync({ insert });
    await saveCheck(makeCheck({ id: 's2', decision: 'ask' }));
    expect(await syncPending()).toBe(0);
    expect(insert).not.toHaveBeenCalled();
  });

  it('pushes a queued check once and marks it synced', async () => {
    const rows: ReferralRow[] = [];
    configureSync({ insert: async (r) => void rows.push(r) });
    await setConsent({ main: true, photos: false });
    await saveCheck(makeCheck({ id: 's3', decision: 'ask' }));
    expect(await syncPending()).toBe(1);
    expect(await syncPending()).toBe(0);
    expect(rows).toHaveLength(1);
    expect(rows[0].member_id).toBe('OCC0412');
    expect(rows[0].photos_shared).toBe(false);
    expect(rows[0].synthetic).toBe(false);
    expect((await getCheck('s3'))?.synced).toBe(true);
  });

  it('keeps a check queued when the insert fails', async () => {
    configureSync({ insert: async () => { throw new Error('offline'); } });
    await setConsent({ main: true, photos: false });
    await saveCheck(makeCheck({ id: 's4', decision: 'ask' }));
    expect(await syncPending()).toBe(0);
    expect(await outboxIds()).toEqual(['s4']);
    expect((await getCheck('s4'))?.synced).toBe(false);
  });

  it('never uploads photos without the second consent', async () => {
    const uploadPhotos = vi.fn(async () => ['https://example.test/p.jpg']);
    const rows: ReferralRow[] = [];
    configureSync({ insert: async (r) => void rows.push(r), uploadPhotos });
    await setConsent({ main: true, photos: false });
    await saveCheck(makeCheck({ id: 's5', decision: 'ask', consentPhotos: true }));
    await syncPending();
    expect(uploadPhotos).not.toHaveBeenCalled();
    expect(rows[0].photo_urls).toEqual([]);
  });

  it('uploads photos only when stored consent and the check both allow it', async () => {
    const uploadPhotos = vi.fn(async () => ['https://example.test/p.jpg']);
    const rows: ReferralRow[] = [];
    configureSync({ insert: async (r) => void rows.push(r), uploadPhotos });
    await setConsent({ main: true, photos: true });
    await saveCheck(makeCheck({ id: 's6', decision: 'ask', consentPhotos: true }));
    await syncPending();
    expect(uploadPhotos).toHaveBeenCalledTimes(1);
    expect(rows[0].photos_shared).toBe(true);
  });

  it('maps a check to the referrals table columns', () => {
    const row = toReferralRow(makeCheck({ decision: 'ask' }), []);
    expect(Object.keys(row).sort()).toEqual(
      ['answer_id', 'check_date', 'confidence', 'counts', 'created_at', 'member_id', 'photo_urls', 'photos_shared', 'plot_id', 'status', 'synthetic', 'uncertain'],
    );
    expect(row.check_date).toBe('2026-10-04');
    expect(row.counts.rust).toBe(6);
    expect(row.confidence).toBeGreaterThan(0);
    expect(row.confidence).toBeLessThanOrEqual(1);
  });
});
