import { openDB, type IDBPDatabase } from 'idb';
import type { Check, LeafResult } from './types.ts';

type LeafRecord = LeafResult & { photo?: Blob };

export async function hashPin(pin: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle || typeof TextEncoder === 'undefined') return 'non-secret';
  try {
    const digest = await subtle.digest('SHA-256', new TextEncoder().encode(pin));
    return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  } catch {
    return 'non-secret';
  }
}

export async function compressPhoto(blob: Blob): Promise<Blob> {
  if (typeof OffscreenCanvas === 'undefined' || typeof createImageBitmap !== 'function') return blob;
  try {
    const bitmap = await createImageBitmap(blob);
    const scale = Math.min(1, 800 / Math.max(bitmap.width, bitmap.height));
    const width = Math.max(1, Math.round(bitmap.width * scale));
    const height = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = new OffscreenCanvas(width, height);
    const context = canvas.getContext('2d');
    if (!context) {
      bitmap.close();
      return blob;
    }
    context.drawImage(bitmap, 0, 0, width, height);
    bitmap.close();
    return await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.8 });
  } catch {
    return blob;
  }
}

function idbAvailable(): boolean {
  return typeof indexedDB !== 'undefined';
}

let databasePromise: Promise<IDBPDatabase> | null = null;

function database(): Promise<IDBPDatabase> {
  if (!databasePromise) {
    databasePromise = openDB('jani', 1, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('checks')) db.createObjectStore('checks', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('consent')) db.createObjectStore('consent');
        if (!db.objectStoreNames.contains('meta')) db.createObjectStore('meta');
      },
    });
  }
  return databasePromise;
}

async function prepareCheck(check: Check): Promise<Check> {
  const leaves = await Promise.all(
    check.leaves.map(async (leaf) => {
      const record = leaf as LeafRecord;
      if (!(record.photo instanceof Blob)) return leaf;
      const photo = await compressPhoto(record.photo);
      return { ...leaf, photo };
    }),
  );
  return { ...check, leaves };
}

export async function saveCheck(check: Check): Promise<void> {
  if (!idbAvailable()) return;
  const db = await database();
  await db.put('checks', await prepareCheck(check));
}

export async function listChecks(): Promise<Check[]> {
  if (!idbAvailable()) return [];
  const db = await database();
  const rows = (await db.getAll('checks')) as Check[];
  return rows.sort((a, b) => (a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0));
}

export async function getConsent(): Promise<{ main: boolean; photos: boolean }> {
  if (!idbAvailable()) return { main: false, photos: false };
  const db = await database();
  const row = (await db.get('consent', 'current')) as { main?: boolean; photos?: boolean } | undefined;
  return { main: row?.main === true, photos: row?.photos === true };
}

export async function setConsent(consent: { main: boolean; photos: boolean }): Promise<void> {
  if (!idbAvailable()) return;
  const db = await database();
  await db.put('consent', { main: consent.main, photos: consent.photos }, 'current');
}

export async function clearAll(): Promise<void> {
  if (!idbAvailable()) return;
  const db = await database();
  const tx = db.transaction(['checks', 'consent', 'meta'], 'readwrite');
  await tx.objectStore('checks').clear();
  await tx.objectStore('consent').clear();
  await tx.objectStore('meta').clear();
  await tx.done;
}

export async function setPin(pin: string): Promise<void> {
  if (!idbAvailable()) return;
  const hash = await hashPin(pin);
  const db = await database();
  await db.put('meta', { hash, secret: hash !== 'non-secret' }, 'pin');
}

export async function checkPin(pin: string): Promise<boolean> {
  if (!idbAvailable()) return false;
  const db = await database();
  const row = (await db.get('meta', 'pin')) as { hash?: string } | undefined;
  if (!row?.hash || row.hash === 'non-secret') return false;
  return (await hashPin(pin)) === row.hash;
}
