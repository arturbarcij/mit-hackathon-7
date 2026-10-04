# Engine handoff

Owner: engine. Date: Sun 4 Oct 2026, about 00:15 CEST. Code: `app/src/engine/**`, `app/src/hooks/useEngine.ts`, tests in `app/tests/engine/**`. Contract: `kb/CONTRACTS.md`.

## What is built
The whole on-phone engine, behind one import (`src/engine/index.ts`): photo quality gate, leaf model (real ONNX via `onnxruntime-web/wasm`, mock fallback with `mock: true`), plot summary, season window, rules-based answer card, IndexedDB storage with consent and optional PIN, JANI1 referral SMS (write and read), audio playback, and store-and-forward sync through a sender the UI injects. Nothing calls a cloud AI API (guarded by `no_ai_api.test.ts`). Importing the engine is SSR-safe (`ssr.test.ts`).

## Files
| File | Role |
|---|---|
| `types.ts`, `index.ts` | shared types, public API (UI imports only from `index.ts`) |
| `image.ts`, `quality.ts` | draw to canvas, blur/brightness/size gate (thresholds provisional) |
| `model.ts`, `model.mock.ts` | load `model.json` + `leaf.onnx`, calibrated softmax, abstention; deterministic mock |
| `plot.ts`, `season.ts`, `decide.ts`, `content.ts` | `summarisePlot`, `seasonWindow`, first-match rules over `src/content/*.json` |
| `storage.ts`, `sync.ts` | IndexedDB (`idb`), consent, PIN, photos, sync queue, `toReferralRow` |
| `referral.ts`, `audio.ts` | SMS build/parse (GSM-7, max 160), `smsLink`, `play`/`stop` |
| `src/hooks/useEngine.ts` | `useEngine`, `useCheck`, `useConsent`, `useOnline` |

## Public API (`src/engine/index.ts`)
| Function | Notes |
|---|---|
| `loadModel(): Promise<{version, mock}>` | never rejects; caches success; a transient failure returns mock and retries next call |
| `checkQuality(img)`, `classifyLeaf(img)` | `img` is an ImageBitmap (or canvas/img); unsure below threshold or bad quality |
| `summarisePlot(leaves)` | `uncertain` = unsure + not_leaf |
| `seasonWindow(date)`, `decide(summary, date)` | `decideForWindow`, `getAnswer(id)` also exported |
| `saveCheck`, `listChecks`, `getConsent`, `setConsent`, `clearAll` | saveCheck is a silent no-op without `consentMain`; `setConsent({main:false})` wipes everything |
| `setPin`, `hasPin`, `unlock`, `lock` | 4-digit PIN hides history for the session |
| `compressPhoto(img)`, `savePhoto(checkId, i, blob)`, `getPhotos(checkId)` | JPEG 0.7, longer side 800; savePhoto no-op without main consent |
| `buildReferral(check)`, `smsLink(number, body)`, `parseReferral(text)`, `toGsm7` | JANI1; parse also reads the old Lovable `JANI ...` short form; never throws |
| `play(answerId, lang)`, `stop()`, `audioPath` | falls back to sw, then silent; never rejects |
| `setSyncSender(fn)`, `queueForSync(check)`, `syncPending()`, `toReferralRow` | no network code in the engine; the UI's sender does the insert |

## How the UI should call it
```ts
const { ready, mock } = useEngine();          // show the "mock model" badge when mock
const { consent, setConsent } = useConsent(); // consent screen: setConsent({ main: true, photos: false })
const chk = useCheck({ lang, memberId, plotId });
const bmp = await createImageBitmap(file);
const { result, retake } = await chk.classify(bmp);
if (retake) showAnswer(retake);               // retake_blurry | retake_dark | not_a_leaf
else { chk.accept(result); photos.push(await compressPhoto(bmp)); }
// chk.summary, chk.card (null until one leaf); Noor taps a decision:
chk.setDecision('ask');
const saved = await chk.save();               // stored only with main consent
await Promise.all(photos.map((b, i) => savePhoto(saved.id, i, b)));
const body = chk.referralText();              // JANI1 body; show it, then on tap:
location.href = smsLink(coopNumber, body!);   // Noor presses send herself
if (photosToggle) await setConsent({ main: true, photos: true }); // second consent, asked here
await queueForSync({ ...saved, consentPhotos: photosToggle });
void syncPending();                           // also call on the 'online' event
```
Register the sender once at app start:
```ts
setSyncSender(async (row, photos) => {
  const photo_urls: string[] = [];
  for (const [i, b] of photos.entries()) {     // empty unless both photo consents hold
    const path = `${crypto.randomUUID()}/${i}.jpg`;
    const { error } = await supabase.storage.from('leaf-photos').upload(path, b, { contentType: 'image/jpeg' });
    if (error) throw error;
    photo_urls.push(path);
  }
  const { error } = await supabase.from('referrals').insert({ ...row, photo_urls });
  if (error) throw error;                      // a throw keeps it queued, in order
});
```
`row` holds `member_id, plot_id, check_date, counts, uncertain, answer_id, confidence, decision, photos_shared, synthetic:false`. The `referrals` table in `kb/agents/ui.md` has no `decision` column: add `decision text` or drop the field in the sender.

