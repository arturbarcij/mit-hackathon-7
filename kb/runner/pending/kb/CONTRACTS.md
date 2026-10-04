# Contracts

Shared types and formats between agents. The engine agent owns this file; ui and content-voice propose changes under "Change requests" at the bottom. Build against these now, using mocks, so nobody waits on anybody.

## TypeScript types (`app/src/engine/types.ts`)
```ts
export type Lang = 'sw' | 'kik' | 'en';
export type Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf';

export interface QualityResult {
  ok: boolean; reason?: 'blurry' | 'dark' | 'too_small' | 'not_on_page'; blur: number; brightness: number;
  sheet?: { paper: number; edge: number; leaf: number; detail?: 'no_page' | 'leaf_cut_off' | 'leaf_too_small' };
}
export interface ClassifyOptions { sheetGate?: boolean }   // default true; false only for bundled demo photos

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

## summarisePlot semantics (exact; the rules and the QA decision matrix depend on them)
- Disease labels are `rust`, `cercospora`, `phoma`, `miner`.
- `n` = leaves photographed. `counts` = per label, including `healthy` and `not_leaf`.
- `affected` = leaves with a disease label (accepted, not unsure).
- `distinctProblems` = number of distinct disease labels with at least one leaf.
- `uncertain` = unsure leaves (below threshold or failed quality) PLUS `not_leaf` leaves.
- `dominant` = `not_leaf` if not_leaf leaves are more than half of `n`; else the most common disease label if `affected` >= 1 (ties: rust, cercospora, phoma, miner); else `healthy` if any healthy leaf; else `none`.
- At capture time a `not_leaf` prediction triggers an immediate retake prompt (answer `not_a_leaf`), like a blurry photo.
- Sheet gate (leaf flat on a plain page, `kb/edge/sheet_gate.py`): a failing photo gets quality `reason: 'not_on_page'`, is never classified (label `unsure`), and the retake card is `retake_on_page` (`useCheck().classify` returns it). If accepted anyway it counts as unsure, like a failed-quality photo.

## Engine functions (`app/src/engine/index.ts`)
```ts
loadModel(): Promise<{ version: string; mock: boolean }>
checkQuality(img: ImageBitmap, opts?: ClassifyOptions): QualityResult   // too_small, dark, blurry, then sheet gate
classifyLeaf(img: ImageBitmap | Blob, opts?: ClassifyOptions): Promise<LeafResult>   // a Blob/File is decoded at native size (createImageBitmap); preprocess.ts is bit-exact with train.py
sheetGate(rgba, w, h): { ok; reason?: 'not_on_page'; detail?; paper; edge; leaf }   // port of kb/edge/sheet_gate.py
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
`Q` is the rounded mean calibrated confidence of accepted leaves, 0 when none (parsers still accept the legacy `Q:-`). `N:0` is valid.
`JANI1` is the format version. Member ID is the cooperative membership number (the existing registry). No names.

## Rules table fields (`app/src/content/rules.json`)
Condition keys allowed: `dominant`, `affected_gte`, `affected_lte`, `uncertain_gte`, `distinct_problems_gte`, `window`. First match wins. Last rule is `{"if": {}, "then": "ask_officer"}`.

## Model files (`app/public/model/`)
`leaf.onnx` and `model.json` as specified in `kb/agents/ml.md`. Input name `input`, output name `logits`.

## Backend tables
As specified in `kb/agents/ui.md` (`referrals`, `corrections`).

## Geo outputs
`app/public/geo/plots.geojson` and `app/public/geo/outliers.json`, schema in `kb/agents/geo.md`. Reason codes: `in_line_with_peers`, `area_wide_weather`, `canopy_loss_check_leaves`, `drop_other_cause_ask_officer`, `not_enough_data`. The officer map colours them green, blue, red, amber, grey, and always shows the "synthetic deliveries" label.

## Change requests
(none yet)

## Usage note (engine, Sun 4 Oct 00:15)
- The UI imports only from `src/engine/index.ts` and `src/hooks/useEngine.ts`. Retire Lovable `src/lib/referralSms.ts` and `src/lib/parseReferral.ts`; call `buildReferral` / `parseReferral`.
- `uncertain` and SMS `U:` = unsure leaves PLUS `not_leaf` leaves. So R+C+H+L+U <= N and parse sets healthy = N - (R+C+H+L+U).
- `loadModel()` never rejects. `mock: true` means show the mock badge. A transient load failure retries on the next call; an invalid model.json (for example threshold 0.0) stays mock for the session.
- `classifyLeaf` returns `unsure` below threshold or when quality fails. Retake on failed quality or `not_leaf` (`retake_blurry`, `retake_dark`, `not_a_leaf`); use `useCheck().classify`.
- Rules use absolute counts tuned for n = 10. Checks with fewer leaves are not yet routed to an ask card.
- `saveCheck`, `savePhoto`, `queueForSync` are no-ops without main consent. `setConsent({ main: false })` wipes local data, PIN included. Photos leave only when `check.consentPhotos` and current `consent.photos` are both true.
- `D:`/`check_date` use the phone's local date. `M:`/`P:` and `member_id`/`plot_id` normalised: uppercase, A-Z 0-9 '-', max 12. Missing values are '-'.
- `Q:` = mean confidence of accepted leaves, whole percent, 0 when none (was '-' before 01:00 Sun 4 Oct).
- `parseReferral` never throws; reads JANI1 and the old `JANI` short form (`format` says which).
- `syncPending()` returns 0 offline or before `setSyncSender`; the UI injects the Supabase insert. The row includes `decision`.
- The engine sends nothing by itself. Full notes: kb/engine/HANDOFF.md.
