export type Lang = "sw" | "kik" | "en";
export type Label = "healthy" | "rust" | "cercospora" | "phoma" | "miner" | "not_leaf";

export interface QualityResult {
  ok: boolean;
  reason?: "blurry" | "dark" | "too_small";
  blur: number;
  brightness: number;
}

export interface LeafResult {
  label: Label | "unsure";
  probs: Record<Label, number>;
  confidence: number;
  quality: QualityResult;
  abstained: boolean;
  modelVersion: string;
}

export interface PlotSummary {
  n: number;
  counts: Record<Label, number>;
  uncertain: number;
  dominant: Label | "none";
  affected: number;
  distinctProblems: number;
}

export type SeasonWindow = "pre_short_rains" | "short_rains" | "pre_long_rains" | "long_rains" | "dry";

export interface AnswerCard {
  id: string;
  severity: "ok" | "watch" | "act" | "ask";
  text: Partial<Record<Lang, string>>;
  notSure?: Partial<Record<Lang, string>>;
  audio: Partial<Record<Lang, string>>;
  sources: string[];
  assumption: boolean;
  /** Per-language review status from answers.json, e.g. { kik: "machine_draft_pending_native_review" }. */
  reviewStatus?: Partial<Record<Lang, string>>;
}

export type Decision = "act" | "wait" | "ask";

export interface ReferralCheck {
  summary: PlotSummary;
  answer: AnswerCard;
  decision: Decision;
  date: Date;
}

/** Input for the JANI1 referral SMS (kb/CONTRACTS.md). */
export interface ReferralInput {
  memberId: string;
  plotId: string;
  date: Date;
  summary: PlotSummary;
  answerId: string;
  /** Mean calibrated confidence of accepted leaves, 0 to 1. */
  confidence: number;
  decision: Decision;
}

export interface SeasonClock {
  window: SeasonWindow;
  /** True when today is inside a pre-rains spray window (pre_short_rains or pre_long_rains). */
  sprayWindowOpen: boolean;
  /** The current spray window if open, otherwise the next one. */
  sprayWindow: { name: "pre_short_rains" | "pre_long_rains"; start: Date; end: Date };
  /** Days until the current spray window closes (open) or opens (closed). */
  days: number;
  /** Days until the next rainy window starts (short_rains or long_rains). */
  daysToRains: number;
  nextRains: { name: "short_rains" | "long_rains"; start: Date };
}
