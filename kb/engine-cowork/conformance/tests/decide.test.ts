// decide(summary, date) conformance: rules.json in order, first match wins, real answers.json cards.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { need } from './engine-under-test';
import {
  abstractSummary, answerIds, answersById, DATE_IN_WINDOW, DISEASES, LABELS, leavesFrom, rules, WINDOWS,
} from './fixtures';
import type { AnswerCard, Label, PlotSummary, SeasonWindow } from '../reference/types';

const here = path.dirname(fileURLToPath(import.meta.url));
const golden = JSON.parse(readFileSync(path.resolve(here, '../golden.json'), 'utf8')) as {
  meta: { count: number; key: string };
  rows: Record<string, string>;
};

const N = 10;

/** Same enumeration as app/qa/checks/decision_matrix.py (and scripts/golden_matrix.py). */
function* enumerateAbstract(): Generator<{ dominant: Label | 'none'; affected: number; uncertain: number; distinct: number; window: SeasonWindow }> {
  const doms: (Label | 'none')[] = [...LABELS, 'none'];
  for (const dominant of doms)
    for (let affected = 0; affected <= N; affected++)
      for (let uncertain = 0; uncertain <= N; uncertain++)
        for (const distinct of [1, 2, 3])
          for (const window of WINDOWS) {
            if (affected + uncertain > N) continue;
            if ((dominant === 'healthy' || dominant === 'none') && affected > 0) continue;
            if (!(dominant === 'healthy' || dominant === 'none') && affected === 0) continue;
            if (distinct > Math.max(1, affected)) continue;
            yield { dominant, affected, uncertain, distinct, window };
          }
}

/** Every real 10-leaf plot as a count vector over 7 outcomes (8008 compositions). */
function* enumerateRealPlots(): Generator<Partial<Record<Label | 'unsure', number>>> {
  const keys: (Label | 'unsure')[] = [...LABELS, 'unsure'];
  const rec = function* (i: number, left: number, acc: number[]): Generator<number[]> {
    if (i === keys.length - 1) { yield [...acc, left]; return; }
    for (let k = 0; k <= left; k++) yield* rec(i + 1, left - k, [...acc, k]);
  };
  for (const v of rec(0, N, [])) {
    const out: Partial<Record<Label | 'unsure', number>> = {};
    keys.forEach((k, i) => { if (v[i] > 0) out[k] = v[i]; });
    yield out;
  }
}

function expectWellFormedCard(card: AnswerCard) {
  expect(card).toBeTypeOf('object');
  expect(answerIds.has(card.id), `answer id '${card.id}' is not in answers.json`).toBe(true);
  const src = answersById.get(card.id)!;
  expect(card.severity).toBe(src.severity);
  expect(['ok', 'watch', 'act', 'ask']).toContain(card.severity);
  // text per language must be the answers.json text, not composed
  for (const lang of ['en', 'sw', 'kik'] as const) {
    if (src.text[lang]) {
      expect(card.text[lang], `${card.id}.text.${lang}`).toBe(src.text[lang]);
      expect(card.audio[lang], `${card.id}.audio.${lang}`).toBe(`/audio/${lang}/${card.id}.mp3`);
    } else {
      expect(card.text[lang], `${card.id}.text.${lang} should be absent`).toBeUndefined();
      expect(card.audio[lang], `${card.id}.audio.${lang} should be absent`).toBeUndefined();
    }
  }
  if (src.not_sure) expect(card.notSure).toEqual(src.not_sure);
  else expect(card.notSure).toBeUndefined();
  expect(card.sources).toEqual(src.sources ?? []);
  expect(card.assumption).toBe(src.assumption === true);
}

