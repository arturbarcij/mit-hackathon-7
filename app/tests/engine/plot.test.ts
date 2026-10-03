import { describe, expect, it } from 'vitest';
import { summarisePlot } from '../../src/engine/plot';
import { leaves } from './helpers';

describe('summarisePlot', () => {
  it('counts classes and keeps unsure leaves separate', () => {
    const s = summarisePlot(leaves({ rust: 6, healthy: 2, miner: 1, unsure: 1 }));
    expect(s.n).toBe(10);
    expect(s.counts.rust).toBe(6);
    expect(s.counts.healthy).toBe(2);
    expect(s.uncertain).toBe(1);
    expect(s.affected).toBe(7);
    expect(s.distinctProblems).toBe(2);
    expect(s.dominant).toBe('rust');
    const classed = Object.values(s.counts).reduce((a, b) => a + b, 0);
    expect(classed + s.uncertain).toBe(s.n);
  });

  it('is healthy when only healthy leaves are present', () => {
    const s = summarisePlot(leaves({ healthy: 10 }));
    expect(s.dominant).toBe('healthy');
    expect(s.affected).toBe(0);
  });

  it('is none for an empty or all-unsure plot', () => {
    expect(summarisePlot([]).dominant).toBe('none');
    expect(summarisePlot(leaves({ unsure: 4 })).dominant).toBe('none');
  });

  it('one stray non-leaf photo does not decide the plot', () => {
    const s = summarisePlot(leaves({ healthy: 9, not_leaf: 1 }));
    expect(s.dominant).toBe('healthy');
  });

  it('mostly non-leaf photos make not_leaf dominant', () => {
    expect(summarisePlot(leaves({ healthy: 3, not_leaf: 3 })).dominant).toBe('not_leaf');
  });

  it('breaks ties in a fixed order', () => {
    expect(summarisePlot(leaves({ phoma: 2, cercospora: 2 })).dominant).toBe('cercospora');
  });
});
