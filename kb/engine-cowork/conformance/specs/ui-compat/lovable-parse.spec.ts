// UI compatibility: can the Lovable officer dashboard read what the engine sends?
// Runs the dashboard's own parser (src/lib/parseReferral.ts, fetched read-only into targets/lovable-ui)
// on the engine's buildReferral output. A failure here is a UI-side finding, not an engine failure,
// so this file runs separately: npm run test:ui-compat (ENGINE_DIR as usual).
import { existsSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import * as engine from '@engine';
import { leaves, LOVABLE_UI_DIR, makeCheck, normaliseParsed } from '../helpers';

const e = engine as any;
const build = (c: any) => e.buildReferral(c, c.memberId) as string;
const check = (over: any = {}) => {
  const c = makeCheck(over);
  c.summary = over.summary ?? e.summarisePlot(c.leaves);
  return c;
};
const referralSmsPath = path.join(LOVABLE_UI_DIR, 'src/lib/referralSms.ts');

const lovableParserPath = path.join(LOVABLE_UI_DIR, 'src/lib/parseReferral.ts');
const uiParse: ((t: string) => any) | null = existsSync(lovableParserPath)
  ? (await import(/* @vite-ignore */ lovableParserPath)).parseReferral
  : null;
describe.runIf(!!uiParse)('Lovable officer dashboard parser (src/lib/parseReferral.ts) reads the engine output', () => {
  it('passes its own unit-test example (P:P07)', () => {
    expect(uiParse!('JANI1 M:OCC0412 P:P07 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask')?.counts.healthy).toBe(2);
  });


  it('reads the CONTRACTS example verbatim (P:2)', () => {
    expect(uiParse!('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask')).not.toBeNull();
  });

  it('reads an engine referral with plot P07 and keeps every field', () => {
    const c = check({ plotId: 'P07' });
    const sms = build(c);
    const p = normaliseParsed(uiParse!(sms));
    expect(p, sms).toBeTruthy();
    expect(p).toMatchObject({ memberId: 'OCC0412', plotId: 'P07', date: '20261004', n: 10, rust: 6, miner: 1, uncertain: 1, answerId: 'rust_high_pre_rains', decision: 'ask' });
  });

  it('reads an engine referral with a numeric plot as in CONTRACTS (plot 2)', () => {
    const sms = build(check({ plotId: '2' }));
    expect(uiParse!(sms), sms).not.toBeNull();
  });

  it('reads an engine referral with no photos (N:0)', () => {
    const sms = build(check({ leaves: [], answerId: 'ask_officer' }));
    expect(uiParse!(sms), sms).not.toBeNull();
  });

  it('reads an engine referral with no member or plot', () => {
    const sms = build(check({ memberId: undefined, plotId: undefined }));
    expect(uiParse!(sms), sms).not.toBeNull();
  });

  it('keeps not_leaf leaves out of the healthy count', () => {
    const c = check({ leaves: leaves({ not_leaf: 2, unsure: 1, rust: 3, healthy: 4 }), plotId: 'P07' });
    const p = uiParse!(build(c));
    expect(p?.counts?.healthy).toBe(4);
  });
});

describe.runIf(!!uiParse && existsSync(referralSmsPath))('Lovable farmer app SMS (src/lib/referralSms.ts) against its own officer parser and the engine', async () => {
  const mod = await import(/* @vite-ignore */ referralSmsPath);
  const ls = leaves({ rust: 6, miner: 1, unsure: 1, healthy: 2 });
  const summary = e.summarisePlot(ls);
  const ui = (over: any = {}) => mod.referralSms({
    memberId: 'OCC0412', plotId: 'P07', date: new Date(2026, 9, 4, 12), summary,
    answer: { id: 'rust_high_pre_rains' }, confidence: mod.meanAcceptedConfidence ? mod.meanAcceptedConfidence(ls) : 87,
    decision: 'ask', ...over,
  }) as string;
  it('the SMS the farmer app sends today can be read by the officer dashboard', () => {
    expect(uiParse!(ui()), ui()).not.toBeNull();
  });
  it('the farmer app SMS and engine buildReferral agree on every field except Q', () => {
    const strip = (t: string) => t.replace(/ Q:\d+/, '');
    expect(strip(ui()), 'UI and engine SMS bodies differ').toBe(strip(build(check({ leaves: ls, plotId: 'P07' }))));
  });
  it('an empty member or plot field still gives an SMS the dashboard reads', () => {
    expect(uiParse!(ui({ memberId: '', plotId: '' })), ui({ memberId: '', plotId: '' })).not.toBeNull();
  });
});
