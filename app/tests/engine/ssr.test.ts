// @vitest-environment node
// The engine must import and run its pure functions on the server (TanStack Start SSR):
// no window, document, navigator, indexedDB or Audio at import time.
import { describe, expect, it } from 'vitest';
import type { Check, Label, LeafResult } from '../../src/engine/types';

const q = { ok: true, blur: 100, brightness: 0.5 };
const leaf = (label: LeafResult['label'], confidence = 0.9): LeafResult => ({
  label,
  probs: { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
  confidence,
  quality: q,
  abstained: label === 'unsure',
  modelVersion: 'test',
});

describe('SSR safety (no window)', () => {
  it('runs in an environment without browser globals', () => {
    expect(typeof window).toBe('undefined');
    expect(typeof document).toBe('undefined');
    expect(typeof indexedDB).toBe('undefined');
  });

  it('imports src/engine/index.ts without throwing', async () => {
    const engine = await import('../../src/engine/index');
    for (const fn of ['loadModel', 'classifyLeaf', 'decide', 'summarisePlot', 'seasonWindow', 'buildReferral', 'parseReferral', 'saveCheck', 'play', 'syncPending']) {
      expect(typeof (engine as Record<string, unknown>)[fn]).toBe('function');
    }
  });

  it('summarisePlot, seasonWindow, decide, buildReferral and parseReferral work with no window', async () => {
    const { summarisePlot, seasonWindow, decide, buildReferral, parseReferral } = await import('../../src/engine/index');
    const date = new Date(2026, 9, 4, 9, 0); // 4 October, local time
    const labels: Label[] = ['rust', 'rust', 'rust', 'rust', 'rust', 'rust', 'healthy', 'healthy', 'healthy'];
    const leaves = [...labels.map((l) => leaf(l)), leaf('unsure', 0.3)];
    const summary = summarisePlot(leaves);
    expect(summary).toMatchObject({ n: 10, affected: 6, uncertain: 1, dominant: 'rust' });
    expect(seasonWindow(date)).toBe('pre_short_rains');
    const card = decide(summary, date);
    expect(card.id).toBe('rust_high_pre_rains');
    const check: Check = {
      id: 'ssr',
      createdAt: date.toISOString(),
      lang: 'sw',
      leaves,
      summary,
      window: seasonWindow(date),
      answerId: card.id,
      decision: 'act',
      memberId: 'OCC0412',
      plotId: '2',
      consentMain: false,
      consentPhotos: false,
      synced: false,
    };
    const sms = buildReferral(check);
    const parsed = parseReferral(sms);
    expect(parsed).toMatchObject({ member_id: 'OCC0412', check_date: '2026-10-04', answer_id: 'rust_high_pre_rains', decision: 'act' });
  });
});
