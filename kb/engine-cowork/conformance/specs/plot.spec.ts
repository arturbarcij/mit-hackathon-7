// summarisePlot against the exact semantics in kb/CONTRACTS.md.
import { describe, expect, it } from 'vitest';
import * as engine from '@engine';
import { DISEASES, LABELS, leaf, leaves, mulberry32, type AnyLabel } from './helpers';

const summarisePlot = (engine as any).summarisePlot as (l: any[]) => any;

/** Oracle written straight from the CONTRACTS text, one bullet per line. */
function oracle(ls: { label: AnyLabel }[]) {
  const counts: Record<string, number> = Object.fromEntries(LABELS.map((l) => [l, 0]));
  let unsure = 0;
  for (const l of ls) (l.label === 'unsure' ? unsure++ : counts[l.label]++);
  const n = ls.length;                                                     // n = leaves photographed
  const affected = DISEASES.reduce((s, d) => s + counts[d], 0);            // leaves with a disease label
  const distinctProblems = DISEASES.filter((d) => counts[d] > 0).length;   // distinct disease labels present
  const uncertain = unsure + counts.not_leaf;                              // unsure PLUS not_leaf
  let dominant: string;
  if (counts.not_leaf > n / 2) dominant = 'not_leaf';                      // not_leaf more than half of n
  else if (affected >= 1) {                                                // most common disease, ties in order
    const max = Math.max(...DISEASES.map((d) => counts[d]));
    dominant = DISEASES.find((d) => counts[d] === max)!;
  } else if (counts.healthy > 0) dominant = 'healthy';
  else dominant = 'none';
  return { n, counts, uncertain, dominant, affected, distinctProblems };
}

const pick = (s: any) => ({ n: s.n, counts: s.counts, uncertain: s.uncertain, dominant: s.dominant, affected: s.affected, distinctProblems: s.distinctProblems });

describe('summarisePlot: named cases', () => {
  it('is exported', () => expect(typeof summarisePlot).toBe('function'));

  it('empty input gives n 0, all counts 0, dominant none', () => {
    expect(pick(summarisePlot([]))).toEqual({ n: 0, counts: { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 }, uncertain: 0, dominant: 'none', affected: 0, distinctProblems: 0 });
  });

  it('healthy only gives dominant healthy, nothing affected', () => {
    const s = summarisePlot(leaves({ healthy: 10 }));
    expect(pick(s)).toEqual({ n: 10, counts: { healthy: 10, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 }, uncertain: 0, dominant: 'healthy', affected: 0, distinctProblems: 0 });
  });

  it('all unsure gives dominant none and uncertain = n; unsure is never forced into a class', () => {
    const s = summarisePlot(leaves({ unsure: 10 }));
    expect(pick(s)).toEqual({ n: 10, counts: { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 }, uncertain: 10, dominant: 'none', affected: 0, distinctProblems: 0 });
  });

  it('uncertain = unsure plus not_leaf', () => {
    const s = summarisePlot(leaves({ unsure: 2, not_leaf: 3, healthy: 5 }));
    expect(s.uncertain).toBe(5);
    expect(s.counts.not_leaf).toBe(3);
  });

  it('not_leaf more than half of n gives dominant not_leaf, even with diseased leaves', () => {
    expect(summarisePlot(leaves({ not_leaf: 6, rust: 4 })).dominant).toBe('not_leaf');
    expect(summarisePlot(leaves({ not_leaf: 1 })).dominant).toBe('not_leaf');
    expect(summarisePlot(leaves({ not_leaf: 2, healthy: 1 })).dominant).toBe('not_leaf');
  });

  it('not_leaf at exactly half of n is not dominant', () => {
    expect(summarisePlot(leaves({ not_leaf: 5, rust: 5 })).dominant).toBe('rust');
    expect(summarisePlot(leaves({ not_leaf: 5, healthy: 5 })).dominant).toBe('healthy');
    expect(summarisePlot(leaves({ not_leaf: 5, unsure: 5 })).dominant).toBe('none');
  });

  it('a disease beats healthy even when healthy is the majority', () => {
    expect(summarisePlot(leaves({ healthy: 9, miner: 1 })).dominant).toBe('miner');
  });

  const ties: [Partial<Record<AnyLabel, number>>, string][] = [
    [{ rust: 2, cercospora: 2 }, 'rust'], [{ cercospora: 2, rust: 2 }, 'rust'],
    [{ cercospora: 3, phoma: 3 }, 'cercospora'], [{ phoma: 1, cercospora: 1 }, 'cercospora'],
    [{ phoma: 2, miner: 2 }, 'phoma'], [{ miner: 2, phoma: 2 }, 'phoma'],
    [{ miner: 1, rust: 1, cercospora: 1, phoma: 1 }, 'rust'], [{ miner: 2, cercospora: 2, healthy: 6 }, 'cercospora'],
  ];
  it.each(ties)('tie %o is broken in the order rust, cercospora, phoma, miner -> %s', (spec, want) => {
    expect(summarisePlot(leaves(spec)).dominant).toBe(want);
    expect(summarisePlot(leaves(spec).reverse()).dominant).toBe(want);
  });

  it('affected and distinctProblems count disease labels only (not unsure, not not_leaf, not healthy)', () => {
    const s = summarisePlot(leaves({ rust: 3, phoma: 1, unsure: 2, not_leaf: 1, healthy: 3 }));
    expect(s.affected).toBe(4);
    expect(s.distinctProblems).toBe(2);
    expect(s.n).toBe(10);
  });

  it('a failed-quality leaf (label unsure) counts as uncertain, not affected', () => {
    const s = summarisePlot([leaf('unsure', 0.95, false), leaf('rust')]);
    expect(s.uncertain).toBe(1);
    expect(s.affected).toBe(1);
  });

  it('does not mutate its input', () => {
    const input = leaves({ rust: 2, unsure: 1 });
    const copy = JSON.parse(JSON.stringify(input));
    summarisePlot(input);
    expect(input).toEqual(copy);
  });
});

