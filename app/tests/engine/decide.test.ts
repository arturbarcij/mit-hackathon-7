import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { summarisePlot } from '../../src/engine/plot.ts';
import type { Label, LeafResult, PlotSummary } from '../../src/engine/types.ts';

const contentDir = join(dirname(fileURLToPath(import.meta.url)), '../../src/content');
const ready = existsSync(join(contentDir, 'rules.json')) && existsSync(join(contentDir, 'answers.json'));

function leaf(label: Label | 'unsure'): LeafResult {
  const probs = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
  if (label !== 'unsure') probs[label] = 0.9;
  return {
    label,
    probs,
    confidence: 0.9,
    quality: label === 'unsure'
      ? { ok: false, reason: 'blurry', blur: 1, brightness: 128 }
      : { ok: true, blur: 100, brightness: 128 },
    abstained: label === 'unsure',
    modelVersion: 'mock',
  };
}

function counts(partial: Partial<PlotSummary['counts']> = {}): PlotSummary['counts'] {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0, ...partial };
}

if (!ready) {
  describe('decide', () => {
    it.skip('src/content/rules.json or answers.json is not written yet', () => {});
  });
} else {
  const { decide } = await import('../../src/engine/decide.ts');

  describe('decide', () => {
    it('maps 6 rust of 10 on 2026-10-04 to rust_high_pre_rains', () => {
      const summary = summarisePlot([
        ...Array.from({ length: 6 }, () => leaf('rust')),
        ...Array.from({ length: 4 }, () => leaf('healthy')),
      ]);
      expect(summary.n).toBe(10);
      expect(summary.counts.rust).toBe(6);
      expect(summary.affected).toBe(6);
      expect(summary.dominant).toBe('rust');
      const card = decide(summary, new Date(Date.UTC(2026, 9, 4)));
      expect(card.id).toBe('rust_high_pre_rains');
      expect(card.severity).toBe('act');
      expect(card.audio.en).toBe('/audio/en/rust_high_pre_rains.mp3');
      expect(card.audio.sw).toBe('/audio/sw/rust_high_pre_rains.mp3');
      expect(card.audio.kik).toBeUndefined();
      expect(card.text.en).toBeTruthy();
      expect(card.assumption).toBe(true);
    });

    it('maps 4 uncertain leaves to too_many_unsure', () => {
      const summary = summarisePlot(Array.from({ length: 4 }, () => leaf('unsure')));
      expect(summary.uncertain).toBe(4);
      const card = decide(summary, new Date(Date.UTC(2026, 9, 4)));
      expect(card.id).toBe('too_many_unsure');
    });

    it('maps an empty plot to ask_officer', () => {
      const summary: PlotSummary = {
        n: 0,
        counts: counts(),
        uncertain: 0,
        dominant: 'none',
        affected: 0,
        distinctProblems: 0,
      };
      expect(decide(summary, new Date(Date.UTC(2026, 9, 4))).id).toBe('ask_officer');
      expect(decide(summarisePlot([]), new Date(Date.UTC(2026, 9, 4))).id).toBe('ask_officer');
    });

    it('maps an all-healthy plot to healthy_all', () => {
      const summary = summarisePlot(Array.from({ length: 10 }, () => leaf('healthy')));
      expect(summary.dominant).toBe('healthy');
      expect(summary.affected).toBe(0);
      const card = decide(summary, new Date(Date.UTC(2026, 9, 4)));
      expect(card.id).toBe('healthy_all');
      expect(card.severity).toBe('ok');
    });
  });
}
