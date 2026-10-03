# Contracts

Shared types and formats between agents. The engine agent owns this file; ui and content-voice propose changes under "Change requests" at the bottom. Build against these now, using mocks, so nobody waits on anybody.

## TypeScript types (`app/src/engine/types.ts`)
```ts
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
```

## Engine functions (`app/src/engine/index.ts`)
```ts
loadModel(): Promise<{ version: string; mock: boolean }>
checkQuality(img: ImageBitmap): QualityResult
classifyLeaf(img: ImageBitmap): Promise<LeafResult>
summarisePlot(leaves: LeafResult[]): PlotSummary
seasonWindow(date: Date): SeasonWindow
decide(summary: PlotSummary, date: Date): AnswerCard
saveCheck(c: Check): Promise<void>; listChecks(): Promise<Check[]>
getConsent(): Promise<{ main: boolean; photos: boolean }>; setConsent(c): Promise<void>
buildReferral(c: Check): string        // max 160 GSM-7 chars
smsLink(number: string, body: string): string
parseReferral(text: string): ParsedReferral | null
play(answerId: string, lang: Lang): Promise<void>
syncPending(): Promise<number>         // store-and-forward; returns count synced
```
React hooks: `useEngine()`, `useCheck()`, `useConsent()`, `useOnline()`.

## Referral SMS format (max 160 chars)
```
JANI1 M:<member> P:<plot> D:<yyyymmdd> N:<n> R:<rust> C:<cerco> H:<phoma> L:<miner> U:<unsure> A:<answerId> Q:<conf%> X:<decision>
```
Example: `JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask`
`JANI1` is the format version. Member ID is the cooperative membership number (the existing registry). No names.

## Rules table fields (`app/src/content/rules.json`)
Condition keys allowed: `dominant`, `affected_gte`, `affected_lte`, `uncertain_gte`, `distinct_problems_gte`, `window`. First match wins. Last rule is `{"if": {}, "then": "ask_officer"}`.

## Model files (`app/public/model/`)
`leaf.onnx` and `model.json` as specified in `kb/agents/ml.md`. Input name `input`, output name `logits`.

## Backend tables
As specified in `kb/agents/ui.md` (`referrals`, `corrections`).

## Change requests
(none yet)
