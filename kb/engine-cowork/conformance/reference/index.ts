// Reference implementation of the pure parts of the Jani engine (kb/CONTRACTS.md).
// No DOM, no model, no storage. loadModel, checkQuality, classifyLeaf, saveCheck,
// listChecks, getConsent, setConsent, play and syncPending are the engine agent's;
// they are not implemented here. The conformance suite only needs the pure functions.
export * from './types';
export { summarisePlot } from './plot';
export { seasonWindow } from './season';
export { decide } from './decide';
export { buildReferral, parseReferral, smsLink } from './referral';
export { gsm7Length, isGsm7 } from './gsm7';
