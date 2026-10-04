import type { Check, Label, LeafResult, QualityResult } from '../../src/engine/types';
import { leafResultFromProbs, zeroProbs } from '../../src/engine/scoring';
import { summarisePlot } from '../../src/engine/plot';

export const goodQuality: QualityResult = { ok: true, blur: 200, brightness: 140 };

export function leaf(label: Label | 'unsure', confidence = 0.9): LeafResult {
  if (label === 'unsure') {
    const probs = zeroProbs();
    probs.healthy = 0.3;
    probs.rust = 0.3;
    return leafResultFromProbs(probs, 0.6, goodQuality, 'test');
  }
  const probs = zeroProbs();
  probs[label] = confidence;
  const others = (Object.keys(probs) as Label[]).filter((l) => l !== label);
  for (const o of others) probs[o] = (1 - confidence) / others.length;
  return leafResultFromProbs(probs, 0.6, goodQuality, 'test');
}

export function leaves(spec: Partial<Record<Label | 'unsure', number>>): LeafResult[] {
  const out: LeafResult[] = [];
  for (const [label, n] of Object.entries(spec) as [Label | 'unsure', number][]) {
    for (let i = 0; i < n; i++) out.push(leaf(label));
  }
  return out;
}

export function makeCheck(over: Partial<Check> = {}): Check {
  const ls = over.leaves ?? leaves({ rust: 6, healthy: 2, miner: 1, unsure: 1 });
  return {
    id: 'c1',
    createdAt: new Date(2026, 9, 4, 10, 0, 0).toISOString(),
    lang: 'sw',
    leaves: ls,
    summary: summarisePlot(ls),
    window: 'pre_short_rains',
    answerId: 'rust_high_pre_rains',
    memberId: 'OCC0412',
    plotId: '2',
    consentMain: true,
    consentPhotos: false,
    synced: false,
    synthetic: true,
    ...over,
  };
}

// Backward-compatible aliases for older tests.
export const emptyLeaf = leaf;
export function summaryOf(labels: (Label | 'unsure')[]) {
  return summarisePlot(labels.map((l) => leaf(l)));
}
