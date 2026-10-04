import type { AnswerCard, Decision, LeafResult, PlotSummary } from "@/engine";

export const SMS_MAX = 160;

function clean(value: string): string {
  return value.trim().toUpperCase().replace(/[^A-Z0-9-]/g, "").slice(0, 12) || "?";
}

export function meanAcceptedConfidence(leaves: LeafResult[]): number {
  const accepted = leaves.filter((leaf) => leaf.label !== "unsure" && leaf.label !== "not_leaf");
  if (accepted.length === 0) return 0;
  return Math.round(accepted.reduce((sum, leaf) => sum + leaf.confidence, 0) / accepted.length * 100);
}

export function referralSms(o: { memberId: string; plotId: string; date: Date; summary: PlotSummary; answer: Pick<AnswerCard, "id">; confidence: number; decision: Decision }): string {
  const date = `${o.date.getFullYear()}${String(o.date.getMonth() + 1).padStart(2, "0")}${String(o.date.getDate()).padStart(2, "0")}`;
  const body = `JANI1 M:${clean(o.memberId)} P:${clean(o.plotId)} D:${date} N:${o.summary.n} R:${o.summary.counts.rust} C:${o.summary.counts.cercospora} H:${o.summary.counts.phoma} L:${o.summary.counts.miner} U:${o.summary.uncertain} A:${o.answer.id} Q:${Math.round(o.confidence)} X:${o.decision}`;
  return body.slice(0, SMS_MAX);
}
