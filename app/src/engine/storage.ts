// Local storage for Jani (IndexedDB via idb). Privacy model, MASTER_PROMPT section 8:
// - Data stays on the phone by default. Main consent covers keeping checks on this phone.
// - Photos are kept locally under main consent; they only leave the phone with the second consent (see sync.ts).
// - The phone is shared: an optional 4-digit PIN hides history until unlocked for this session.
// - Withdrawing main consent wipes every local record, the PIN included.
// SSR-safe: nothing here touches indexedDB, crypto or canvas until a function is called.
import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { Check, Consent, ImageInput } from './types';

interface PinRecord {
  salt: string; // hex
  hash: string; // hex SHA-256(salt + pin)
}

interface QueueEntry {
  id: string;
  seq: number; // insertion order
}

interface JaniDB extends DBSchema {
  checks: { key: string; value: Check };
  photos: { key: string; value: Blob }; // key `${checkId}:${leafIndex}`
  meta: { key: string; value: Consent | PinRecord }; // 'consent', 'pin'
  queue: { key: string; value: QueueEntry }; // key = check id
}

const DB_NAME = 'jani';
const DEFAULT_CONSENT: Consent = { main: false, photos: false };

let dbPromise: Promise<IDBPDatabase<JaniDB>> | null = null;
let unlocked = false;

function db(): Promise<IDBPDatabase<JaniDB>> {
  if (typeof indexedDB === 'undefined') {
    return Promise.reject(new Error('Jani storage needs IndexedDB (browser only)'));
  }
  if (!dbPromise) {
    dbPromise = openDB<JaniDB>(DB_NAME, 1, {
      upgrade(d) {
        d.createObjectStore('checks', { keyPath: 'id' });
        d.createObjectStore('photos');
        d.createObjectStore('meta');
        d.createObjectStore('queue');
      },
    });
  }
  return dbPromise;
}

/** Test helper: close and forget the cached connection and the session unlock. */
export async function _resetStorageForTests(): Promise<void> {
  if (dbPromise) {
    try {
      (await dbPromise).close();
    } catch {
      // ignore
    }
  }
  dbPromise = null;
  unlocked = false;
}

// ---------- checks ----------

/**
 * Insert or replace a check. Deliberately a silent no-op when c.consentMain is false:
 * without main consent nothing is kept on the phone.
 */
export async function saveCheck(c: Check): Promise<void> {
  if (!c.consentMain) return;
  await (await db()).put('checks', c);
}

/** All checks, newest first. Returns [] while a PIN is set and this session is locked. */
export async function listChecks(): Promise<Check[]> {
  if (await isLocked()) return [];
  const all = await (await db()).getAll('checks');
  return all.sort((a, b) => (a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0));
}

/** Engine-internal (sync.ts): one check by id, ignoring the PIN lock. */
export async function getCheck(id: string): Promise<Check | undefined> {
  return (await db()).get('checks', id);
}

// ---------- consent ----------

export async function getConsent(): Promise<Consent> {
  const v = (await (await db()).get('meta', 'consent')) as Consent | undefined;
  if (!v) return { ...DEFAULT_CONSENT };
  return { main: v.main === true, photos: v.main === true && v.photos === true };
}

/** Photos consent is forced false without main consent. Withdrawing main consent wipes everything first. */
export async function setConsent(c: Consent): Promise<void> {
  const main = c.main === true;
  if (!main) {
    await clearAll();
    return;
  }
  await (await db()).put('meta', { main: true, photos: c.photos === true }, 'consent');
}

// ---------- PIN ----------

function toHex(buf: ArrayBuffer | Uint8Array): string {
  const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
}

async function hashPin(salt: string, pin: string): Promise<string> {
  const data = new TextEncoder().encode(salt + pin);
  return toHex(await crypto.subtle.digest('SHA-256', data));
}

async function getPinRecord(): Promise<PinRecord | undefined> {
  return (await (await db()).get('meta', 'pin')) as PinRecord | undefined;
}

async function isLocked(): Promise<boolean> {
  return !unlocked && (await getPinRecord()) !== undefined;
}

/**
 * Set a 4-digit PIN, or pass null to remove it. Rejects any other format.
 * Changing or removing an existing PIN requires the session to be unlocked first.
 * Setting a PIN leaves the current session unlocked (the person who set it is holding the phone).
 */
export async function setPin(pin: string | null): Promise<void> {
  if (pin !== null && !/^\d{4}$/.test(pin)) throw new Error('PIN must be exactly 4 digits');
  if (await isLocked()) throw new Error('Unlock with the current PIN first');
  const d = await db();
  if (pin === null) {
    await d.delete('meta', 'pin');
    return;
  }
  const salt = toHex(crypto.getRandomValues(new Uint8Array(16)));
  await d.put('meta', { salt, hash: await hashPin(salt, pin) }, 'pin');
  unlocked = true;
}

export async function hasPin(): Promise<boolean> {
  return (await getPinRecord()) !== undefined;
}

