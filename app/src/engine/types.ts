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
  synthetic: boolean;
}

/** Result of `parseReferral`. Fields mirror the JANI1 SMS format in kb/CONTRACTS.md. */
export interface ParsedReferral {
  version: 1;
  memberId: string;
  plotId: string;
  /** ISO date, yyyy-mm-dd. */
  date: string;
  n: number;
  rust: number;
  cercospora: number;
  phoma: number;
  miner: number;
  unsure: number;
  uncertain: number;
  /** Leaves not accounted for by the problem counts or unsure: healthy plus any non-leaf photos. */
  other: number;
  answerId: string;
  /** Mean confidence over leaves the model committed to, 0 to 100. */
  confidence: number;
  decision: Decision;
}

/** Contents of public/model/model.json (written by the ml agent). */
export interface ModelConfig {
  version: string;
  labels: Label[];
  input: {
    size: number;
    resize: string;
    /** Optional. Resize the shorter side to this before the centre crop of `size` (for example 256 then 224). */
    resize_to?: number;
    mean: [number, number, number];
    std: [number, number, number];
    layout: string;
    range: string;
  };
  temperature: number;
  threshold: number;
  sha256?: string;
  bytes?: number;
}