describe('decide', () => {
  const decide = need('decide');
  const summarisePlot = need('summarisePlot');

  const run = (counts: Partial<Record<Label | 'unsure', number>>, window: SeasonWindow = 'pre_short_rains') =>
    decide(summarisePlot(leavesFrom(counts)), DATE_IN_WINDOW[window]);

  describe('scenario expectations', () => {
    it('6 rust + 4 healthy on Sun 4 Oct 2026 -> rust_high_pre_rains (act)', () => {
      const card = decide(summarisePlot(leavesFrom({ rust: 6, healthy: 4 })), new Date(2026, 9, 4));
      expect(card.id).toBe('rust_high_pre_rains');
      expect(card.severity).toBe('act');
      expectWellFormedCard(card);
    });
    it('3 unsure -> too_many_unsure, whatever else is on the plot', () => {
      expect(run({ unsure: 3, rust: 7 }).id).toBe('too_many_unsure');
      expect(run({ unsure: 3, healthy: 7 }).id).toBe('too_many_unsure');
      expect(run({ unsure: 10 }).id).toBe('too_many_unsure');
    });
    it('unsure + not_leaf add up to the uncertain threshold', () => {
      expect(run({ unsure: 2, not_leaf: 1, healthy: 7 }).id).toBe('too_many_unsure');
      expect(run({ not_leaf: 3, healthy: 7 }).id).toBe('too_many_unsure');
    });
    it('2 unsure is still a verdict (not too_many_unsure)', () => {
      expect(run({ unsure: 2, healthy: 8 }).id).toBe('healthy_all');
      expect(run({ unsure: 2, rust: 8 }).id).toBe('rust_high_pre_rains');
    });
    it('two problem types -> mixed_problems', () => {
      expect(run({ rust: 5, phoma: 1, healthy: 4 }).id).toBe('mixed_problems');
      expect(run({ cercospora: 1, miner: 1, healthy: 8 }).id).toBe('mixed_problems');
    });
    it('all healthy -> healthy_all', () => {
      expect(run({ healthy: 10 }).id).toBe('healthy_all');
      expect(run({ healthy: 5 }).id).toBe('healthy_all');
    });
    it('not_leaf majority -> not_a_leaf (when fewer than 3 uncertain is impossible, too_many_unsure wins by rule order)', () => {
      // With n = 10 a not_leaf majority means at least 6 uncertain, so the first rule
      // (uncertain_gte 3) wins. not_a_leaf is reachable for small plots only.
      expect(run({ not_leaf: 6, rust: 4 }).id).toBe('too_many_unsure');
      expect(run({ not_leaf: 2, healthy: 1 }).id).toBe('not_a_leaf');
      expect(run({ not_leaf: 1 }).id).toBe('not_a_leaf');
    });
    it('rust thresholds by window', () => {
      expect(run({ rust: 3, healthy: 7 }, 'pre_short_rains').id).toBe('rust_high_pre_rains');
      expect(run({ rust: 3, healthy: 7 }, 'pre_long_rains').id).toBe('rust_high_pre_rains');
      expect(run({ rust: 3, healthy: 7 }, 'short_rains').id).toBe('rust_high_in_rains');
      expect(run({ rust: 3, healthy: 7 }, 'long_rains').id).toBe('rust_high_in_rains');
      expect(run({ rust: 3, healthy: 7 }, 'dry').id).toBe('rust_high_dry');
      for (const w of WINDOWS) {
        expect(run({ rust: 2, healthy: 8 }, w).id).toBe('rust_low');
        expect(run({ rust: 1, healthy: 9 }, w).id).toBe('rust_low');
      }
    });
    it('single other disease -> its own card in every window', () => {
      for (const w of WINDOWS) {
        expect(run({ cercospora: 1, healthy: 9 }, w).id).toBe('cercospora');
        expect(run({ phoma: 4, healthy: 6 }, w).id).toBe('phoma');
        expect(run({ miner: 9, healthy: 1 }, w).id).toBe('miner');
      }
    });
    it('empty plot -> catch-all ask_officer', () => {
      const card = decide(summarisePlot([]), new Date(2026, 9, 4));
      expect(card.id).toBe('ask_officer');
      expectWellFormedCard(card);
    });
    it('is pure: same input twice gives the same card', () => {
      const s = summarisePlot(leavesFrom({ rust: 6, healthy: 4 }));
      const d = new Date(2026, 9, 4);
      expect(decide(s, d)).toEqual(decide(s, d));
    });
  });

  describe('card shape', () => {
    it('every card returned for the scenario set is built from answers.json', () => {
      const cases: Partial<Record<Label | 'unsure', number>>[] = [
        { healthy: 10 }, { rust: 6, healthy: 4 }, { rust: 1, healthy: 9 }, { cercospora: 2, healthy: 8 },
        { phoma: 1, healthy: 9 }, { miner: 3, healthy: 7 }, { rust: 1, miner: 1, healthy: 8 }, { unsure: 3, healthy: 7 },
        { not_leaf: 1 }, {},
      ];
      for (const c of cases) for (const w of WINDOWS) expectWellFormedCard(run(c, w));
    });
  });

  describe('abstract matrix (same enumeration as decision_matrix.py)', () => {
    const results = new Map<string, string>();
    const catchAllKeys: string[] = [];
    beforeAll(() => {
      for (const a of enumerateAbstract()) {
        const key = `${a.dominant}|${a.affected}|${a.uncertain}|${a.distinct}|${a.window}`;
        const card = decide(abstractSummary(a.dominant, a.affected, a.uncertain, a.distinct), DATE_IN_WINDOW[a.window]);
        results.set(key, card?.id ?? String(card));
        if (card?.id === 'ask_officer') catchAllKeys.push(key);
      }
    });

    it('enumerates 3,510 summaries, the same count as decision_matrix.py', () => {
      expect(results.size).toBe(3510);
      expect(results.size).toBe(golden.meta.count);
    });

    it('every result is an answer id that exists in answers.json', () => {
      const bad = [...results].filter(([, id]) => !answerIds.has(id)).map(([k, id]) => `${k} -> ${id}`);
      expect(bad.length, bad.slice(0, 10).join('\n')).toBe(0);
    });

    it('matches the Python golden table row by row', () => {
      const diffs: string[] = [];
      for (const [k, want] of Object.entries(golden.rows)) {
        const got = results.get(k);
        if (got !== want) diffs.push(`${k}: want ${want}, got ${got}`);
      }
      expect(diffs, diffs.slice(0, 20).join('\n')).toEqual([]);
      expect(results.size).toBe(Object.keys(golden.rows).length);
    });

    it('the catch-all is reached only for dominant none with fewer than 3 uncertain (15 abstract rows, none reachable from a real 10-leaf plot)', () => {
      expect(catchAllKeys.length).toBe(15);
      for (const k of catchAllKeys) {
        const [dominant, , uncertain] = k.split('|');
        expect(dominant).toBe('none');
        expect(Number(uncertain)).toBeLessThan(3);
      }
    });

    it('safety invariants from decision_matrix.py hold', () => {
      const violations: string[] = [];
      for (const [k, id] of results) {
        const [dominant, affected, uncertain, distinct] = k.split('|');
        const sev = answersById.get(id)?.severity ?? 'missing';
        if (Number(uncertain) >= 3 && sev !== 'ask') violations.push(`unsure>=3 not ask: ${k} -> ${id}`);
        else if (dominant === 'not_leaf' && id !== 'not_a_leaf' && sev !== 'ask') violations.push(`not_leaf not handled: ${k} -> ${id}`);
        else if (Number(distinct) >= 2 && id !== 'mixed_problems' && sev !== 'ask') violations.push(`mixed not handled: ${k} -> ${id}`);
        else if (Number(affected) <= 1 && sev === 'act') violations.push(`act on <=1 leaf: ${k} -> ${id}`);
        else if (id === 'healthy_all' && Number(affected) > 0) violations.push(`healthy_all with affected: ${k}`);
      }
      expect(violations.length, violations.slice(0, 10).join('\n')).toBe(0);
    });
  });

  describe('every real 10-leaf plot (8,008 count vectors) x 5 windows', () => {
    const seen = new Map<string, number>();
    const violations: string[] = [];
    let total = 0;
    beforeAll(() => {
      for (const counts of enumerateRealPlots()) {
        const s: PlotSummary = summarisePlot(leavesFrom(counts));
        for (const w of WINDOWS) {
          const card = decide(s, DATE_IN_WINDOW[w]);
          total++;
          const id = card?.id ?? String(card);
          seen.set(id, (seen.get(id) ?? 0) + 1);
          const tag = `${JSON.stringify(counts)} ${w} -> ${id}`;
          if (!answerIds.has(id)) { violations.push(`not an answer id: ${tag}`); continue; }
          const sev = answersById.get(id)!.severity;
          // Invariants are stated on the REAL plot (recomputed here), so a wrong summarisePlot shows up too.
          const unsure = counts.unsure ?? 0, notLeaf = counts.not_leaf ?? 0;
          const affected = DISEASES.reduce((a, d) => a + (counts[d] ?? 0), 0);
          const distinct = DISEASES.filter((d) => (counts[d] ?? 0) > 0).length;
          if (unsure + notLeaf >= 3 && id !== 'too_many_unsure') violations.push(`uncertain>=3 not too_many_unsure: ${tag}`);
          if (affected <= 1 && sev === 'act') violations.push(`act on <=1 leaf: ${tag}`);
          if (id === 'healthy_all' && affected > 0) violations.push(`healthy_all with affected: ${tag}`);
          if (distinct >= 2 && unsure + notLeaf < 3 && id !== 'mixed_problems') violations.push(`two problems not mixed_problems: ${tag}`);
        }
      }
    });
    it('covers 8,008 x 5 = 40,040 decisions', () => expect(total).toBe(40040));
    it('every decision is an answer id and respects the safety invariants', () => {
      expect(violations.length, `${violations.length} violations, first 10:\n${violations.slice(0, 10).join('\n')}`).toBe(0);
    });
    it('never reaches the catch-all for a real 10-leaf plot', () => expect(seen.get('ask_officer') ?? 0).toBe(0));
    it('never reaches not_a_leaf for a real 10-leaf plot (too_many_unsure wins first)', () => expect(seen.get('not_a_leaf') ?? 0).toBe(0));
    it('reaches every other result card named in rules.json', () => {
      const targets = new Set(rules.map((r) => r.then).filter((t) => t !== 'ask_officer' && t !== 'not_a_leaf'));
      for (const t of targets) expect(seen.get(t) ?? 0, t).toBeGreaterThan(0);
    });
  });
});
