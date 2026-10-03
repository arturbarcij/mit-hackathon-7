import { describe, expect, it } from 'vitest';
import { summarisePlot } from '../../src/engine/plot.ts';
import type { Label, LeafResult } from '../../src/engine/types.ts';

function leaf(label: Label | 'unsure', extra?: Partial<LeafResult>): LeafResult {
  const probs = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
  if (label !== 'unsure') probs[label] = 0.9;
  return {
    label,
    probs,
    confidence: label === 'unsure' ? 0.2 : 0.9,
    quality: { ok: true, blur: 100, brightness: 128 },
    abstained: label === 'unsure',
    modelVersion: 'mock',
    ...extra,
  };
}

describe('summarisePlot', () => {
  it('does not count uncertain leaves as a class', () => {
    const summary = summarisePlot([
      leaf('rust'),
      leaf('rust', { abstained: true }),
      leaf('healthy', { quality: { ok: false, reason: 'dark', blur: 80, brightness: 10 } }),
      leaf('unsure', { abstained: true, label: 'unsure' }),
    ]);
    expect(summary.n).toBe(4);
    expect(summary.uncertain).toBe(3);
    expect(summary.counts.rust).toBe(1);
    expect(summary.counts.healthy).toBe(0);
    expect(summary.affected).toBe(1);
    expect(summary.dominant).toBe('rust');
  });

  it('uses none when problem labels tie', () => {
    const summary = summarisePlot([
      leaf('rust'),
      leaf('rust'),
      leaf('miner'),
      leaf('miner'),
    ]);
    expect(summary.dominant).toBe('none');
    expect(summary.distinctProblems).toBe(2);
    expect(summary.affected).toBe(4);
    expect(summary.counts.rust).toBe(2);
    expect(summary.counts.miner).toBe(2);
  });

  it('keeps a single problem label as dominant', () => {
    const summary = summarisePlot([leaf('rust'), leaf('healthy'), leaf('healthy'), leaf('healthy')]);
    expect(summary.dominant).toBe('rust');
    expect(summary.affected).toBe(1);
  });

  it('calls an all-healthy plot healthy', () => {
    const summary = summarisePlot([leaf('healthy'), leaf('healthy')]);
    expect(summary.dominant).toBe('healthy');
    expect(summary.affected).toBe(0);
    expect(summary.uncertain).toBe(0);
  });
});
