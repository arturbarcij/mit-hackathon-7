// End-to-end engine flow without a browser: leaves -> summarisePlot -> decide -> saveCheck
// (consent) -> buildReferral -> parseReferral. LeafResults are built directly, as the mock
// or real model would return them, so no canvas or ONNX is needed.
import 'fake-indexeddb/auto';
import { IDBFactory } from 'fake-indexeddb';
import { beforeEach, describe, expect, it } from 'vitest';
import {
  buildReferral,
  decide,
  getPhotos,
  listChecks,
  parseReferral,
  queueForSync,
  saveCheck,
  savePhoto,
  seasonWindow,
  setConsent,
  summarisePlot,
  toReferralRow,
} from '../../src/engine/index';
import { _resetStorageForTests } from '../../src/engine/storage';
import { LABELS, type Check, type Decision, type Label, type LeafResult } from '../../src/engine/types';

const okQ = { ok: true, blur: 100, brightness: 0.5 };

function leaf(label: LeafResult['label'], confidence: number): LeafResult {
  const probs = Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
  if (label !== 'unsure') probs[label] = confidence;
  else probs.rust = confidence;
  return { label, probs, confidence, quality: okQ, abstained: label === 'unsure', modelVersion: 'mock' };
}

const many = (n: number, label: LeafResult['label'], conf: number) => Array.from({ length: n }, () => leaf(label, conf));

function makeCheck(id: string, leaves: LeafResult[], date: Date, consent: { main: boolean; photos: boolean }, decision?: Decision): Check {
  const summary = summarisePlot(leaves);
  return {
    id,
    createdAt: date.toISOString(),
    lang: 'sw',
    leaves,
    summary,
    window: seasonWindow(date),
    answerId: decide(summary, date).id,
    ...(decision ? { decision } : {}),
    memberId: 'OCC0412',
    plotId: '2',
    consentMain: consent.main,
    consentPhotos: consent.photos,
    synced: false,
  };
}

const OCT4 = new Date(2026, 9, 4, 9, 30); // local time, pre_short_rains
const photo = () => new Blob(['jpeg'], { type: 'image/jpeg' });

beforeEach(async () => {
  await _resetStorageForTests();
  globalThis.indexedDB = new IDBFactory();
});

describe('engine flow: ten leaves with consent', () => {
  const leaves = [...many(6, 'rust', 0.9), ...many(3, 'healthy', 0.8), leaf('unsure', 0.4)];

  it('summarises, decides, saves, builds and parses the referral', async () => {
    const summary = summarisePlot(leaves);
    expect(summary).toEqual({
      n: 10,
      counts: { healthy: 3, rust: 6, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
      uncertain: 1,
      dominant: 'rust',
      affected: 6,
      distinctProblems: 1,
    });
    const card = decide(summary, OCT4);
    expect(card).toMatchObject({ id: 'rust_high_pre_rains', severity: 'act' });

    await setConsent({ main: true, photos: false });
    const check = makeCheck('c1', leaves, OCT4, { main: true, photos: false }, 'ask');
    await saveCheck(check);
    await savePhoto(check.id, 0, photo());
    expect(await listChecks()).toEqual([check]);
    expect(await getPhotos(check.id)).toHaveLength(1);

    const sms = buildReferral(check);
    expect(sms).toBe('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:0 U:1 A:rust_high_pre_rains Q:87 X:ask');
    expect(sms.length).toBeLessThanOrEqual(160);

    const parsed = parseReferral(sms);
    expect(parsed).toEqual({
      member_id: 'OCC0412',
      plot_id: '2',
      check_date: '2026-10-04',
      counts: { healthy: 3, rust: 6, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
      uncertain: 1,
      answer_id: 'rust_high_pre_rains',
      confidence: 0.87,
      decision: 'ask',
      format: 'JANI1',
    });

    // SMS and the synced row agree on the fields the officer dashboard joins on.
    const row = toReferralRow(check);
    expect(row).toMatchObject({
      member_id: parsed!.member_id,
      plot_id: parsed!.plot_id,
      check_date: parsed!.check_date,
      uncertain: parsed!.uncertain,
      answer_id: parsed!.answer_id,
      decision: parsed!.decision,
    });
  });

  it('uses the same local date in SMS and row just after local midnight', () => {
    const justAfterMidnight = new Date(2026, 9, 4, 0, 30);
    const check = makeCheck('c2', leaves, justAfterMidnight, { main: true, photos: false }, 'wait');
    const parsed = parseReferral(buildReferral(check))!;
    expect(parsed.check_date).toBe('2026-10-04');
    expect(toReferralRow(check).check_date).toBe(parsed.check_date);
  });
});

describe('engine flow: ids', () => {
  it('normalises member and plot ids the same way in SMS and row', () => {
    const leaves = [...many(6, 'rust', 0.9), ...many(4, 'healthy', 0.8)];
    const check = { ...makeCheck('i1', leaves, OCT4, { main: true, photos: false }, 'ask'), memberId: 'occ 0412', plotId: 'p7' };
    const parsed = parseReferral(buildReferral(check))!;
    const row = toReferralRow(check);
    expect([parsed.member_id, parsed.plot_id]).toEqual(['OCC0412', 'P7']);
    expect([row.member_id, row.plot_id]).toEqual([parsed.member_id, parsed.plot_id]);
  });
});

describe('engine flow: abstention', () => {
  it('three unsure leaves go to a person (too_many_unsure, severity ask)', async () => {
    const leaves = [...many(7, 'healthy', 0.9), ...many(3, 'unsure', 0.4)];
    const summary = summarisePlot(leaves);
    expect(summary.uncertain).toBe(3);
    const card = decide(summary, OCT4);
    expect(card).toMatchObject({ id: 'too_many_unsure', severity: 'ask' });

    await setConsent({ main: true, photos: false });
    const check = makeCheck('u1', leaves, OCT4, { main: true, photos: false }, 'ask');
    await saveCheck(check);
    const parsed = parseReferral(buildReferral(check))!;
    expect(parsed).toMatchObject({ uncertain: 3, answer_id: 'too_many_unsure', decision: 'ask' });
    expect(parsed.counts.healthy).toBe(7);
  });

  it('U counts unsure plus not_leaf', () => {
    const leaves = [...many(7, 'healthy', 0.9), ...many(2, 'unsure', 0.4), leaf('not_leaf', 0.95)];
    const summary = summarisePlot(leaves);
    expect(summary.uncertain).toBe(3);
    expect(decide(summary, OCT4).id).toBe('too_many_unsure');
    const sms = buildReferral(makeCheck('u2', leaves, OCT4, { main: false, photos: false }, 'ask'));
    expect(sms).toContain(' U:3 ');
  });
});

describe('engine flow: no consent', () => {
  it('saveCheck, savePhoto and queueForSync store nothing; the SMS can still be built', async () => {
    const leaves = [...many(6, 'rust', 0.9), ...many(4, 'healthy', 0.8)];
    const check = makeCheck('n1', leaves, OCT4, { main: false, photos: false }, 'act');
    await saveCheck(check);
    await savePhoto(check.id, 0, photo());
    await queueForSync(check);
    expect(await listChecks()).toEqual([]);
    expect(await getPhotos(check.id)).toEqual([]);
    // The farmer can still send the referral herself; nothing is kept on the phone.
    expect(parseReferral(buildReferral(check))).toMatchObject({ member_id: 'OCC0412', decision: 'act' });
  });
});
