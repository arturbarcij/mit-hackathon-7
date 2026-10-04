// Shared engine types. Source of truth: kb/CONTRACTS.md.
// Superset of the Lovable mock's src/engine/types.ts so the real engine is a drop-in replacement.

export type Lang = 'sw' | 'kik' | 'en';
export type Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf';
export const LABELS: readonly Label[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];
/** Disease labels in tie-break order (CONTRACTS: rust, cercospora, phoma, miner). */
export const DISEASES: readonly Label[] = ['rust', 'cercospora', 'phoma', 'miner'];

export interface QualityResult {
  ok: boolean;
  /** 'not_on_page': the sheet gate (leaf flat on a plain page) failed; retake card 'retake_on_page'. */
  reason?: 'blurry' | 'dark' | 'too_small' | 'not_on_page';
  blur: number;
  brightness: number;
  /** Sheet gate measurements (fractions 0 to 1), present when the gate ran. */
  sheet?: { paper: number; edge: number; leaf: number; detail?: 'no_page' | 'leaf_cut_off' | 'leaf_too_small' };
}

/** Options for checkQuality / classifyLeaf. */
export interface ClassifyOptions {
  /** Run the sheet gate (leaf flat on a plain page). Default true. Set false only for bundled demo photos. */
  sheetGate?: boolean;
}

export interface LeafResult {
  label: Label | 'unsure'; // 'unsure' when below threshold or quality failed
  probs: Record<Label, number>; // calibrated (temperature applied)
  confidence: number; // max calibrated prob
  quality: QualityResult;
  abstained: boolean;
  modelVersion: string; // from model.json, 'mock' when mocked
}

export interface PlotSummary {
  n: number;
  counts: Record<Label, number>;
  uncertain: number;
  dominant: Label | 'none';
  affected: number;
  distinctProblems: number;
}

export type SeasonWindow = 'pre_short_rains' | 'short_rains' | 'pre_long_rains' | 'long_rains' | 'dry';

export type Severity = 'ok' | 'watch' | 'act' | 'ask';

export interface AnswerCard {
  id: string;
  severity: Severity;
  text: Partial<Record<Lang, string>>;
  notSure?: Partial<Record<Lang, string>>;
  audio: Partial<Record<Lang, string>>; // '/audio/sw/<id>.mp3'
  sources: string[];
  assumption: boolean;
  /** Extras (optional, additive): answers.json kind and per-language review status for UI labels. */
  kind?: string;
  reviewStatus?: Partial<Record<Lang, string>>;
}

export type Decision = 'act' | 'wait' | 'ask';

export interface Check {
  id: string;
  createdAt: string;
  lang: Lang;
  leaves: LeafResult[];
  summary: PlotSummary;
  window: SeasonWindow;
  answerId: string;
  decision?: Decision;
  memberId?: string;
  plotId?: string;
  consentMain: boolean;
  consentPhotos: boolean;
  synced: boolean;
}

/** Shape used by the Lovable UI mock for buildReferral (kept for drop-in compatibility). */
export interface ReferralCheck {
  summary: PlotSummary;
  answer: AnswerCard;
  decision: Decision;
  date: Date;
  memberId?: string;
  plotId?: string;
  leaves?: LeafResult[];
}

export interface ReferralOptions {
  memberId?: string;
  plotId?: string;
}

/** Parsed referral SMS. Field names match the Supabase `referrals` table (snake_case). */
export interface ParsedReferral {
  member_id: string;
  plot_id: string;
  check_date: string; // YYYY-MM-DD
  counts: Record<Label, number>;
  uncertain: number;
  answer_id: string | null;
  confidence: number | null; // 0 to 1
  decision: Decision | null;
  format: 'JANI1' | 'JANI';
}

/** Row pushed to the `referrals` table by syncPending (via the injected sender). */
export interface ReferralRow {
  member_id: string | null;
  plot_id: string | null;
  check_date: string; // YYYY-MM-DD
  counts: Record<Label, number>;
  uncertain: number;
  answer_id: string;
  confidence: number | null;
  decision: Decision | null;
  photos_shared: boolean;
  synthetic: false;
}

export type SyncSender = (row: ReferralRow, photos: Blob[]) => Promise<void>;

export interface ModelInfo {
  version: string;
  mock: boolean;
}

export interface ModelSpec {
  version: string;
  labels: Label[];
  input: {
    size: number;
    resize: 'shorter_side_then_center_crop';
    mean: [number, number, number];
    std: [number, number, number];
    layout: 'NCHW';
    range: '0-1';
  };
  temperature: number;
  threshold: number;
  sha256: string;
  bytes: number;
}

export interface Consent {
  main: boolean;
  photos: boolean;
}

/** Anything the browser can draw to a canvas. ImageBitmap is what the UI passes. */
export type ImageInput = ImageBitmap | HTMLImageElement | HTMLCanvasElement | OffscreenCanvas;

/** Raw entry in src/content/answers.json. */
export interface AnswerEntry {
  id: string;
  kind: string;
  severity: Severity;
  text: Partial<Record<Lang, string>>;
  not_sure?: Partial<Record<Lang, string>>;
  sources: string[];
  assumption: boolean;
  note?: string;
  review_status?: Partial<Record<Lang, string>>;
  translation_status?: Partial<Record<Lang, string>>;
  reviewed_by?: string | null;
}

export interface RuleCondition {
  dominant?: Label | 'none';
  affected_gte?: number;
  affected_lte?: number;
  uncertain_gte?: number;
  distinct_problems_gte?: number;
  /** Fewer than this many leaves in the plot (decide.ts also applies MIN_LEAVES before the rules). */
  n_lt?: number;
  window?: SeasonWindow;
}

/** Entry in src/content/rules.json. First match wins; last rule is the ask_officer catch-all. */
export interface Rule {
  if: RuleCondition;
  then: string;
  sources?: string[];
  assumption?: boolean;
  note?: string;
}

export interface SeasonWindowDef {
  name: SeasonWindow;
  start_month: number;
  start_day: number;
  end_month: number;
  end_day: number;
  wraps_year?: boolean;
  basis?: string;
}

export interface SeasonFile {
  location: { name: string; latitude: number; longitude: number };
  source: string[];
  note?: string;
  windows: SeasonWindowDef[];
}
