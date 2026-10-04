# L3 draft: Lovable message after the real engine lands (NOT SENT)

Send only after: (1) the real engine is on `main` via GitHub, (2) `ENGINE_DIR=<repo>/app/src/engine npx vitest run` in `kb/engine-cowork/conformance` is green, (3) the lead has fixed the content JSON shape question (COMPAT.md point 1). One message, plan mode off. Replaces `kb/prompts/lovable/L3_engine_publish.md`.

---

The real engine is now in src/engine and src/hooks via GitHub. Do not modify src/engine, src/hooks/useEngine*, vite.config.ts, public/model, public/audio, public/ort, public/geo or src/content/*.json. Change only UI code. Keep every screen, size and colour you have now unless a step below says otherwise.

1. Content files. src/content/answers.json and rules.json are now plain arrays, and season.json has `windows` at the top level. In lib/answerText.ts, lib/mockBridge.ts and the Limits screen, read both shapes: `const list = Array.isArray(data) ? data : data.answers` (same for rules, season, sources). The app must not crash on first render.

2. Hooks. Replace local engine calls in routes/index.tsx with the hooks from src/hooks/useEngine.ts: `useEngine()` for model state and the mock flag, `useCheck()` for leaves, summary, answer and the saved Check, `useConsent()` for both consents, `useOnline()` for the online badge. Remove the window online/offline listeners. Keep lib/mockBridge.ts but stop calling it; the summary and the answer now come only from the engine.

3. Consent order. Keep: language, then main consent, then the guide. On "Yes" call `setConsent({ main: true, photos: false })`; on "No" call `setConsent({ main: false, photos: false })` and show the stopped screen. On the next app start, skip the consent screen if main consent is already true. The photo-sharing switch on the referral screen calls `setConsent({ main: true, photos: <value> })` and is off by default.

4. Unsure and not-leaf, shown separately. On the Summary screen show three tiles with icon, number and one short word: problem leaves (dominant label), healthy leaves, and "not sure" leaves (`summary.uncertain`). Never fold not-sure leaves into healthy or into a disease. During capture, a `not_leaf` result or a failed quality check shows the matching retake card (`not_a_leaf`, `retake_blurry`, `retake_dark`) and a Retake button; that leaf is never added. If the photo cannot be decoded, show the retake card; do not classify a placeholder.

5. Answer card. Show `answer.text[lang]` and `answer.notSure[lang]` from the card the engine returns (fall back to English with the "not translated yet" tag, as now). Every screen keeps its speaker button: call `play(id, lang)` with the answer id. For screens without an answer id (language, summary, decision, history, limits) keep the button and let `play` do nothing if there is no file. Do not show any audio error.

6. Act, wait, ask. The decision screen keeps three large buttons: "I will act", "I will wait", "Ask the officer". The farmer chooses; the app never pre-selects. Save the choice into the Check with `saveCheck`. Show the referral screen when the choice is "Ask the officer" or the answer severity is "ask"; otherwise go to History with an optional "Send to officer" button.

7. Referral SMS. Build the text with `buildReferral(check)` from the engine and show it as a preview with the character count (max 160). Open the SMS app with `smsLink(number, body)` only when the farmer taps "Send SMS". She presses send in her own SMS app. Nothing is sent automatically. Delete lib/referralSms.ts once the preview uses the engine. In lib/parseReferral.ts accept member ids `[A-Z0-9-]{1,16}`, plot ids `[A-Z0-9-]{1,8}`, `-` for an empty field and `N:0`.

8. History and sync. History comes from `listChecks()`, newest first, and survives a reload. When online and main consent is true, call `syncPending()` after saving a check and show "saved, will send when online" or "sent" as a small status line. Never upload photos unless photo consent is true.

9. Mock badge. Keep the "MOCK MODEL" badge logic. It shows while `useEngine()` reports `mock: true`, and disappears only when the real model has loaded.

10. Rules for every screen (do not break these):
- No marketing words, no gradients, no glassmorphism, no emoji, no stock images.
- Every number has a source or a visible "assumption" or "synthetic" label. Simulated parts say "simulated".
- One action per screen, touch targets at least 56 px, base font 18 px, works at 360 px width, high contrast.
- Icon plus one short line plus a speaker button on every screen. No paragraph instructions.
- When unsure, the app says "ask the officer". It never guesses.
- All strings come from src/content/i18n/*.json. Under Kikuyu text show "machine translation, pending review" where review_status says so.

11. Check at 360 px in an incognito window: full farmer flow with 10 photos, one blurry photo, one non-leaf photo, the referral SMS preview, and History after reload. Then the officer dashboard: paste the SMS from the preview and confirm it is accepted. Then publish and give me the URL.
