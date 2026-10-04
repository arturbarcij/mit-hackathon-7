// summarisePlot conformance, one case per clause of CONTRACTS "summarisePlot semantics".
import { describe, expect, it } from 'vitest';
import { need } from './engine-under-test';
import { leavesFrom, type emptyCounts } from './fixtures';
import type { Label, PlotSummary } from '../reference/types';

type Counts = Partial<Record<Label | 'unsure', number>>;
type Expected = Partial<Omit<PlotSummary, 'counts'>> & { counts?: Partial<ReturnType<typeof emptyCounts>> };

interface Case { name: string; leaves: Counts; expect: Expected; }

const CASES: Case[] = [
  { name: 'empty list: n 0, dominant none', leaves: {}, expect: { n: 0, dominant: 'none', affected: 0, uncertain: 0, distinctProblems: 0 } },
  { name: 'all healthy: dominant healthy, affected 0', leaves: { healthy: 10 }, expect: { n: 10, dominant: 'healthy', affected: 0, uncertain: 0, distinctProblems: 0, counts: { healthy: 10 } } },
  { name: '6 rust + 4 healthy: dominant rust, affected 6', leaves: { rust: 6, healthy: 4 }, expect: { dominant: 'rust', affected: 6, distinctProblems: 1, uncertain: 0 } },
  { name: 'one disease leaf is enough for dominant', leaves: { healthy: 9, phoma: 1 }, expect: { dominant: 'phoma', affected: 1, distinctProblems: 1 } },
  { name: 'disease beats healthy even when healthy is more common', leaves: { healthy: 8, miner: 2 }, expect: { dominant: 'miner', affected: 2 } },
  { name: 'uncertain = unsure + not_leaf', leaves: { healthy: 6, unsure: 2, not_leaf: 2 }, expect: { uncertain: 4, affected: 0, dominant: 'healthy', counts: { not_leaf: 2, healthy: 6 } } },
  { name: 'unsure leaves are not counted in counts', leaves: { healthy: 7, unsure: 3 }, expect: { n: 10, uncertain: 3, counts: { healthy: 7, rust: 0, not_leaf: 0 } } },
  { name: 'not_leaf is not affected', leaves: { not_leaf: 3, rust: 2, healthy: 5 }, expect: { affected: 2, uncertain: 3, dominant: 'rust' } },
  { name: 'distinctProblems counts labels, not leaves', leaves: { rust: 5, cercospora: 1, phoma: 1, miner: 1, healthy: 2 }, expect: { distinctProblems: 4, affected: 8, dominant: 'rust' } },
  { name: 'most common disease wins', leaves: { rust: 1, cercospora: 4, healthy: 5 }, expect: { dominant: 'cercospora', distinctProblems: 2 } },
  { name: 'tie rust vs cercospora: rust', leaves: { rust: 3, cercospora: 3, healthy: 4 }, expect: { dominant: 'rust' } },
  { name: 'tie cercospora vs phoma: cercospora', leaves: { cercospora: 2, phoma: 2, healthy: 6 }, expect: { dominant: 'cercospora' } },
  { name: 'tie phoma vs miner: phoma', leaves: { miner: 2, phoma: 2, healthy: 6 }, expect: { dominant: 'phoma' } },
  { name: 'four-way tie: rust', leaves: { miner: 1, phoma: 1, cercospora: 1, rust: 1, healthy: 6 }, expect: { dominant: 'rust', distinctProblems: 4 } },
  { name: 'tie with healthy equal does not matter', leaves: { rust: 2, miner: 2, healthy: 2, unsure: 4 }, expect: { dominant: 'rust', uncertain: 4 } },
  { name: 'all unsure: dominant none, uncertain n', leaves: { unsure: 10 }, expect: { n: 10, dominant: 'none', uncertain: 10, affected: 0, distinctProblems: 0 } },
  { name: 'not_leaf exactly half (5 of 10) is NOT dominant; healthy wins', leaves: { not_leaf: 5, healthy: 5 }, expect: { dominant: 'healthy', uncertain: 5 } },
  { name: 'not_leaf exactly half with a disease present: disease wins', leaves: { not_leaf: 5, rust: 1, healthy: 4 }, expect: { dominant: 'rust', uncertain: 5, affected: 1 } },
  { name: 'not_leaf more than half (6 of 10) is dominant even with rust', leaves: { not_leaf: 6, rust: 4 }, expect: { dominant: 'not_leaf', uncertain: 6, affected: 4, distinctProblems: 1 } },
  { name: 'not_leaf majority on odd n (2 of 3)', leaves: { not_leaf: 2, healthy: 1 }, expect: { n: 3, dominant: 'not_leaf', uncertain: 2 } },
  { name: 'not_leaf exactly half on even small n (1 of 2)', leaves: { not_leaf: 1, healthy: 1 }, expect: { dominant: 'healthy' } },
  { name: 'single not_leaf: dominant not_leaf (1 of 1)', leaves: { not_leaf: 1 }, expect: { n: 1, dominant: 'not_leaf', uncertain: 1, affected: 0 } },
  { name: 'not_leaf half + unsure half: none', leaves: { not_leaf: 5, unsure: 5 }, expect: { dominant: 'none', uncertain: 10 } },
  { name: 'unsure + not_leaf, no accepted leaf, not_leaf minority: none', leaves: { not_leaf: 2, unsure: 8 }, expect: { dominant: 'none', uncertain: 10, affected: 0 } },
  { name: 'n counts every leaf including unsure and not_leaf', leaves: { healthy: 3, rust: 2, unsure: 2, not_leaf: 3 }, expect: { n: 10, uncertain: 5, affected: 2 } },
];

