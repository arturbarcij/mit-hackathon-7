import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import { canvasToJpeg, drawScaled } from './canvas';
import type { Check } from './types';

export interface Consent { main: boolean; photos: boolean }

interface StoredConsent extends Consent { updatedAt: string }
interface PinRecord { salt: string; hash: string; iterations: number }

interface JaniDB extends DBSchema {
  checks: { key: string; value: Check; indexes: { createdAt: string } };
  photos: { key: string; value: Blob };
  meta: { key: string; value: StoredConsent | PinRecord };
  outbox: { key: string; value: { checkId: string; queuedAt: string } };
}

export const DB_NAME = 'jani';
export const MAX_PHOTO_SIDE = 800;
const JPEG_QUALITY = 0.8;
const PIN_ITERATIONS = 50_000;

let dbPromise: Promise<IDBPDatabase<JaniDB>> | null = null;
let unlocked = false;

function db(): Promise<IDBPDatabase<JaniDB>> {
  dbPromise ??= openDB<JaniDB>(DB_NAME, 1, {
    upgrade(d) {
      const checks = d.createObjectStore('checks', { keyPath: 'id' });
      checks.createIndex('createdAt', 'createdAt');
      d.createObjectStore('photos');
      d.createObjectStore('meta');
      d.createObjectStore('outbox', { keyPath: 'checkId' });
    },
  });
  return dbPromise;
}

/** Closes the connection and forgets the unlock state. Tests use this to start clean. */
export async function resetStorageHandle(): Promise<void> {
  if (dbPromise) (await dbPromise).close();
  dbPromise = null;
  unlocked = false;
}

const photoKey = (checkId: string, index: number) => `${checkId}:${index}`;

/** Scales a photo so its longer side is at most 800 px and re-encodes it as JPEG. */
export async function compressPhoto(photo: Blob): Promise<Blob> {
  if (typeof createImageBitmap === 'undefined') return photo;
  const bmp = await createImageBitmap(photo);
  try {
    const scale = Math.min(1, MAX_PHOTO_SIDE / Math.max(bmp.width, bmp.height));
    const canvas = drawScaled(bmp, Math.max(1, Math.round(bmp.width * scale)), Math.max(1, Math.round(bmp.height * scale)));
    return await canvasToJpeg(canvas, JPEG_QUALITY);
  } finally {
    bmp.close();
  }
}

/**
 * A check goes to the sync queue only when the farmer chose "ask the officer" and gave the main consent.
 * Nothing is queued for a plain "act" or "wait", or before a decision is made.
 */
export function isSyncEligible(c: Check): boolean {
  return c.consentMain && c.decision === 'ask' && !c.synced;
}

export async function saveCheck(c: Check, photos?: Blob[]): Promise<void> {
  const compressed = photos ? await Promise.all(photos.map(compressPhoto)) : [];
  const d = await db();
  const tx = d.transaction(['checks', 'photos', 'outbox'], 'readwrite');
  await tx.objectStore('checks').put(c);
  for (let i = 0; i < compressed.length; i++) {
    await tx.objectStore('photos').put(compressed[i], photoKey(c.id, i));
  }
  if (isSyncEligible(c)) {
    await tx.objectStore('outbox').put({ checkId: c.id, queuedAt: new Date().toISOString() });
  } else {
    await tx.objectStore('outbox').delete(c.id);
  }
  await tx.done;
}

export async function getCheck(id: string): Promise<Check | undefined> {
  return (await db()).get('checks', id);
}

/** Newest first. Returns an empty list while a PIN is set and the history is locked. */
export async function listChecks(): Promise<Check[]> {
  if (await isLocked()) return [];
  const all = await (await db()).getAll('checks');
  return all.sort((a, b) => (a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0));
}

export async function getPhotos(checkId: string): Promise<Blob[]> {
  const d = await db();
  const out: Blob[] = [];
  for (let i = 0; ; i++) {
    const b = await d.get('photos', photoKey(checkId, i));
    if (!b) break;
    out.push(b);
  }
  return out;
}

