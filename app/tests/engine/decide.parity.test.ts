import { describe, expect, it } from 'vitest';
import { decideForWindow } from '../../src/engine/decide';
import matrix from './fixtures/decision_matrix.json';
import { LABELS, type Label, type PlotSummary, type SeasonWindow } from '../../src/engine/types';

interface Row { dominant: Label | 'none'; affected: number; uncertain: number; distinct: number; window: SeasonWindow; card: string }
const rows = (matrix as unknown as { rows: Row[] }).rows;

describe('decision parity with qa/checks/decision_matrix.py', () => {
  it(`matches the Python reference on all ${rows.length} rows`, () => {
    const counts = Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
    const mismatches: string[] = [];
    for (const r of rows) {
      const s: PlotSummary = {
        n: 10, counts, dominant: r.dominant, affected: r.affected, uncertain: r.uncertain, distinctProblems: r.distinct,
      };
      const got = decideForWindow(s, r.window).id;
      if (got !== r.card) mismatches.push(`${JSON.stringify(r)} got ${got}`);
    }
    expect(rows.length).toBe(3510);
    expect(mismatches.slice(0, 20)).toEqual([]);
  });
});
