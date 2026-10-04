// Public engine API. Signatures: kb/CONTRACTS.md. The UI imports only from here.
// SSR-safe: importing this module must not touch window, document, navigator, indexedDB or Audio.
export * from './types';
export { loadModel, classifyLeaf } from './model';
export { checkQuality } from './quality';
export { sheetGate } from './gate';
export { decodeImage } from './image';
export type { GateResult } from './gate';
export { summarisePlot } from './plot';
export { seasonWindow } from './season';
export { decide, decideForWindow, getAnswer, MIN_LEAVES, TOO_FEW_ID } from './decide';
export {
  saveCheck,
  listChecks,
  getConsent,
  setConsent,
  clearAll,
  setPin,
  hasPin,
  unlock,
  lock,
  compressPhoto,
  savePhoto,
  getPhotos,
} from './storage';
export { buildReferral, smsLink, parseReferral, toGsm7 } from './referral';
export { play, stop, audioPath } from './audio';
export { setSyncSender, queueForSync, syncPending, toReferralRow } from './sync';
