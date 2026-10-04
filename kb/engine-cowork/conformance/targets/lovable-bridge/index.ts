// What the Lovable UI actually computes in mock mode today (src/routes/index.tsx at e47a8a7):
// summarisePlot -> lib/mockBridge.summariseForRules, decide -> lib/mockBridge.applyRules,
// seasonWindow -> lib/mockBridge.seasonWindow, buildReferral -> lib/referralSms.referralSms,
// parseReferral -> lib/parseReferral.parseReferral, smsLink/play/loadModel -> src/engine (mock).
// Thin adapter only. Content: targets/lovable-ui/src/content holds the repo JSON wrapped in the
// { answers }, { rules }, { season } shape that Lovable's copy uses (see COMPAT.md, content shape).
import * as mock from '../lovable-mock/src/engine/index';
import { applyRules, seasonWindow as bridgeSeason, summariseForRules } from '../lovable-ui/src/lib/mockBridge';
import { meanAcceptedConfidence, referralSms } from '../lovable-ui/src/lib/referralSms';
import { parseReferral as uiParse } from '../lovable-ui/src/lib/parseReferral';

export const { loadModel, checkQuality, classifyLeaf, smsLink, play } = mock;
export const summarisePlot = summariseForRules;
export const decide = applyRules;
export const seasonWindow = bridgeSeason;
export const parseReferral = uiParse;
export function buildReferral(c: any): string {
  return referralSms({
    memberId: c.memberId ?? '', plotId: c.plotId ?? '', date: new Date(c.createdAt), summary: c.summary,
    answer: { id: c.answerId }, confidence: meanAcceptedConfidence(c.leaves ?? []), decision: c.decision,
  });
}
