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
React hooks (`app/src/hooks/useEngine.ts`): `useEngine()`, `useCheck()`, `useConsent()`, `useOnline()`.

### Engine additions (engine agent, Sat 3 Oct)
These extend the list above without changing any signature. All are exported from `src/engine`.
```ts
classifyFile(file: File | Blob): Promise<LeafResult>   // decode + quality gate + model; use this from the UI
bitmapFromFile(file): Promise<ImageBitmap>              // remembers the file name for the mock model
assembleCheck(opts): Check                              // summary + season window + answer id + new id
getAnswer(id: string): AnswerCard | undefined           // guidance and flow cards: how_to_pick_leaves, consent_main, decision_act, ...
getCheck(id), getPhotos(checkId)                        // read back a saved check and its JPEG blobs (max 800 px)
hasPin() / setPin(pin) / unlock(pin) / lock() / removePin(pin) / isLocked()   // optional 4-digit PIN; listChecks() returns [] while locked
stopAudio(), configureSync(target), lastInferenceTimeMs()
saveCheck(c: Check, photos?: Blob[])                    // photos optional second argument
```

### Model runtime delivery
`public/ort/` holds `ort-wasm-simd-threaded.mjs` and `ort-wasm-simd-threaded.wasm.gz` (gzipped on purpose to keep the offline precache small). Regenerate with `npm run copy:ort`. Do not add a raw `.wasm` next to it.

### Usage notes for the ui agent
- `useEngine()` returns `{ status: 'loading'|'ready'|'error', ready, mock, version, error }`. Show the visible "mock model" badge whenever `mock` is true. `mock` is also true when the real model files are not deployed yet (the engine logs a console warning).
- `useCheck({ lang, memberId?, plotId?, target? })` runs one check. `addPhoto(file)` returns `{ accepted, result }`. If `accepted` is false the photo failed the quality gate (`result.quality.reason` is `blurry`, `dark` or `too_small`): play the `retake_blurry` / `retake_dark` card and ask for a retake. Leaves the model is unsure about are accepted and show as `?`.
- `useCheck` also gives `leaves`, `summary`, `card` (the `AnswerCard` for the current photos), `referralText`, `smsHref(number)` and `choose('act'|'wait'|'ask')`. `choose` saves the check on the phone and sends nothing. Open `smsHref(number)` only from the farmer's tap on "Send SMS".
- Use `<input type="file" accept="image/*" capture="environment">` and pass the `File` to `addPhoto`. For the mock model, file names containing `rust`, `cerco`, `phoma`, `miner`, `healthy`, `table` or `blur` give predictable results.
- `useConsent()` returns `{ consent, loaded, setMain, setPhotos }`. Photo consent cannot be on without main consent.
- Sync: call `syncPending()` (also exported from the hook module) when `useOnline()` turns true. Only checks where the farmer chose "ask" and gave main consent are queued. It inserts into `referrals` using `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` if they exist (both are public by design). Photo upload is off until the ui agent supplies `configureSync({ insert, uploadPhotos })`.
- Audio: `play(card.id, lang)` resolves when the clip ends. It falls back to Swahili, then to silence, and never throws. Browsers block audio before a tap, so call it from a tap handler.
- Card text: `card.text[lang] ?? card.text.sw ?? card.text.en`. Never compose your own text.

## Referral SMS format (max 160 chars)
```
JANI1 M:<member> P:<plot> D:<yyyymmdd> N:<n> R:<rust> C:<cerco> H:<phoma> L:<miner> U:<unsure> A:<answerId> Q:<conf%> X:<decision>
```
Example: `JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask`
`JANI1` is the format version. Member ID is the cooperative membership number (the existing registry). No names.

## QualityResult details
`brightness` is the mean luma (0 to 255) of a 256 px copy; below 45 the photo is rejected as `dark`. `blur` is a blur extent from 0 (sharp) to 1 (blurry), higher is blurrier (re-blur method of Crete et al. 2007); above 0.6 the photo is rejected as `blurry`. Exposure independent. Tuned on real BRACOL and Uganda photos. Show the numbers only in debug views.

## PlotSummary details
`dominant` is the most common problem label (ties: rust, cercospora, phoma, miner). It is `not_leaf` only when at least half of the photos are not leaves, `healthy` when no leaf has a problem but at least one is healthy, and `none` otherwise. Leaves the model is unsure about, or whose photo failed the quality gate, count in `uncertain` and never in a class. `affected` counts rust, cercospora, phoma and miner leaves.

## Referral field notes
`Q` is the mean calibrated confidence (whole percent) over leaves the model committed to; 0 when none. A check with no decision yet is written as `X:ask`. A missing member or plot is `NA`. Fields are upper-cased and stripped to `A-Z 0-9 -` (answer ids to `a-z 0-9 _`), with caps of 14, 8 and 40 characters, so the longest message is 130 characters. `parseReferral` also returns `other` (healthy plus non-leaf photos) so the officer dashboard can show the full split.

## Rules table fields (`app/src/content/rules.json`)
Condition keys allowed: `dominant`, `affected_gte`, `affected_lte`, `uncertain_gte`, `uncertain_lte`, `distinct_problems_gte`, `window`. `dominant` and `window` also accept a list of values. An unknown key makes that rule fail to match. First match wins. Last rule is `{"if": {}, "then": "ask_officer"}`.

## Model files (`app/public/model/`)
`leaf.onnx` and `model.json` as specified in `kb/agents/ml.md`. Input name `input`, output name `logits`.

## Backend tables
As specified in `kb/agents/ui.md` (`referrals`, `corrections`).

## Change requests
- (engine, Sat 3 Oct) Added `uncertain_lte` to the rule conditions so `healthy_all` can require no unsure leaves. content-voice: please use it on the `healthy_all` rule, for example `{"if":{"dominant":"healthy","affected_lte":0,"uncertain_lte":0},"then":"healthy_all"}`. Rules that do not use it still work.
- (engine, Sat 3 Oct) `season.json`: the engine reads `windows[].name` as one of `pre_short_rains`, `short_rains`, `pre_long_rains`, `long_rains`, `dry`. Windows may wrap the year end. The first listed window that contains the date wins; uncovered dates are `dry`. Research: please include a `pre_short_rains` window (the weeks before 15 October) so the demo date 4 October maps to it.
