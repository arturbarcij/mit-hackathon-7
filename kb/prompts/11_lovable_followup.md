# Lovable follow-up (draft, NOT sent; sending spends credits)

Review of project 4619dfd1 (Jani Leaf Check) at commit 7b17159, Sat 3 Oct about 23:00 CEST. Send as one message to the ui lane after Arthur approves. Plan mode first is wise.

Findings the prompt fixes:
1. `src/engine/index.ts` is a mock. Sw and Kikuyu cards fall back to English text, audio is a no-op, ids (`rust-action`, `keep-watching`) do not match answers.json ids. This file belongs to the engine agent (OWNERSHIP.md), so Lovable should only consume it, not extend it.
2. Referral text omits member number, plot and date (MASTER_PROMPT section 4 step 8 requires them, under 160 characters).
3. No PWA, no onnxruntime-web, no idb in package.json. App is TanStack Start with SSR (nitro). Offline after first load is not yet shown to be possible.
4. Migration: any account that signs up gets the officer role and can read all referrals; anon can insert unlimited rows. Fine as a labelled prototype, not for the Responsible AI doc without a caveat.
5. Not published, so no live URL yet.

Prompt text:

> Plan first, then build. Do not change the farmer flow layout. (1) Load answers from `src/content/answers.json` (copied by the sync script) and render the `sw`, `kik`, `en` text for the answer id returned by the engine; never show English when sw or kik is selected, and show the `review_status` label ("pending native review") under Kikuyu text. (2) Referral SMS: build "member id, plot id, date, rust/total, uncertain, decision" and keep under 160 characters; show the character count; the user taps send. (3) Make the farmer route work offline after first load: add a service worker that precaches the app shell, `/model/*`, `/audio/*` and `src/content/*`; show an Online/Offline badge from `navigator.onLine`. If the TanStack Start SSR build cannot be precached, tell me and propose switching the farmer route to a static client build. (4) Officer sign-up: stop auto-granting the officer role; instead seed one demo officer account and show a visible "prototype" banner on /officer. Rate-limit or cap referral inserts per member_id per day. (5) Label every synthetic row "synthetic" in the table and the map. (6) Publish and give me the live URL.
