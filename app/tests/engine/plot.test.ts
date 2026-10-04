import { describe, expect, it } from 'vitest';
import { summarisePlot } from '../../src/engine/plot';
import { LABELS, type Label, type LeafResult } from '../../src/engine/types';

function leaf(label: Label | 'unsure'): LeafResult {
  const probs = Object.fromEntries(LABELS.map((l) => [l, l === label ? 0.9 : 0.02])) as Record<Label, number>;
  return {
    label,
    probs,
    confidence: label === 'unsure' ? 0.4 : 0.9,
    quality: { ok: true, blur: 200, brightness: 120 },
    abstained: label === 'unsure',
    modelVersion: 'test',
  };
}
const leaves = (spec: Partial<Record<Label | 'unsure', number>>): LeafResult[] =>
  Object.entries(spec).flatMap(([l, k]) => Array.from({ length: k ?? 0 }, () => leaf(l as Label | 'unsure')));

describe('summarisePlot', () => {
  it('counts every label including healthy and not_leaf', () => {
    const s = summarisePlot(leaves({ healthy: 4, rust: 3, miner: 1, not_leaf: 1, unsure: 1 }));
    expect(s.n).toBe(10);
    expect(s.counts).toEqual({ healthy: 4, rust: 3, cercospora: 0, phoma: 0, miner: 1, not_leaf: 1 });
    expect(s.affected).toBe(4);
    expect(s.distinctProblems).toBe(2);
    expect(s.uncertain).toBe(2);
    expect(s.dominant).toBe('rust');
  });

  it('never puts unsure leaves into counts', () => {
    const s = summarisePlot(leaves({ healthy: 2, unsure: 8 }));
    expect(Object.values(s.counts).reduce((a, b) => a + b, 0)).toBe(2);
    expect(s.uncertain).toBe(8);
    expect(s.dominant).toBe('healthy');
  });

  it('breaks disease ties in order rust, cercospora, phoma, miner', () => {
    expect(summarisePlot(leaves({ miner: 2, rust: 2 })).dominant).toBe('rust');
    expect(summarisePlot(leaves({ miner: 2, phoma: 2, cercospora: 2 })).dominant).toBe('cercospora');
    expect(summarisePlot(leaves({ miner: 1, phoma: 1 })).dominant).toBe('phoma');
    expect(summarisePlot(leaves({ miner: 3, rust: 2 })).dominant).toBe('miner');
  });

  it('a single disease leaf beats many healthy leaves', () => {
    expect(summarisePlot(leaves({ healthy: 9, cercospora: 1 })).dominant).toBe('cercospora');
  });

  it('not_leaf wins only when more than half of n', () => {
    expect(summarisePlot(leaves({ not_leaf: 6, rust: 4 })).dominant).toBe('not_leaf');
    // Exactly half is not a majority.
    const half = summarisePlot(leaves({ not_leaf: 5, rust: 2, healthy: 3 }));
    expect(half.dominant).toBe('rust');
    expect(half.uncertain).toBe(5);
    expect(summarisePlot(leaves({ not_leaf: 5, healthy: 5 })).dominant).toBe('healthy');
    expect(summarisePlot(leaves({ not_leaf: 5, unsure: 5 })).dominant).toBe('none');
  });

  it('all unsure gives none', () => {
    const s = summarisePlot(leaves({ unsure: 10 }));
    expect(s.dominant).toBe('none');
    expect(s.affected).toBe(0);
    expect(s.distinctProblems).toBe(0);
    expect(s.uncertain).toBe(10);
  });

  it('no leaves gives an empty summary', () => {
    const s = summarisePlot([]);
    expect(s).toMatchObject({ n: 0, dominant: 'none', affected: 0, uncertain: 0, distinctProblems: 0 });
  });
});
