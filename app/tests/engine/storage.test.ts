import { describe, expect, it } from 'vitest';
import { checkPin, compressPhoto, getConsent, hashPin, listChecks, saveCheck } from '../../src/engine/storage.ts';
import { canSync, withoutPhotos } from '../../src/engine/sync.ts';
import type { Check } from '../../src/engine/types.ts';

describe('storage helpers', () => {
  it('hashes a pin without storing the pin itself', async () => {
    const hash = await hashPin('1234');
    expect(hash).not.toBe('1234');
    expect(hash).not.toBe('non-secret');
    expect(hash).toHaveLength(64);
    expect(await hashPin('1234')).toBe(hash);
  });

  it('no-ops IndexedDB calls when the browser store is missing', async () => {
    const blob = new Blob(['leaf'], { type: 'image/jpeg' });
    expect(await compressPhoto(blob)).toBe(blob);
    await saveCheck({} as Check);
    expect(await listChecks()).toEqual([]);
    expect(await getConsent()).toEqual({ main: false, photos: false });
    expect(await checkPin('1234')).toBe(false);
  });

  it('syncs only when online, both consents are set, and a URL exists', () => {
    expect(canSync(false, { main: true, photos: true }, 'https://example.test/sync')).toBe(false);
    expect(canSync(true, { main: true, photos: false }, 'https://example.test/sync')).toBe(false);
    expect(canSync(true, { main: false, photos: true }, 'https://example.test/sync')).toBe(false);
    expect(canSync(true, { main: true, photos: true }, '')).toBe(false);
    expect(canSync(true, { main: true, photos: true }, 'https://example.test/sync')).toBe(true);
  });

  it('drops photo blobs from the sync payload', () => {
    const photo = new Blob(['pixels']);
    const check = {
      id: 'c',
      leaves: [{ label: 'rust', photo } as Check['leaves'][number] & { photo: Blob }],
    } as Check;
    const clean = withoutPhotos(check);
    expect('photo' in clean.leaves[0]).toBe(false);
    expect('photo' in check.leaves[0]).toBe(true);
  });
});