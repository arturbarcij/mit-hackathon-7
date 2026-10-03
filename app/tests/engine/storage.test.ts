import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearAll, getConsent, getPhotos, hasPin, isLocked, listChecks, lock, outboxIds, removePin,
  requestPersistentStorage, resetStorageHandle, saveCheck, setConsent, setPin, unlock, isSyncEligible,
} from '../../src/engine/storage';
import { makeCheck } from './helpers';

beforeEach(async () => {
  await clearAll();
  await resetStorageHandle();
});

describe('storage', () => {
  it('defaults consent to off', async () => {
    expect(await getConsent()).toEqual({ main: false, photos: false });
  });

  it('persists consent and never allows photo consent without main consent', async () => {
    await setConsent({ main: true, photos: true });
    expect(await getConsent()).toEqual({ main: true, photos: true });
    await setConsent({ main: false, photos: true });
    expect(await getConsent()).toEqual({ main: false, photos: false });
  });

  it('saves and lists checks, newest first', async () => {
    await saveCheck(makeCheck({ id: 'a', createdAt: '2026-10-01T10:00:00.000Z' }));
    await saveCheck(makeCheck({ id: 'b', createdAt: '2026-10-03T10:00:00.000Z' }));
    await saveCheck(makeCheck({ id: 'a', createdAt: '2026-10-01T10:00:00.000Z', decision: 'wait' }));
    const list = await listChecks();
    expect(list.map((c) => c.id)).toEqual(['b', 'a']);
    expect(list[1].decision).toBe('wait');
  });

  it('stores photos next to the check', async () => {
    await saveCheck(makeCheck({ id: 'p' }), [new Blob(['one']), new Blob(['two'])]);
    const photos = await getPhotos('p');
    expect(photos).toHaveLength(2);
    expect(await photos[1].text()).toBe('two');
  });

  it('queues only checks where the farmer chose to ask and consent is on', async () => {
    await saveCheck(makeCheck({ id: 'x1', decision: 'ask', consentMain: true }));
    await saveCheck(makeCheck({ id: 'x2', decision: 'act', consentMain: true }));
    await saveCheck(makeCheck({ id: 'x3', decision: 'ask', consentMain: false }));
    await saveCheck(makeCheck({ id: 'x4', decision: undefined, consentMain: true }));
    expect(await outboxIds()).toEqual(['x1']);
    expect(isSyncEligible(makeCheck({ decision: 'ask', synced: true }))).toBe(false);
  });

  it('drops a check from the queue when the decision changes away from ask', async () => {
    await saveCheck(makeCheck({ id: 'y', decision: 'ask' }));
    expect(await outboxIds()).toEqual(['y']);
    await saveCheck(makeCheck({ id: 'y', decision: 'wait' }));
    expect(await outboxIds()).toEqual([]);
  });

  it('hides history behind an optional 4-digit PIN', async () => {
    await saveCheck(makeCheck({ id: 'h' }));
    expect(await hasPin()).toBe(false);
    await setPin('1234');
    expect(await hasPin()).toBe(true);
    expect((await listChecks()).length).toBe(1);
    lock();
    expect(await isLocked()).toBe(true);
    expect(await listChecks()).toEqual([]);
    expect(await unlock('0000')).toBe(false);
    expect(await listChecks()).toEqual([]);
    expect(await unlock('1234')).toBe(true);
    expect((await listChecks()).length).toBe(1);
  });

  it('rejects a PIN that is not 4 digits and needs the PIN to remove it', async () => {
    await expect(setPin('12')).rejects.toThrow();
    await expect(setPin('abcd')).rejects.toThrow();
    await setPin('4321');
    expect(await removePin('1111')).toBe(false);
    expect(await hasPin()).toBe(true);
    expect(await removePin('4321')).toBe(true);
    expect(await hasPin()).toBe(false);
  });

  it('clearAll removes checks, photos, consent, PIN and the queue', async () => {
    await setConsent({ main: true, photos: true });
    await setPin('1234');
    await saveCheck(makeCheck({ id: 'z', decision: 'ask' }), [new Blob(['a'])]);
    await clearAll();
    expect(await hasPin()).toBe(false);
    expect(await listChecks()).toEqual([]);
    expect(await getPhotos('z')).toEqual([]);
    expect(await getConsent()).toEqual({ main: false, photos: false });
    expect(await outboxIds()).toEqual([]);
  });
});

describe('persistent storage', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('asks the browser to keep our data once, and never throws', async () => {
    const persist = vi.fn(async () => true);
    vi.stubGlobal('navigator', { storage: { persisted: async () => false, persist } });
    expect(await requestPersistentStorage()).toBe(true);
    expect(persist).toHaveBeenCalledTimes(1);
    vi.stubGlobal('navigator', { storage: { persisted: async () => true, persist } });
    expect(await requestPersistentStorage()).toBe(true);
    expect(persist).toHaveBeenCalledTimes(1);
    vi.stubGlobal('navigator', {});
    expect(await requestPersistentStorage()).toBe(false);
    vi.stubGlobal('navigator', { storage: { persisted: async () => { throw new Error('x'); }, persist } });
    expect(await requestPersistentStorage()).toBe(false);
  });
});
