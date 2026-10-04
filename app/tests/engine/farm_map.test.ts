import { describe, expect, it } from 'vitest';
import type { Check } from '../../src/engine';
import { blockPlotId, blockStates, COFFEE_BLOCKS, exampleChecks, nextBlock, RECHECK_DAYS, unassignedChecks } from '../../src/ui/farm';
import { buildReferral, parseReferral } from '../../src/engine';

const NOW = new Date(2026, 9, 4, 10, 0, 0); // 4 Oct 2026, pre short rains

describe('farm map', () => {
  it('has four coffee blocks with SMS-safe plot ids', () => {
    expect(COFFEE_BLOCKS.map((b) => b.id)).toEqual(['C1', 'C2', 'C3', 'C4']);
    for (const b of COFFEE_BLOCKS) expect(blockPlotId(b.id)).toMatch(/^[A-Z0-9-]{1,12}$/);
  });

  it('with no checks every block is not checked and overdue', () => {
    const s = blockStates([], NOW);
    expect(s.every((x) => x.status === 'none' && x.overdue && x.last === null)).toBe(true);
    expect(nextBlock(s)?.block.id).toBe('C1');
  });

  it('example farm takes its answers from the rule table and is never marked as real', () => {
    const ex = exampleChecks(NOW);
    expect(ex.every((c) => c.id.startsWith('example-'))).toBe(true);
    const s = blockStates(ex, NOW);
    const by = Object.fromEntries(s.map((x) => [x.block.id, x]));
    expect(by.C1.status).toBe('act'); // 6 of 10 rust before the short rains
    expect(by.C1.last?.answerId).toBe('rust_high_pre_rains');
    expect(by.C2.status).toBe('ok');
    expect(by.C2.overdue).toBe(true); // 30 days > RECHECK_DAYS
    expect(by.C3.status).toBe('ask'); // 4 unsure leaves go to a person
    expect(by.C4.status).toBe('none');
    expect(RECHECK_DAYS).toBe(21);
  });

  it('latest check per block wins and due date is 21 days on', () => {
    const [a] = exampleChecks(NOW);
    const older: Check = { ...a, id: 'old', createdAt: new Date(2026, 8, 1).toISOString(), answerId: 'healthy_all' };
    const s = blockStates([older, a], NOW).find((x) => x.block.id === 'C1')!;
    expect(s.last?.id).toBe(a.id);
    expect(s.count).toBe(2);
    expect(s.overdue).toBe(false);
    expect(s.due!.getTime() - new Date(a.createdAt).setHours(0, 0, 0, 0)).toBe(21 * 86_400_000);
  });

  it('next block: overdue and unchecked come before checked ones', () => {
    const s = blockStates(exampleChecks(NOW), NOW);
    const n = nextBlock(s)!;
    expect(n.overdue).toBe(true);
    expect(['C2', 'C4']).toContain(n.block.id);
  });

  it('old farm-level checks are counted as unassigned', () => {
    const [a] = exampleChecks(NOW);
    expect(unassignedChecks([{ ...a, plotId: 'P07' }, { ...a, plotId: undefined }, a])).toBe(2);
  });

  it('block plot id survives the referral SMS round trip', () => {
    const [a] = exampleChecks(NOW);
    const body = buildReferral({ ...a, memberId: 'OCC0412' });
    expect(body.length).toBeLessThanOrEqual(160);
    expect(parseReferral(body)?.plot_id).toBe('P07-C1');
  });
});
