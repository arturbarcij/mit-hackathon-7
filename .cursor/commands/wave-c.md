# Wave C: integrate (Sun 06:30 to 09:30)

Read `kb/WORKFLOW.md` first and clear the "Requests between agents" lines from Wave B. Launch in ONE message as parallel `Task` calls with `run_in_background: true`:

1. [engine] E3 real model in browser with parity against the ONNX int8 export; E4 tests including offline Playwright.
2. [ui] U2 officer dashboard prompts; U3 wire the real engine hooks; publish the live URL (needs Arthur to run the Lovable prompts).
3. [content-voice] C3 audio render only from the frozen `answers.json` (needs L2 keys and L3 reviewer); Kikuyu subset via MMS-TTS; update `REVIEW_LOG.md`.
4. [ml] Final numbers into `EVALUATION.md`, including Uganda and RoCoLe cross-domain results even if poor.
5. [docs] D2 DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION from measured numbers only.
6. [pitch] Update scripts against the real app.
7. [qa] Deterministic run at 08:30 (budgets, parity, client clean).

Cut line 09:30: if the real model is not in the app, say so and stop adding features.
Each prompt ends with "When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."
