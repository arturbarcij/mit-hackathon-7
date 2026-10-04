import { describe, expect, it, vi } from 'vitest';
import { MIN_LEAVES, decide, decideForWindow, getAnswer, ruleMatches } from '../../src/engine/decide';
import { summarisePlot } from '../../src/engine/plot';
import type { LeafResult } from '../../src/engine/types';
import { ANSWERS, RULES, answerById } from '../../src/engine/content';
import { LABELS, type Label, type PlotSummary, type SeasonWindow } from '../../src/engine/types';

const WINDOWS: SeasonWindow[] = ['pre_short_rains', 'short_rains', 'pre_long_rains', 'long_rains', 'dry'];

function summary(p: Partial<PlotSummary> & { dominant: Label | 'none' }): PlotSummary {
  const counts = Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
  return { n: 10, counts, uncertain: 0, affected: 0, distinctProblems: 0, ...p };
}

describe('content', () => {
  it('every rule points at an answer that exists', () => {
    for (const r of RULES) expect(answerById(r.then), r.then).toBeDefined();
  });
  it('last rule is the empty ask_officer catch-all', () => {
    const last = RULES[RULES.length - 1];
    expect(last.if).toEqual({});
    expect(last.then).toBe('ask_officer');
    expect(answerById('ask_officer')?.severity).toBe('ask');
  });
  it('answer ids are unique', () => {
    expect(new Set(ANSWERS.map((a) => a.id)).size).toBe(ANSWERS.length);
  });
});

describe('getAnswer', () => {
  it('maps answers.json fields onto AnswerCard', () => {
    const c = getAnswer('rust_high_pre_rains');
    const raw = answerById('rust_high_pre_rains')!;
    expect(c.id).toBe('rust_high_pre_rains');
    expect(c.severity).toBe(raw.severity);
    expect(c.text).toEqual(raw.text);
    expect(c.notSure).toEqual(raw.not_sure);
    expect(c.sources).toEqual(raw.sources);
    expect(c.assumption).toBe(raw.assumption);
    expect(c.kind).toBe(raw.kind);
    expect(c.reviewStatus).toEqual(raw.review_status);
    for (const lang of Object.keys(raw.text)) {
      expect(c.audio[lang as keyof typeof c.audio]).toBe(`/audio/${lang}/rust_high_pre_rains.mp3`);
    }
    expect(Object.keys(c.audio).sort()).toEqual(Object.keys(raw.text).sort());
  });
  it('unknown id returns the ask_officer card', () => {
    expect(getAnswer('no_such_card').id).toBe('ask_officer');
    expect(getAnswer('').severity).toBe('ask');
  });
});

describe('ruleMatches', () => {
  const s = summary({ dominant: 'rust', affected: 4, distinctProblems: 1 });
  it('an unknown condition key makes the rule not match', () => {
    expect(ruleMatches({ dominant: 'rust', colour: 'red' } as never, s, 'dry')).toBe(false);
  });
  it('a non-numeric threshold makes the rule not match', () => {
    expect(ruleMatches({ affected_gte: '3' } as never, s, 'dry')).toBe(false);
  });
  it('an empty condition always matches', () => {
    expect(ruleMatches({}, s, 'dry')).toBe(true);
  });
  it('n_lt compares the leaf count', () => {
    expect(ruleMatches({ n_lt: 10 }, s, 'dry')).toBe(false);
    expect(ruleMatches({ n_lt: 10 }, { ...s, n: 9 }, 'dry')).toBe(true);
  });
});

