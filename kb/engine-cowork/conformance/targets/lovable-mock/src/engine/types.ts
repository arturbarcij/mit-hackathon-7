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

export interface AnswerCard {
  id: string;
  severity: "ok" | "watch" | "act" | "ask";
  text: Partial<Record<Lang, string>>;
  notSure?: Partial<Record<Lang, string>>;
  audio: Partial<Record<Lang, string>>;
  sources: string[];
  assumption: boolean;
}

export type Decision = "act" | "wait" | "ask";

export interface ReferralCheck {
  summary: PlotSummary;
  answer: AnswerCard;
  decision: Decision;
  date: Date;
}
