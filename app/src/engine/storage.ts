import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { Check, Decision } from './types.ts'

export interface StoredReferral {
  id: string
  createdAt: string
  memberId: string
  plotId: string
  checkDate: string
  counts: { rust: number; cercospora: number; phoma: number; miner: number; healthy: number; not_leaf: number }
  uncertain: number
  answerId: string
  confidence: number
  photosShared: boolean
  status: 'new' | 'confirmed' | 'visit'
  synthetic: boolean
  sms: string
  decision: Decision
}

export interface Correction {
  id: string
  referralId: string
  leafIndex: number
  modelLabel: string
  officerLabel: string
  officerId: string
  createdAt: string
}

interface JaniDb extends DBSchema {
  checks: { key: string; value: Check }
  photos: { key: string; value: { checkId: string; index: number; blob: Blob } }
  meta: { key: string; value: unknown }
  referrals: { key: string; value: StoredReferral }
  corrections: { key: string; value: Correction }
}

let dbPromise: Promise<IDBPDatabase<JaniDb>> | null = null

function db(): Promise<IDBPDatabase<JaniDb>> {
  if (!dbPromise) {
    dbPromise = openDB<JaniDb>('jani', 1, {
      upgrade(database) {
        database.createObjectStore('checks', { keyPath: 'id' })
        database.createObjectStore('photos')
        database.createObjectStore('meta')
        database.createObjectStore('referrals', { keyPath: 'id' })
        database.createObjectStore('corrections', { keyPath: 'id' })
      },
    })
  }
  return dbPromise
}

export async function saveCheck(check: Check): Promise<void> {
  const database = await db()
  await database.put('checks', check)
}

export async function listChecks(): Promise<Check[]> {
  const database = await db()
  const rows = await database.getAll('checks')
  return rows.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
}

export async function savePhoto(checkId: string, index: number, blob: Blob): Promise<void> {
  const database = await db()
  await database.put('photos', { checkId, index, blob }, `${checkId}:${index}`)
}

export async function listPhotos(checkId: string): Promise<Array<{ index: number; blob: Blob }>> {
  const database = await db()
  const keys = await database.getAllKeys('photos')
  const found: Array<{ index: number; blob: Blob }> = []
  for (const key of keys) {
    if (typeof key !== 'string' || !key.startsWith(`${checkId}:`)) continue
    const row = await database.get('photos', key)
    if (row) found.push({ index: row.index, blob: row.blob })
  }
  return found.sort((a, b) => a.index - b.index)
}

export async function getConsent(): Promise<{ main: boolean; photos: boolean }> {
  const database = await db()
  const value = await database.get('meta', 'consent')
  if (!value || typeof value !== 'object') return { main: false, photos: false }
  const record = value as { main?: boolean; photos?: boolean }
  return { main: Boolean(record.main), photos: Boolean(record.photos) }
}

export async function setConsent(consent: { main: boolean; photos: boolean }): Promise<void> {
  const database = await db()
  await database.put('meta', consent, 'consent')
}

export async function getProfile(): Promise<{ memberId: string; plotId: string; coopNumber: string }> {
  const database = await db()
  const value = await database.get('meta', 'profile')
  if (!value || typeof value !== 'object') return { memberId: '', plotId: '', coopNumber: '' }
  const record = value as { memberId?: string; plotId?: string; coopNumber?: string }
  return {
    memberId: record.memberId ?? '',
    plotId: record.plotId ?? '',
    coopNumber: record.coopNumber ?? '',
  }
}

export async function setProfile(profile: { memberId: string; plotId: string; coopNumber: string }): Promise<void> {
  const database = await db()
  await database.put('meta', profile, 'profile')
}

export async function hashPin(pin: string): Promise<string> {
  const data = new TextEncoder().encode(`jani-pin:${pin}`)
  const buf = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(buf)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

export async function setPin(pin: string): Promise<void> {
  const database = await db()
  await database.put('meta', await hashPin(pin), 'pin')
}

export async function clearPin(): Promise<void> {
  const database = await db()
  await database.delete('meta', 'pin')
}

export async function hasPin(): Promise<boolean> {
  const database = await db()
  const value = await database.get('meta', 'pin')
  return typeof value === 'string' && value.length > 0
}

export async function checkPin(pin: string): Promise<boolean> {
  const database = await db()
  const value = await database.get('meta', 'pin')
  if (typeof value !== 'string') return false
  return value === (await hashPin(pin))
}

export async function saveReferral(referral: StoredReferral): Promise<void> {
  const database = await db()
  await database.put('referrals', referral)
}

export async function listReferrals(): Promise<StoredReferral[]> {
  const database = await db()
  return database.getAll('referrals')
}

export async function saveCorrection(correction: Correction): Promise<void> {
  const database = await db()
  await database.put('corrections', correction)
}

export async function listCorrections(): Promise<Correction[]> {
  const database = await db()
  return database.getAll('corrections')
}

export async function clearAll(): Promise<void> {
  const database = await db()
  await database.clear('checks')
  await database.clear('photos')
  await database.clear('meta')
  await database.clear('referrals')
  await database.clear('corrections')
}
