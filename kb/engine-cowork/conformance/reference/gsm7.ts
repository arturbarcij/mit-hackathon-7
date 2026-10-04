// GSM 03.38 default alphabet length counter. Basic characters count 1 septet,
// extension table characters count 2 (escape plus character). Anything else is
// not GSM-7 and would force the SMS into UCS-2 (70 characters per message).

const GSM7_BASIC =
  '@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?' +
  '¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà';
const GSM7_EXTENSION = '\f^{}\\[~]|€';

const BASIC = new Set(Array.from(GSM7_BASIC));
const EXT = new Set(Array.from(GSM7_EXTENSION));

/** Septets needed for one character, or null if it is outside GSM-7. */
export function gsm7CharLength(ch: string): 1 | 2 | null {
  if (BASIC.has(ch)) return 1;
  if (EXT.has(ch)) return 2;
  return null;
}

/** True when every character is in the GSM-7 basic or extension table. */
export function isGsm7(text: string): boolean {
  for (const ch of text) if (gsm7CharLength(ch) === null) return false;
  return true;
}

/**
 * Length in GSM-7 septets. Characters outside GSM-7 are counted as NaN so the
 * caller's "<= 160" check fails; use isGsm7 first for a clear error.
 */
export function gsm7Length(text: string): number {
  let total = 0;
  for (const ch of text) {
    const l = gsm7CharLength(ch);
    if (l === null) return Number.NaN;
    total += l;
  }
  return total;
}

/** Drop every character that is not GSM-7. */
export function stripNonGsm7(text: string): string {
  let out = '';
  for (const ch of text) if (gsm7CharLength(ch) !== null) out += ch;
  return out;
}

export const SMS_GSM7_MAX = 160;