describe('summarisePlot', () => {
  const summarisePlot = need('summarisePlot');

  it.each(CASES)('$name', ({ leaves, expect: exp }) => {
    const s = summarisePlot(leavesFrom(leaves));
    const { counts, ...rest } = exp;
    for (const [k, v] of Object.entries(rest)) expect(s[k as keyof PlotSummary], k).toBe(v);
    if (counts) for (const [k, v] of Object.entries(counts)) expect(s.counts[k as Label], `counts.${k}`).toBe(v);
  });

  it('counts has every label key, including zeros', () => {
    const s = summarisePlot(leavesFrom({ healthy: 1 }));
    for (const l of ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf']) {
      expect(typeof s.counts[l as Label]).toBe('number');
    }
  });

  it('invariant over 500 random plots: n = sum(counts) + unsure; uncertain = unsure + not_leaf; affected = sum(diseases)', () => {
    const labels: (Label | 'unsure')[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf', 'unsure'];
    let seed = 7;
    const next = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed; };
    for (let i = 0; i < 500; i++) {
      const n = next() % 11;
      const counts: Counts = {};
      for (let j = 0; j < n; j++) { const l = labels[next() % labels.length]; counts[l] = (counts[l] ?? 0) + 1; }
      const s = summarisePlot(leavesFrom(counts));
      const unsure = counts.unsure ?? 0;
      const sumCounts = Object.values(s.counts).reduce((a, b) => a + b, 0);
      expect(s.n).toBe(n);
      expect(sumCounts + unsure).toBe(n);
      expect(s.uncertain).toBe(unsure + s.counts.not_leaf);
      expect(s.affected).toBe(s.counts.rust + s.counts.cercospora + s.counts.phoma + s.counts.miner);
      expect(s.distinctProblems).toBe(['rust', 'cercospora', 'phoma', 'miner'].filter((d) => s.counts[d as Label] > 0).length);
      if (s.counts.not_leaf * 2 > n) expect(s.dominant).toBe('not_leaf');
      else if (s.affected > 0) expect(['rust', 'cercospora', 'phoma', 'miner']).toContain(s.dominant);
      else if (s.counts.healthy > 0) expect(s.dominant).toBe('healthy');
      else expect(s.dominant).toBe('none');
    }
  });
});
