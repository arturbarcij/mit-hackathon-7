import { LABELS, type Label, type QualityResult } from './types.ts';

export interface MockClassification {
  label: Label | 'unsure';
  probs: Record<Label, number>;
  confidence: number;
  abstained: boolean;
  modelVersion: 'mock';
  quality?: QualityResult;
}

let hintOverride = '';

export function setMockHint(name: string): void {
  hintOverride = name;
}

export function getMockHint(): string {
  return hintOverride;
}

export function probsFor(label: Label | null, confidence: number): Record<Label, number> {
  const probs = {
    healthy: 0,
    rust: 0,
    cercospora: 0,
    phoma: 0,
    miner: 0,
    not_leaf: 0,
  };
  if (!label) {
    const share = 1 / LABELS.length;
    let sum = 0;
    for (const name of LABELS) {
      probs[name] = share;
      sum += share;
    }
    probs[LABELS[LABELS.length - 1]] += 1 - sum;
    return probs;
  }
  const rest = (1 - confidence) / (LABELS.length - 1);
  let sum = 0;
  for (const name of LABELS) {
    probs[name] = name === label ? confidence : rest;
    sum += probs[name];
  }
  const adjust = LABELS.find((name) => name !== label) ?? LABELS[0];
  probs[adjust] += 1 - sum;
  return probs;
}

function maxProb(probs: Record<Label, number>): number {
  let best = 0;
  for (const name of LABELS) if (probs[name] > best) best = probs[name];
  return best;
}

function sure(label: Label, confidence: number): MockClassification {
  const probs = probsFor(label, confidence);
  return {
    label,
    probs,
    confidence,
    abstained: false,
    modelVersion: 'mock',
  };
}

function qualityAbstain(reason: 'blurry' | 'dark' | 'too_small', blur: number, brightness: number): MockClassification {
  const probs = probsFor(null, 0);
  return {
    label: 'unsure',
    probs,
    confidence: maxProb(probs),
    abstained: true,
    modelVersion: 'mock',
    quality: { ok: false, reason, blur, brightness },
  };
}

export function mockClassify(hint: string): MockClassification {
  const name = hint.toLowerCase();
  if (name.includes('blur')) return qualityAbstain('blurry', 5, 128);
  if (name.includes('dark')) return qualityAbstain('dark', 80, 10);
  if (name.includes('tiny') || name.includes('small')) return qualityAbstain('too_small', 0, 0);
  if (name.includes('notleaf') || name.includes('paper') || name.includes('hand')) return sure('not_leaf', 0.9);
  if (name.includes('rust')) return sure('rust', 0.9);
  if (name.includes('cercospora') || name.includes('brown')) return sure('cercospora', 0.88);
  if (name.includes('phoma')) return sure('phoma', 0.88);
  if (name.includes('miner')) return sure('miner', 0.88);
  if (name.includes('healthy')) return sure('healthy', 0.92);
  const probs = probsFor(null, 0);
  return {
    label: 'unsure',
    probs,
    confidence: maxProb(probs),
    abstained: true,
    modelVersion: 'mock',
  };
}
