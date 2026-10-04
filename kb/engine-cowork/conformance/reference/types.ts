// Types copied from kb/CONTRACTS.md, section "TypeScript types". Keep identical.
// ParsedReferral is named in CONTRACTS but not defined there; the shape below is
// the reference proposal (see RESULTS.md, ambiguities).

export type Lang = 'sw' | 'kik' | 'en';
export type Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf';

export interface QualityResult { ok: boolean; reason?: 'blurry' | 'dark' | 'too_small'; blur: number; brightness: number; }

export interface LeafResult {
  label: Label | 'unsure';          // 'unsure' when below threshold or quality failed
  probs: Record<Label, number>;     // calibrated (temperature applied)
  confidence: number;               // max calibrated prob
  quality: QualityResult;
  abstained: boolean;
  modelVersion: string;             // from model.json, 'mock' when mocked
}

export interface PlotSummary {
  n: number;                        // leaves photographed
  counts: Record<Label, number>;
  uncertain: number;
  dominant: Label | 'none';         // most common non-healthy label, or 'healthy'
  affected: number;                 // leaves with any problem label
  distinctProblems: number;
}

export type SeasonWindow = 'pre_short_rains' | 'short_rains' | 'pre_long_rains' | 'long_rains' | 'dry';

export interface AnswerCard {
  id: string;                       // key in answers.json
  severity: 'ok' | 'watch' | 'act' | 'ask';
  text: Partial<Record<Lang, string>>;
  notSure?: Partial<Record<Lang, string>>;
  audio: Partial<Record<Lang, string>>; // '/audio/sw/<id>.mp3'
  sources: string[];
  assumption: boolean;
}

export type Decision = 'act' | 'wait' | 'ask';

export interface Check {
  id: string; createdAt: string; lang: Lang;
  leaves: LeafResult[]; summary: PlotSummary; window: SeasonWindow;
  answerId: string; decision?: Decision;
  memberId?: string; plotId?: string;
  consentMain: boolean; consentPhotos: boolean; synced: boolean;
}

// Not in CONTRACTS (only referenced). Field by field mirror of the JANI1 line.
export interface ParsedReferral {
  version: 'JANI1';
  memberId: string;                 // M:
  plotId: string;                   // P:
  date: string;                     // D: yyyymmdd, as written
  n: number;                        // N:
  counts: { rust: number; cercospora: number; phoma: number; miner: number }; // R: C: H: L:
  uncertain: number;                // U:
  answerId: string;                 // A:
  confidence: number;               // Q: 0 to 100
  decision: Decision;               // X:
}
