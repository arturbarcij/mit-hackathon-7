import { LABELS, leafResultFromBadQuality, leafResultFromProbs, zeroProbs } from './scoring';
import { assessRgba } from './quality';
import type { Label, LeafResult, QualityResult } from './types';

export const MOCK_VERSION = 'mock';
export const MOCK_THRESHOLD = 0.6;
let forcedHint: string | null = null;

const KEYWORDS: [RegExp, Label][] = [
  [/not[_-]?leaf|table|hand|soil|paper/i, 'not_leaf'],
  [/rust/i, 'rust'],
  [/cerco/i, 'cercospora'],
  [/phoma/i, 'phoma'],
  [/miner/i, 'miner'],
  [/health/i, 'healthy'],
];

/**
 * Deterministic fake probabilities from the file name. "rust" gives rust at 0.9, "blur" or
 * "unsure" gives a flat low-confidence answer, anything else is healthy at 0.9.
 */
export function mockProbs(name: string): Record<Label, number> {
  const probs = zeroProbs();
  if (/blur|unsure|unclear/i.test(name)) {
    probs.healthy = 0.34;
    probs.rust = 0.33;
    probs.cercospora = 0.1;
    probs.phoma = 0.1;
    probs.miner = 0.08;
    probs.not_leaf = 0.05;
    return probs;
  }
  const hit = KEYWORDS.find(([re]) => re.test(name));
  const top: Label = hit ? hit[1] : 'healthy';
  const rest = LABELS.filter((l) => l !== top);
  for (const l of rest) probs[l] = 0.1 / rest.length;
  probs[top] = 0.9;
  return probs;
}

export function classifyMock(name: string, quality: QualityResult): LeafResult {
  return leafResultFromProbs(mockProbs(forcedHint ?? name), MOCK_THRESHOLD, quality, MOCK_VERSION);
}

export function setMockHint(hint: string | null): void {
  forcedHint = hint;
}

/** Backward-compatible helper for tests that classify synthetic RGBA inputs directly. */
export function classifyRgba(
  width: number,
  height: number,
  rgba: Uint8ClampedArray,
  hint = 'healthy',
): LeafResult {
  const quality = assessRgba(width, height, rgba);
  if (!quality.ok) return leafResultFromBadQuality(quality, MOCK_VERSION);
  return classifyMock(hint, quality);
}