describe('summarisePlot: seeded property tests against the oracle', () => {
  const pool: AnyLabel[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf', 'unsure'];
  for (const seed of [1, 7, 42, 2026, 31337]) {
    it(`seed ${seed}: 400 random plots match the oracle`, () => {
      const rnd = mulberry32(seed);
      const bad: string[] = [];
      for (let i = 0; i < 400; i++) {
        const n = Math.floor(rnd() * 21);
        const w = pool.map(() => rnd() ** 2);
        const tot = w.reduce((a, b) => a + b, 0);
        const ls = Array.from({ length: n }, () => {
          let r = rnd() * tot;
          for (let k = 0; k < pool.length; k++) if ((r -= w[k]) <= 0) return leaf(pool[k]);
          return leaf('unsure');
        });
        const got = pick(summarisePlot(ls));
        const want = oracle(ls);
        if (JSON.stringify(got) !== JSON.stringify(want)) bad.push(`${JSON.stringify(ls.map((l: any) => l.label))} got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
      }
      expect(bad.slice(0, 5), `${bad.length} of 400 differ`).toEqual([]);
    });
  }

  it('invariants hold on 2000 random plots', () => {
    const rnd = mulberry32(99);
    for (let i = 0; i < 2000; i++) {
      const ls = Array.from({ length: Math.floor(rnd() * 15) }, () => leaf(pool[Math.floor(rnd() * pool.length)]));
      const s = summarisePlot(ls);
      const unsure = ls.filter((l: any) => l.label === 'unsure').length;
      expect(s.n).toBe(ls.length);
      expect(LABELS.reduce((a, l) => a + s.counts[l], 0) + unsure).toBe(s.n);
      expect(s.uncertain).toBe(unsure + s.counts.not_leaf);
      expect(s.affected).toBeLessThanOrEqual(s.n);
      expect(s.distinctProblems).toBeLessThanOrEqual(Math.min(4, s.affected));
      expect(['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf', 'none']).toContain(s.dominant);
    }
  });
});