// Gate blocker B1 (4 Oct): fewer than 10 leaves must never give a plot answer.
describe('too few leaves', () => {
  const leaf = (label: LeafResult['label']): LeafResult => ({
    label, probs: {} as LeafResult['probs'], confidence: label === 'unsure' ? 0.4 : 0.9,
    quality: { ok: true, blur: 100, brightness: 0.5 }, abstained: label === 'unsure', modelVersion: 'test',
  });
  const day = new Date(2026, 9, 4, 12);
  it('MIN_LEAVES is 10, matching the 3-of-10 rule thresholds', () => {
    expect(MIN_LEAVES).toBe(10);
  });
  it('gives too_few_leaves (an ask card) for 0 to 9 leaves, whatever the labels', () => {
    for (let n = 0; n < MIN_LEAVES; n++) {
      for (const label of ['healthy', 'rust', 'unsure', 'not_leaf'] as const) {
        const card = decide(summarisePlot(Array.from({ length: n }, () => leaf(label))), day);
        expect(card.id, `${n} ${label}`).toBe('too_few_leaves');
        expect(card.severity).toBe('ask');
      }
    }
  });
  it('the judge probes: 1 healthy, 2 healthy + 2 unsure, 3 rust of 3, 1 rust', () => {
    const probes: LeafResult['label'][][] = [['healthy'], ['healthy', 'healthy', 'unsure', 'unsure'], ['rust', 'rust', 'rust'], ['rust']];
    for (const p of probes) expect(decide(summarisePlot(p.map(leaf)), day).id).toBe('too_few_leaves');
  });
  it('10 leaves still go through the rules', () => {
    expect(decide(summarisePlot(Array.from({ length: 10 }, () => leaf('healthy'))), day).id).toBe('healthy_all');
    const rust = [...Array.from({ length: 3 }, () => leaf('rust')), ...Array.from({ length: 7 }, () => leaf('healthy'))];
    expect(decide(summarisePlot(rust), day).id).toBe('rust_high_pre_rains');
  });
  it('the healthy card does not state a leaf count', () => {
    const c = getAnswer('healthy_all');
    for (const v of Object.values(c.notSure ?? {})) expect(v).not.toMatch(/\d/);
  });
});

describe('decideForWindow', () => {
  it('rust 3+ follows the season', () => {
    const s = summary({ dominant: 'rust', affected: 3, distinctProblems: 1 });
    expect(decideForWindow(s, 'pre_short_rains').id).toBe('rust_high_pre_rains');
    expect(decideForWindow(s, 'pre_long_rains').id).toBe('rust_high_pre_rains');
    expect(decideForWindow(s, 'short_rains').id).toBe('rust_high_in_rains');
    expect(decideForWindow(s, 'long_rains').id).toBe('rust_high_in_rains');
    expect(decideForWindow(s, 'dry').id).toBe('rust_high_dry');
  });
  it('first match wins: unsure before everything', () => {
    const s = summary({ dominant: 'rust', affected: 5, uncertain: 3, distinctProblems: 2 });
    expect(decideForWindow(s, 'pre_short_rains').id).toBe('too_many_unsure');
  });
  it('healthy and none', () => {
    expect(decideForWindow(summary({ dominant: 'healthy' }), 'dry').id).toBe('healthy_all');
    expect(decideForWindow(summary({ dominant: 'none' }), 'dry').id).toBe('ask_officer');
  });
  it('not_leaf majority', () => {
    expect(decideForWindow(summary({ dominant: 'not_leaf', uncertain: 2 }), 'dry').id).toBe('not_a_leaf');
  });
  it('is pure: same input, same output', () => {
    const s = summary({ dominant: 'phoma', affected: 2, distinctProblems: 1 });
    expect(decideForWindow(s, 'dry')).toEqual(decideForWindow(s, 'dry'));
  });
});

describe('decide', () => {
  it('uses the season window of the date', () => {
    const s = summary({ dominant: 'rust', affected: 6, distinctProblems: 1 });
    expect(decide(s, new Date(2026, 9, 4, 12)).id).toBe('rust_high_pre_rains');
    expect(decide(s, new Date(2026, 11, 1, 12)).id).toBe('rust_high_in_rains');
    expect(decide(s, new Date(2027, 0, 10, 12)).id).toBe('rust_high_dry');
  });
  it('does not read the clock', () => {
    const now = vi.spyOn(Date, 'now');
    decide(summary({ dominant: 'healthy' }), new Date(2026, 9, 4, 12));
    expect(now).not.toHaveBeenCalled();
    now.mockRestore();
  });
});