export async function getConsent(): Promise<Consent> {
  const rec = (await (await db()).get('meta', 'consent')) as StoredConsent | undefined;
  return { main: rec?.main ?? false, photos: rec?.photos ?? false };
}

/** Photo consent is never true without main consent. */
export async function setConsent(c: Consent): Promise<void> {
  const rec: StoredConsent = { main: c.main, photos: c.main && c.photos, updatedAt: new Date().toISOString() };
  await (await db()).put('meta', rec, 'consent');
}

export async function clearAll(): Promise<void> {
  const d = await db();
  const tx = d.transaction(['checks', 'photos', 'meta', 'outbox'], 'readwrite');
  await Promise.all([
    tx.objectStore('checks').clear(),
    tx.objectStore('photos').clear(),
    tx.objectStore('meta').clear(),
    tx.objectStore('outbox').clear(),
  ]);
  await tx.done;
  unlocked = false;
}

/* Optional 4-digit PIN. It hides history on a shared phone. It is not encryption. */

const toHex = (b: ArrayBuffer | Uint8Array) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, '0')).join('');

async function hashPin(pin: string, saltHex: string, iterations: number): Promise<string> {
  const enc = new TextEncoder().encode(`${saltHex}:${pin}`);
  if (typeof crypto === 'undefined' || !crypto.subtle) {
    // Insecure context (plain http). Keep the feature working with a weak hash rather than failing.
    let h = 2166136261;
    for (const byte of enc) h = Math.imul(h ^ byte, 16777619) >>> 0;
    return `weak-${h.toString(16)}`;
  }
  const key = await crypto.subtle.importKey('raw', enc, 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', hash: 'SHA-256', salt: new TextEncoder().encode(saltHex), iterations },
    key,
    256,
  );
  return toHex(bits);
}

function assertPin(pin: string): void {
  if (!/^\d{4}$/.test(pin)) throw new Error('PIN must be exactly 4 digits');
}

async function getPinRecord(): Promise<PinRecord | undefined> {
  return (await (await db()).get('meta', 'pin')) as PinRecord | undefined;
}

export async function hasPin(): Promise<boolean> {
  return (await getPinRecord()) !== undefined;
}

export async function isLocked(): Promise<boolean> {
  return (await hasPin()) && !unlocked;
}

export async function setPin(pin: string): Promise<void> {
  assertPin(pin);
  const salt = toHex(crypto.getRandomValues(new Uint8Array(16)));
  const rec: PinRecord = { salt, hash: await hashPin(pin, salt, PIN_ITERATIONS), iterations: PIN_ITERATIONS };
  await (await db()).put('meta', rec, 'pin');
  unlocked = true;
}

export async function unlock(pin: string): Promise<boolean> {
  const rec = await getPinRecord();
  if (!rec) {
    unlocked = true;
    return true;
  }
  if (!/^\d{4}$/.test(pin)) return false;
  unlocked = (await hashPin(pin, rec.salt, rec.iterations)) === rec.hash;
  return unlocked;
}

export function lock(): void {
  unlocked = false;
}

/** Removing the PIN needs the current PIN. */
export async function removePin(pin: string): Promise<boolean> {
  if (!(await unlock(pin))) return false;
  await (await db()).delete('meta', 'pin');
  return true;
}

/* Used by sync.ts */

export async function outboxIds(): Promise<string[]> {
  return (await (await db()).getAllKeys('outbox')) as string[];
}

export async function removeFromOutbox(checkId: string): Promise<void> {
  await (await db()).delete('outbox', checkId);
}

export async function markSynced(checkId: string): Promise<void> {
  const d = await db();
  const tx = d.transaction(['checks', 'outbox'], 'readwrite');
  const c = await tx.objectStore('checks').get(checkId);
  if (c) await tx.objectStore('checks').put({ ...c, synced: true });
  await tx.objectStore('outbox').delete(checkId);
  await tx.done;
}
