// Thin adapter: Lovable's mock engine (src/engine/index.ts, fetched read-only at commit 492daba)
// exposed under the CONTRACTS signatures. It adapts only where a signature differs:
//   buildReferral(check: ReferralCheck) -> buildReferral(c: Check)
// It adds nothing that is missing: there is no seasonWindow and no parseReferral in the mock,
// and the suite records those as drift.
import * as mock from './src/engine/index';

export * from './src/engine/index';

export function buildReferral(c: any): string {
  const date = new Date(c.createdAt);
  return mock.buildReferral({ summary: c.summary, answer: mock.decide(c.summary, date), decision: c.decision ?? 'ask', date });
}
