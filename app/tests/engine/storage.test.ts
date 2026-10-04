import 'fake-indexeddb/auto';
import { IDBFactory } from 'fake-indexeddb';
import { beforeEach, describe, expect, it } from 'vitest';
import type { Check } from '../../src/engine/types';
import {
  _resetStorageForTests,
  clearAll,
  compressPhoto,
  getConsent,
  getPhotos,
  hasPin,
  listChecks,
  lock,
  queueAdd,
  queueList,
  saveCheck,
  savePhoto,
  setConsent,
  setPin,
  unlock,
} from '../../src/engine/storage';

function makeCheck(id: string, createdAt: string, over: Partial<Check> = {}): Check {
  return {
    id,
    createdAt,
    lang: 'sw',
    leaves: [],
    summary: {
      n: 0,
      counts: { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
      uncertain: 0,
      dominant: 'none',
      affected: 0,
      distinctProblems: 0,
    },
    window: 'dry',
    answerId: 'healthy_ok',
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
});

describe('consent', () => {
  it('defaults to nothing given', async () => {
    expect(await getConsent()).toEqual({ main: false, photos: false });
  });

  it('forces photos off without main consent', async () => {
    await setConsent({ main: false, photos: true });
    expect(await getConsent()).toEqual({ main: false, photos: false });
    await setConsent({ main: true, photos: true });
    expect(await getConsent()).toEqual({ main: true, photos: true });
    await setConsent({ main: true, photos: false });
    expect(await getConsent()).toEqual({ main: true, photos: false });
  });

  it('withdrawing main consent wipes checks, photos, queue and PIN', async () => {
    await setConsent({ main: true, photos: true });
    await saveCheck(makeCheck('a', '2026-10-01T08:00:00Z'));
    await savePhoto('a', 0, blob('x'));
    await queueAdd('a');
    await setPin('1234');
    await setConsent({ main: false, photos: false });
    expect(await getConsent()).toEqual({ main: false, photos: false });
    expect(await hasPin()).toBe(false);
    expect(await listChecks()).toEqual([]);
    expect(await getPhotos('a')).toEqual([]);
    expect(await queueList()).toEqual([]);
  });
});

describe('checks', () => {
  it('saveCheck is a no-op without main consent on the check', async () => {
    await saveCheck(makeCheck('a', '2026-10-01T08:00:00Z', { consentMain: false }));
    expect(await listChecks()).toEqual([]);
  });

  it('lists newest first and upserts', async () => {
    await saveCheck(makeCheck('old', '2026-09-01T08:00:00Z'));
    await saveCheck(makeCheck('new', '2026-10-02T08:00:00Z'));
    await saveCheck(makeCheck('mid', '2026-09-15T08:00:00Z'));
    await saveCheck(makeCheck('mid', '2026-09-15T08:00:00Z', { answerId: 'changed' }));
    const list = await listChecks();
    expect(list.map((c) => c.id)).toEqual(['new', 'mid', 'old']);
    expect(list[1].answerId).toBe('changed');
  });

  it('clearAll empties everything', async () => {
    await setConsent({ main: true, photos: false });
    await saveCheck(makeCheck('a', '2026-10-01T08:00:00Z'));
    await clearAll();
    expect(await listChecks()).toEqual([]);
    expect(await getConsent()).toEqual({ main: false, photos: false });
  });
});

describe('PIN', () => {
  it('hides history until unlocked; wrong PIN fails', async () => {
    await saveCheck(makeCheck('a', '2026-10-01T08:00:00Z'));
    await setPin('4821');
    expect(await hasPin()).toBe(true);
    expect(await listChecks()).toHaveLength(1); // setter stays unlocked
    lock();
    expect(await listChecks()).toEqual([]);
    expect(await unlock('0000')).toBe(false);
    expect(await listChecks()).toEqual([]);
    expect(await unlock('4821')).toBe(true);
    expect(await listChecks()).toHaveLength(1);
  });

  it('stays locked across a fresh session (new module state)', async () => {
    await saveCheck(makeCheck('a', '2026-10-01T08:00:00Z'));
    await setPin('4821');
    const idb = globalThis.indexedDB;
    await _resetStorageForTests();
    globalThis.indexedDB = idb;
    expect(await hasPin()).toBe(true);
    expect(await listChecks()).toEqual([]);
  });

  it('rejects bad formats', async () => {
    for (const bad of ['123', '12345', 'abcd', '12a4', ' 1234', '']) {
      await expect(setPin(bad)).rejects.toThrow();
    }
    expect(await hasPin()).toBe(false);
  });

  it('cannot change or remove the PIN while locked; can after unlock', async () => {
    await setPin('1111');
    lock();
    await expect(setPin(null)).rejects.toThrow();
    await expect(setPin('2222')).rejects.toThrow();
    expect(await unlock('1111')).toBe(true);
    await setPin(null);
    expect(await hasPin()).toBe(false);
  });

  it('salts the hash (no plain PIN stored)', async () => {
    await setPin('1234');
    const d = await new Promise<IDBDatabase>((res, rej) => {
      const r = indexedDB.open('jani');
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    const rec = await new Promise<{ salt: string; hash: string }>((res) => {
      const r = d.transaction('meta').objectStore('meta').get('pin');
      r.onsuccess = () => res(r.result);
    });
    d.close();
    expect(rec.salt).toMatch(/^[0-9a-f]{32}$/);
    expect(rec.hash).toMatch(/^[0-9a-f]{64}$/);
    expect(JSON.stringify(rec)).not.toContain('1234');
  });
});

describe('photos', () => {
  it('needs current main consent and returns leaf order', async () => {
    await savePhoto('c', 0, blob('no'));
    expect(await getPhotos('c')).toEqual([]);
    await setConsent({ main: true, photos: false });
    for (const i of [10, 2, 0, 1]) await savePhoto('c', i, blob(`leaf${i}`));
    await savePhoto('c2', 0, blob('other'));
    const texts = await Promise.all((await getPhotos('c')).map((b) => b.text()));
    expect(texts).toEqual(['leaf0', 'leaf1', 'leaf2', 'leaf10']);
  });

  it('compressPhoto gives a clear error without a canvas', async () => {
    await expect(compressPhoto({ width: 100, height: 100 } as ImageBitmap)).rejects.toThrow(/canvas/);
  });
});