/** True and unlocked for this session when the PIN matches (or when no PIN is set). */
export async function unlock(pin: string): Promise<boolean> {
  const rec = await getPinRecord();
  if (!rec) {
    unlocked = true;
    return true;
  }
  if (!/^\d{4}$/.test(pin)) return false;
  const ok = (await hashPin(rec.salt, pin)) === rec.hash;
  if (ok) unlocked = true;
  return ok;
}

export function lock(): void {
  unlocked = false;
}

// ---------- photos ----------

function sizeOf(img: ImageInput): { w: number; h: number } {
  const el = img as HTMLImageElement;
  if (typeof el.naturalWidth === 'number' && el.naturalWidth > 0) return { w: el.naturalWidth, h: el.naturalHeight };
  return { w: img.width, h: img.height };
}

/** Downscale so the longer side is at most maxSide, then encode as JPEG quality 0.7. */
export async function compressPhoto(img: ImageInput, maxSide = 800): Promise<Blob> {
  const { w, h } = sizeOf(img);
  if (!w || !h) throw new Error('compressPhoto: image has no size');
  const scale = Math.min(1, maxSide / Math.max(w, h));
  const tw = Math.max(1, Math.round(w * scale));
  const th = Math.max(1, Math.round(h * scale));
  if (typeof OffscreenCanvas !== 'undefined') {
    const canvas = new OffscreenCanvas(tw, th);
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('compressPhoto: no 2D canvas context');
    ctx.drawImage(img as CanvasImageSource, 0, 0, tw, th);
    return canvas.convertToBlob({ type: 'image/jpeg', quality: 0.7 });
  }
  if (typeof document !== 'undefined') {
    const canvas = document.createElement('canvas');
    canvas.width = tw;
    canvas.height = th;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('compressPhoto: no 2D canvas context');
    ctx.drawImage(img as CanvasImageSource, 0, 0, tw, th);
    return new Promise((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('compressPhoto: encoding failed'))), 'image/jpeg', 0.7),
    );
  }
  throw new Error('compressPhoto needs a canvas (OffscreenCanvas or document); not available here');
}

/** Keep a leaf photo on the phone. No-op unless main consent is currently given. */
export async function savePhoto(checkId: string, leafIndex: number, blob: Blob): Promise<void> {
  if (!(await getConsent()).main) return;
  await (await db()).put('photos', blob, `${checkId}:${leafIndex}`);
}

/** Engine-internal (sync.ts): photos of one check in leaf order, ignoring the PIN lock. */
export async function readPhotos(checkId: string): Promise<Blob[]> {
  const d = await db();
  const prefix = `${checkId}:`;
  const range = IDBKeyRange.bound(prefix, prefix + '￿');
  const found: { i: number; blob: Blob }[] = [];
  let cursor = await d.transaction('photos').store.openCursor(range);
  while (cursor) {
    const i = Number(String(cursor.key).slice(prefix.length));
    if (Number.isInteger(i)) found.push({ i, blob: cursor.value });
    cursor = await cursor.continue();
  }
  return found.sort((a, b) => a.i - b.i).map((x) => x.blob);
}

/** Photos of one check in leaf order. [] while the PIN lock is on. */
export async function getPhotos(checkId: string): Promise<Blob[]> {
  if (await isLocked()) return [];
  return readPhotos(checkId);
}

// ---------- sync queue (engine-internal, used by sync.ts) ----------

/** Add a check id to the sync queue once; repeated calls keep its original place. */
export async function queueAdd(id: string): Promise<void> {
  const tx = (await db()).transaction('queue', 'readwrite');
  if (!(await tx.store.get(id))) {
    const all = await tx.store.getAll();
    const seq = all.reduce((m, e) => Math.max(m, e.seq), 0) + 1;
    await tx.store.put({ id, seq }, id);
  }
  await tx.done;
}

/** Queued check ids in the order they were queued. */
export async function queueList(): Promise<string[]> {
  const all = await (await db()).getAll('queue');
  return all.sort((a, b) => a.seq - b.seq).map((e) => e.id);
}

export async function queueRemove(id: string): Promise<void> {
  await (await db()).delete('queue', id);
}

/** Mark a check synced and drop it from the queue in one transaction. */
export async function markSynced(id: string): Promise<void> {
  const tx = (await db()).transaction(['checks', 'queue'], 'readwrite');
  const c = await tx.objectStore('checks').get(id);
  if (c) await tx.objectStore('checks').put({ ...c, synced: true });
  await tx.objectStore('queue').delete(id);
  await tx.done;
}

// ---------- wipe ----------

/** Empty every store (checks, photos, consent, PIN, queue). Consent reads back as {main:false, photos:false}. */
export async function clearAll(): Promise<void> {
  const tx = (await db()).transaction(['checks', 'photos', 'meta', 'queue'], 'readwrite');
  await Promise.all([
    tx.objectStore('checks').clear(),
    tx.objectStore('photos').clear(),
    tx.objectStore('meta').clear(),
    tx.objectStore('queue').clear(),
    tx.done,
  ]);
  unlocked = false;
}
