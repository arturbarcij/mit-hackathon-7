# Lovable prompt L3: make the farmer route ready for the real engine (draft, NOT sent; sending spends credits)

Scope: UI-side changes only in `src/routes/index.tsx` and Lovable-owned files, so Cursor's real `src/engine` drops in without further UI work. Based on `AUDIT_LOVABLE.md`. Send as one message after Arthur approves. Plan mode first.

Prompt text:

> Plan first, then build. Do not change the farmer flow layout or the design tokens. Do NOT modify anything in `src/engine/` (another developer replaces that folder from GitHub; your mock stays until then). Keep the amber "MOCK MODEL" badge driven by `loadModel().mock`.
>
> (1) Types. Add these two types to `src/engine/types.ts` ONLY if they are missing, as the single allowed exception, exactly as written: `export type SeasonWindow = 'pre_short_rains' | 'short_rains' | 'pre_long_rains' | 'long_rains' | 'dry';` and `export interface Check { id: string; createdAt: string; lang: Lang; leaves: LeafResult[]; summary: PlotSummary; window: SeasonWindow; answerId: string; decision?: Decision; memberId?: string; plotId?: string; consentMain: boolean; consentPhotos: boolean; synced: boolean; }`. Re-export them from `src/engine/index.ts`. Change nothing else in that folder.
>
> (2) Build a `Check` in `index.tsx`. After the decision step create one object of type `Check`: `id` a random id, `createdAt` `new Date().toISOString()`, `lang` the chosen language, `leaves` the LeafResult array, `summary` from `summarisePlot`, `window` set to `'pre_short_rains'` for now (the real engine exports `seasonWindow(date)`; import it when it exists), `answerId` the id of the card returned by `decide`, `decision` the farmer's choice, `memberId` and `plotId` from the new inputs in (3), `consentMain` from the consent screen, `consentPhotos` from the photo toggle, `synced: false`. Call `buildReferral(check)` with this object and nothing else. Delete the local `ReferralCheck` usage from the route.
>
> (3) Referral screen inputs. Above the SMS preview add two short inputs with i18n labels: cooperative member number (placeholder `OCC0412`) and plot (placeholder `2`). Remember both in localStorage next to the cooperative phone number. Allow them to be empty. No names, no free text fields.
>
> (4) SMS preview. Show the string returned by `buildReferral(check)` verbatim in a monospace box, with a character counter `n/160` and a red counter if over 160. The "Send SMS" button opens `smsLink(number, body)`. Nothing is sent automatically. The mock will still show its old sentence; that is expected until the engine lands.
>
> (5) Card text and audio from the engine. Render `card.text[lang] ?? card.text.sw ?? card.text.en` and `card.notSure?.[lang] ?? card.notSure?.sw ?? card.notSure?.en`. Show the speaker button active only when `card.audio[lang]` exists; on tap call `play(card.id, lang)`. When the language is Kikuyu show a small grey label "pending native review" under the text (the content file carries this status).
>
> (6) Audio ids. `play()` must only be called with an answer id from `src/content/answers.json`, never with a screen name. Map the screens: language screen -> `language_name`, consent -> `consent_main`, how to pick leaves -> `how_to_pick_leaves`, capture -> `how_to_photograph`, decision buttons -> `decision_act`, `decision_wait`, `decision_ask`, referral -> `referral_ready`, photo toggle -> `consent_photos`. Where no answer exists (summary, history, limits) show no speaker button. Do not invent ids.
>
> (7) Decode failure. If `createImageBitmap` fails, do not call `classifyLeaf` with a fake object. Show the `retake_blurry` card text and the retake button, and leave the leaf slot empty.
>
> (8) History and consent. Keep the in-memory history for now, but route all writes through two small functions `saveCheckLocal(check)` and `listChecksLocal()` in `src/lib/checkStore.ts` that the engine's `saveCheck`/`listChecks` will replace one for one. Store the consent screen answer (`consentMain`) and the photo toggle (`consentPhotos`) in that store too.
>
> (9) Officer paste box. In `src/routes/officer.tsx` import `parseReferral` from `@/engine` if it exists, else from `src/lib/parseReferral.ts`, and accept a plot id of `2` or `P07` (change the plot regex to `^[A-Za-z0-9_-]{1,8}$`). Label the box "simulated SMS gateway".
>
> (10) Do not add a service worker, onnxruntime, or IndexedDB; those come with the engine. Run the existing vitest tests and fix only what you broke. Report the diff per file.

Notes for the lead:
- Item (1) is the one exception to "never touch src/engine": adding two type declarations that CONTRACTS already defines so the route compiles today. Cursor's engine will overwrite the file with the same types.
- After the engine lands, run `ENGINE_PATH=/path/to/app/src/engine npx vitest run` in `ec/conformance` to confirm.