// Safety invariants mirrored from app/qa/checks/decision_matrix.py.
function* reachableSummaries(): Generator<[PlotSummary, SeasonWindow]> {
  for (const dominant of [...LABELS, 'none'] as (Label | 'none')[])
    for (let affected = 0; affected <= 10; affected++)
      for (let uncertain = 0; uncertain + affected <= 10; uncertain++)
        for (const distinct of [1, 2, 3]) {
          const noDisease = dominant === 'healthy' || dominant === 'none';
          if (noDisease ? affected > 0 : affected === 0) continue;
          if (distinct > Math.max(1, affected)) continue;
          for (const window of WINDOWS) yield [summary({ dominant, affected, uncertain, distinctProblems: distinct }), window];
        }
}

describe('safety invariants over every reachable summary', () => {
  it('hold for all summaries', () => {
    const sev = (id: string) => answerById(id)?.severity ?? 'missing';
    const bad: string[] = [];
    let seen = 0;
    for (const [s, window] of reachableSummaries()) {
      seen++;
      const card = decideForWindow(s, window);
      const cs = sev(card.id);
      const key = `${s.dominant} a=${s.affected} u=${s.uncertain} d=${s.distinctProblems} ${window} -> ${card.id}`;
      if (cs === 'missing') bad.push('missing ' + key);
      if (s.uncertain >= 3 && cs !== 'ask') bad.push('unsure>=3 not ask ' + key);
      if (s.dominant === 'not_leaf' && card.id !== 'not_a_leaf' && cs !== 'ask') bad.push('not_leaf ' + key);
      if (s.distinctProblems >= 2 && card.id !== 'mixed_problems' && cs !== 'ask') bad.push('mixed ' + key);
      if (s.affected <= 1 && cs === 'act') bad.push('act on <=1 ' + key);
      if (card.id === 'healthy_all' && s.affected > 0) bad.push('healthy_all affected ' + key);
    }
    expect(seen).toBe(3510);
    expect(bad).toEqual([]);
  });
});

describe('decide is fail-safe on bad input', () => {
  const day = new Date(2026, 9, 4);
  const ok = summary({ dominant: 'healthy' });
  ok.counts = { ...ok.counts, healthy: 10 };
  const cases: [string, unknown, unknown][] = [
    ['null summary', null, day],
    ['undefined summary', undefined, day],
    ['empty object', {}, day],
    ['string summary', 'rust', day],
    ['unknown dominant', { ...ok, dominant: 'banana' }, day],
    ['NaN affected', { ...ok, affected: NaN }, day],
    ['negative uncertain', { ...ok, uncertain: -1 }, day],
    ['string counts', { ...ok, affected: '3', uncertain: '0' }, day],
    ['Infinity n', { ...ok, n: Infinity }, day],
    ['fractional n', { ...ok, n: 9.5 }, day],
    ['missing counts', { ...ok, counts: undefined }, day],
    ['negative count', { ...ok, counts: { ...ok.counts, rust: -1 } }, day],
    ['affected + uncertain above n', { ...ok, affected: 8, uncertain: 5 }, day],
    ['counts above n', { ...ok, counts: { ...ok.counts, healthy: 11 } }, day],
    ['distinct problems above 4', { ...ok, distinctProblems: 5 }, day],
    ['invalid date', ok, new Date('not a date')],
    ['date is a string', ok, '2026-10-04'],
    ['date is null', ok, null],
  ];
  it('the well-formed baseline gives healthy_all', () => {
    expect(decide(ok, day).id).toBe('healthy_all');
  });
  it.each(cases)('%s gives ask_officer without throwing', (_name, s, d) => {
    let id = '';
    expect(() => {
      id = decide(s as PlotSummary, d as Date).id;
    }).not.toThrow();
    expect(id).toBe('ask_officer');
  });
  it('decideForWindow rejects bad summaries and unknown windows', () => {
    expect(decideForWindow(null as unknown as PlotSummary, 'dry').id).toBe('ask_officer');
    expect(decideForWindow(ok, 'monsoon' as SeasonWindow).id).toBe('ask_officer');
  });
});
