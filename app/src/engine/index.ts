import { decide } from './decide';
import { classifyLeaf } from './model';
import { summarisePlot } from './plot';
import { seasonWindow } from './season';
import { bitmapFromFile } from './source';
import type { Check, Lang, LeafResult } from './types';

export * from './types';
export { loadModel, classifyLeaf, lastInferenceTimeMs } from './model';
export { LABELS } from './scoring';
export { checkQuality } from './quality';
export { summarisePlot } from './plot';
export { seasonWindow } from './season';
export { decide, answerById as getAnswer } from './decide';
export { makeSample, type SampleKind } from './samples';
export { setMockHint } from './model.mock';
export type { Consent } from './storage';
export {
  saveCheck,
  listChecks,
  getCheck,
  getPhotos,
  savePhoto,
  listPhotos,
  getConsent,
  setConsent,
  getProfile,
  setProfile,
  clearAll,
  hasPin,
  checkPin,
  clearPin,
  isLocked,
  setPin,
  unlock,
  lock,
  removePin,
  saveReferral,
  listReferrals,
  saveCorrection,
  listCorrections,
} from './storage';
export { buildReferral, smsLink, parseReferral } from './referral';
export { play, stop as stopAudio } from './audio';
export { syncPending, configureSync } from './sync';
export { bitmapFromFile };

/** Reads the photo, runs the quality gate and the model. The file name only matters to the mock model. */
export async function classifyFile(file: File | Blob): Promise<LeafResult> {
  const bmp = await bitmapFromFile(file);
  try {
    return await classifyLeaf(bmp);
  } finally {
    bmp.close();
  }
}

export interface AssembleOptions {
  leaves: LeafResult[];
  lang: Lang;
  date?: Date;
  memberId?: string;
  plotId?: string;
  consentMain: boolean;
  consentPhotos: boolean;
}

export function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Builds a Check from the leaf results: summary, season window and the answer from the rule table. */
export function assembleCheck(o: AssembleOptions): Check {
  const date = o.date ?? new Date();
  const summary = summarisePlot(o.leaves);
  const card = decide(summary, date);
  return {
    id: newId(),
    createdAt: date.toISOString(),
    lang: o.lang,
    leaves: o.leaves,
    summary,
    window: seasonWindow(date),
    answerId: card.id,
    memberId: o.memberId,
    plotId: o.plotId,
    consentMain: o.consentMain,
    consentPhotos: o.consentPhotos,
    synced: false,
    synthetic: false,
  };
}