## Lovable referral mismatch and fix
Lovable has its own `src/lib/referralSms.ts` (short `JANI <member> <plot> <date> ...` form, silent slice at 160) and `src/lib/parseReferral.ts` (member must match `^[A-Z]{2,4}\d{2,6}$`, plot `^P\d{1,3}$`, so plot `2` from CONTRACTS is rejected). These disagree with JANI1 and with each other. Fix: the UI calls the engine's `buildReferral` (or `chk.referralText()`) and `parseReferral` on both farmer and officer screens, and retires `src/lib/referralSms.ts` and `src/lib/parseReferral.ts`. The engine parser reads both formats, so SMS already sent in the short form still parse. Member and plot ids are normalised (uppercase A-Z 0-9 `-`, max 12) the same way in SMS and synced row; `check_date` uses the phone's local date in both.

## Phase 2: move into `web/` (the Lovable repo)
1. Copy `app/src/engine/**` to `web/src/engine/` (replaces the Lovable mock engine), `app/src/hooks/useEngine.ts` to `web/src/hooks/`, `app/src/content/*.json` if newer, and `app/tests/engine/**` to `web/tests/engine/` with `app/vitest.config.ts` and `app/tsconfig.engine.json`.
2. Deps: `idb`, `onnxruntime-web` (1.30.0); dev `fake-indexeddb`, `vitest`, `jsdom`; `@testing-library/dom` only if hooks tests move to `@testing-library/react` (today they use their own `renderHook`).
3. Copy `node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm` and `.mjs` to `web/public/ort/` (recopy on ORT upgrade). Do not ship the `.jsep` files.
4. Offline: follow `kb/engine/OFFLINE_SPIKE.md` (`public/sw.js`, `sw-register.ts`, the `janiPrecache` Vite plugin, one `registerOfflineSW()` line in `__root.tsx`).
5. UI swaps `src/lib/mockBridge.ts`, `referralSms.ts`, `parseReferral.ts` for engine calls; keep the mock badge wired to `useEngine().mock`.
6. Run `vitest run` and `tsc -p tsconfig.engine.json` in `web/`; then the browser checks below.

## Measured facts (app/, Sun 00:15)
- `vitest run`: 14 files, 135 passed, 0 failed, 1 todo (browser parity, E3).
- `tsc -p tsconfig.engine.json`: clean.
- Per file: model 20, season 18, decide 16, referral 14, storage 13, sync 13, audio 8, hooks 8, plot 7, quality 6, flow 6, ssr 3, no_ai_api 2, decide.parity 1 (whole QA decision matrix).
- Flow test: 6 rust + 3 healthy + 1 unsure on 4 Oct gives `rust_high_pre_rains` (act) and SMS `JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:0 U:1 A:rust_high_pre_rains Q:87 X:ask`, which parses back exactly and matches the synced row.

## Known gaps
- Browser parity against `ml/parity_samples` not run (pending E3); `model.test.ts` has it as a todo.
- `kb/agents/ml.md` template ships `threshold: 0.0`; the loader rejects it and falls back to the mock (intended). ml must write the real threshold.
- Quality thresholds (`MIN_BLUR 60`, `MIN_BRIGHTNESS 0.18`, `MIN_SIDE 224`) are provisional; tune on real phone photos.
- `compressPhoto` and `checkQuality` need a real browser check (canvas, OffscreenCanvas, JPEG encode); node tests mock them.
- n < 10: rules use absolute counts tuned for 10 leaves. Red team and judge flagged that the UI lets a check finish at 5 (`finishAfterFive`). Either require 10 in the UI or the engine must route n < 10 to an ask card; not done yet.
- Lovable hosting headers for `.wasm` (content type, compression) are unverified on the real host.
