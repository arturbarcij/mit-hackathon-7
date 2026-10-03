import { describe, expect, it } from 'vitest';
import {
  answerById,
  bundledAnswerIds,
  bundledRuleTargets,
  decide,
  decideWith,
  FALLBACK_ID,
  normaliseAnswers,
  normaliseRules,
  ruleMatches,
} from '../../src/engine/decide';
import { loadContent } from '../../src/engine/content';
import { normaliseSeason, seasonWindow, seasonWindowFrom, SEASON_WINDOWS } from '../../src/engine/season';
import type { Label, PlotSummary, SeasonWindow } from '../../src/engine/types';
import { summarisePlot } from '../../src/engine/plot';
import { leaves } from './helpers';

function summary(over: Partial<PlotSummary>): PlotSummary {
  return {
    n: 10,
    counts: { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
    uncertain: 0,
    dominant: 'none',
    affected: 0,
    distinctProblems: 0,
    ...over,
  };
}

const REQUIRED_IDS = [
  'how_to_pick_leaves', 'how_to_photograph', 'retake_blurry', 'retake_dark', 'not_a_leaf',
  'healthy_all', 'rust_low', 'rust_high_pre_rains', 'rust_high_in_rains', 'rust_high_dry',
  'cercospora', 'phoma', 'miner', 'mixed_problems', 'too_many_unsure', 'ask_officer',
  'berries_out_of_scope', 'other_crop',
  'consent_main', 'consent_photos', 'decision_act', 'decision_wait', 'decision_ask', 'referral_ready', 'language_name',
];

describe('content bundle', () => {
  it('has every required answer id', () => {
    const ids = new Set(bundledAnswerIds());
    for (const id of REQUIRED_IDS) expect(ids.has(id), id).toBe(true);
  });

  it('has a catch-all ask_officer rule last', () => {
    const rules = normaliseRules(loadContent().rules);
    const last = rules[rules.length - 1];
    expect(last.then).toBe(FALLBACK_ID);
    expect(Object.keys(last.if)).toHaveLength(0);
  });

  it('every rule points at an answer that exists', () => {
    for (const id of bundledRuleTargets()) expect(answerById(id), id).toBeDefined();
  });

  it('every answer has text in at least one language and an audio path per language', () => {
    for (const id of bundledAnswerIds()) {
      const card = answerById(id)!;
      const langs = Object.keys(card.text);
      expect(langs.length, id).toBeGreaterThan(0);
      for (const l of langs) expect(card.audio[l as 'sw'], `${id} ${l}`).toBe(`/audio/${l}/${id}.mp3`);
    }
  });
});

describe('decide', () => {
  const dominants: (Label | 'none')[] = ['none', 'healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];
  const dates = [new Date(2026, 0, 10), new Date(2026, 3, 10), new Date(2026, 6, 10), new Date(2026, 9, 4), new Date(2026, 10, 20)];

  it('returns a card from the bank for every combination in the rule inputs', () => {
    const bank = new Set(bundledAnswerIds());
    let combos = 0;
    for (const dominant of dominants)
      for (const affected of [0, 1, 2, 3, 5, 10])
        for (const uncertain of [0, 1, 2, 3, 6])
          for (const distinctProblems of [0, 1, 2, 3, 4])
            for (const date of dates) {
              const card = decide(summary({ dominant, affected, uncertain, distinctProblems }), date);
              expect(bank.has(card.id)).toBe(true);
              expect(card.text.en ?? card.text.sw).toBeTruthy();
              combos++;
            }
    expect(combos).toBeGreaterThan(1000);
  });

  it('reaches every rule target through some input', () => {
    const reached = new Set<string>();
    for (const dominant of dominants)
      for (const affected of [0, 1, 3, 10])
        for (const uncertain of [0, 3])
          for (const distinctProblems of [0, 1, 2])
            for (const date of dates)
              reached.add(decide(summary({ dominant, affected, uncertain, distinctProblems }), date).id);
    for (const id of bundledRuleTargets()) expect(reached.has(id), id).toBe(true);
  });

  it('is deterministic', () => {
    const s = summarisePlot(leaves({ rust: 6, healthy: 3, unsure: 1 }));
    const d = new Date(2026, 9, 4);
    expect(decide(s, d)).toEqual(decide(s, d));
  });

  it('answers rust before the short rains with the pre-rains card (placeholder or real rules)', () => {
    const s = summarisePlot(leaves({ rust: 6, healthy: 4 }));
    expect(decide(s, new Date(2026, 9, 4)).id).toBe('rust_high_pre_rains');
  });

  it('asks the officer when there are no leaves', () => {
    expect(decide(summarisePlot([]), new Date()).id).toBe(FALLBACK_ID);
  });

  it('asks the officer when too many leaves are unsure', () => {
    expect(decide(summarisePlot(leaves({ healthy: 6, unsure: 4 })), new Date(2026, 9, 4)).id).toBe('too_many_unsure');
  });

  it('asks the officer when the rule table has no match or points at a missing answer', () => {
    const answers = normaliseAnswers([{ id: 'ask_officer', severity: 'ask', text: { en: 'Ask' } }]);
    const s = summary({ dominant: 'rust', affected: 5 });
    const noMatch = decideWith(s, { rules: normaliseRules([{ if: { dominant: 'miner' }, then: 'miner' }]), answers, window: 'dry' });
    expect(noMatch.id).toBe(FALLBACK_ID);
    const missing = decideWith(s, { rules: normaliseRules([{ if: {}, then: 'does_not_exist' }]), answers, window: 'dry' });
    expect(missing.id).toBe(FALLBACK_ID);
  });

  it('never matches on an unknown condition key', () => {
    expect(ruleMatches({ colour: 'red' } as never, summary({}), 'dry')).toBe(false);
  });
});

describe('rule conditions', () => {
  const s = summary({ dominant: 'rust', affected: 4, uncertain: 1, distinctProblems: 1 });
  it('supports each key', () => {
    expect(ruleMatches({ dominant: 'rust' }, s, 'dry')).toBe(true);
    expect(ruleMatches({ dominant: ['miner', 'rust'] }, s, 'dry')).toBe(true);
    expect(ruleMatches({ dominant: 'miner' }, s, 'dry')).toBe(false);
    expect(ruleMatches({ affected_gte: 4 }, s, 'dry')).toBe(true);
    expect(ruleMatches({ affected_gte: 5 }, s, 'dry')).toBe(false);
    expect(ruleMatches({ affected_lte: 4 }, s, 'dry')).toBe(true);
    expect(ruleMatches({ uncertain_gte: 2 }, s, 'dry')).toBe(false);
    expect(ruleMatches({ uncertain_lte: 1 }, s, 'dry')).toBe(true);
    expect(ruleMatches({ distinct_problems_gte: 2 }, s, 'dry')).toBe(false);
    expect(ruleMatches({ window: 'dry' }, s, 'dry')).toBe(true);
    expect(ruleMatches({ window: ['short_rains', 'dry'] }, s, 'dry')).toBe(true);
    expect(ruleMatches({ window: 'long_rains' }, s, 'dry')).toBe(false);
  });
  it('rejects non-numeric thresholds', () => {
    expect(ruleMatches({ affected_gte: '1' as never }, s, 'dry')).toBe(false);
  });
  it('first match wins', () => {
    const rules = normaliseRules([
      { if: { dominant: 'rust' }, then: 'a' },
      { if: { dominant: 'rust' }, then: 'b' },
    ]);
    const answers = normaliseAnswers({ a: { severity: 'act', text: { en: 'A' } }, b: { severity: 'act', text: { en: 'B' } } });
    expect(decideWith(s, { rules, answers, window: 'dry' }).id).toBe('a');
  });
});

describe('answer bank shapes', () => {
  it('accepts an object keyed by id and snake_case not_sure', () => {
    const bank = normaliseAnswers({ x: { severity: 'watch', text: { en: 'Hello', sw: 'Habari' }, not_sure: { en: 'Unsure' }, sources: ['S1'], assumption: true } });
    const c = bank.get('x')!;
    expect(c.text.sw).toBe('Habari');
    expect(c.notSure?.en).toBe('Unsure');
    expect(c.sources).toEqual(['S1']);
    expect(c.assumption).toBe(true);
    expect(c.audio.sw).toBe('/audio/sw/x.mp3');
  });
  it('turns an invalid severity into ask', () => {
    expect(normaliseAnswers([{ id: 'y', severity: 'panic', text: { en: 'z' } }]).get('y')!.severity).toBe('ask');
  });
  it('accepts rules wrapped in an object', () => {
    expect(normaliseRules({ rules: [{ if: {}, then: 'ask_officer' }] })).toHaveLength(1);
  });
});

describe('season windows', () => {
  const ranges = normaliseSeason({
    windows: [
      { name: 'short_rains', start_month: 10, start_day: 15, end_month: 12, end_day: 15 },
      { name: 'dry', start_month: 12, start_day: 16, end_month: 2, end_day: 14 },
      { name: 'bogus', start_month: 1, start_day: 1, end_month: 12, end_day: 31 },
    ],
  });
  it('ignores unknown names and handles year wrap', () => {
    expect(ranges).toHaveLength(2);
    expect(seasonWindowFrom(ranges, new Date(2026, 10, 1))).toBe('short_rains');
    expect(seasonWindowFrom(ranges, new Date(2026, 0, 5))).toBe('dry');
    expect(seasonWindowFrom(ranges, new Date(2026, 11, 20))).toBe('dry');
  });
  it('treats uncovered dates as dry', () => {
    expect(seasonWindowFrom(ranges, new Date(2026, 5, 1))).toBe('dry');
    expect(seasonWindowFrom([], new Date())).toBe('dry');
  });
  it('bundled calendar returns a valid window for every day of the year', () => {
    for (let m = 0; m < 12; m++)
      for (let d = 1; d <= 28; d++) {
        const w: SeasonWindow = seasonWindow(new Date(2026, m, d));
        expect(SEASON_WINDOWS).toContain(w);
      }
  });
  it('4 October 2026 is before the short rains', () => {
    expect(seasonWindow(new Date(2026, 9, 4))).toBe('pre_short_rains');
  });
});
