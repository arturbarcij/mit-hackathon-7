import type { Label, LeafResult, QualityResult } from './types';

export const LABELS: readonly Label[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];

export function zeroProbs(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
}

/** Softmax of logits divided by the calibration temperature. Numerically stable. */
export function calibratedSoftmax(logits: ArrayLike<number>, temperature: number): number[] {
  const t = temperature > 0 && Number.isFinite(temperature) ? temperature : 1;
  let max = -Infinity;
  for (let i = 0; i < logits.length; i++) max = Math.max(max, logits[i] / t);
  const exps: number[] = [];
  let sum = 0;
  for (let i = 0; i < logits.length; i++) {
    const e = Math.exp(logits[i] / t - max);
    exps.push(e);
    sum += e;
  }
  return exps.map((e) => e / sum);
}

export function probsRecord(labels: readonly Label[], probs: ArrayLike<number>): Record<Label, number> {
  const rec = zeroProbs();
  labels.forEach((label, i) => {
    rec[label] = probs[i] ?? 0;
  });
  return rec;
}

/** Applies the abstention threshold. Below it the leaf is 'unsure' and flagged as abstained. */
export function leafResultFromProbs(
  probs: Record<Label, number>,
  threshold: number,
  quality: QualityResult,
  modelVersion: string,
): LeafResult {
  let top: Label = LABELS[0];
  for (const l of LABELS) if (probs[l] > probs[top]) top = l;
  const confidence = probs[top];
  const abstained = !(confidence >= threshold);
  return {
    label: abstained ? 'unsure' : top,
    probs,
    confidence,
    quality,
    abstained,
    modelVersion,
  };
}

/** Result for a photo that failed the quality gate. No inference is run. */
export function leafResultFromBadQuality(quality: QualityResult, modelVersion: string): LeafResult {
  return {
    label: 'unsure',
    probs: zeroProbs(),
    confidence: 0,
    quality,
    abstained: true,
    modelVersion,
  };
}
