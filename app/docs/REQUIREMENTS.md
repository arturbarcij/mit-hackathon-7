# Requirements traceability

The matrix from the master prompt, Section 12. Nothing is "pass" until its acceptance test passes and the evidence is linked. The QA reviewer sets final statuses.

Status values: `todo`, `pass`, `fail`. Snapshot taken Sat 3 Oct 2026, late evening CEST.

Branches cited (none merged yet):
- engine: `cursor/engine-offline-core-d90f`, [PR #2](https://github.com/arturbarcij/mit-hackathon-7/pull/2)
- geo: `cursor/geo-outlier-map-d222`, [PR #3](https://github.com/arturbarcij/mit-hackathon-7/pull/3)
- wave 1 (research, ml data prep, docs drafts): `cursor/wave1-research-engine-82ab`, [PR #4](https://github.com/arturbarcij/mit-hackathon-7/pull/4)

No row is `pass` yet. Most acceptance tests need the real model, the farmer screens or the live URL, none of which exist yet. Where a branch already holds part of the evidence, the last column says what and where.

| ID | Requirement (source) | How we meet it | Acceptance test | Evidence | Status | Evidence so far |
|---|---|---|---|---|---|---|
| R1 | Runs on a device the user already has (§06) | PWA on the household Android smartphone; SMS on her basic phone | Install and run on a real Android phone (or throttled Chrome mobile emulation, stated) | Screen recording | todo | engine: manifest installable test passes in Chromium (`tests/e2e/offline.spec.ts`). Not run on an Android phone. No screens yet |
| R2 | Core feature works offline (§06) | Service worker caches app, model, audio, rules | Airplane mode: full leaf check end to end | Video 2 clip | todo | engine: Playwright "full ten-leaf check works in airplane mode" passes with a fixture model (not coffee). Needs the real model, the UI and the video |
| R3 | Model small enough to side-load or send over weak link (§06) | int8 ONNX, at most 5 MB; bundle at most 15 MB | File sizes printed in build log; download time at 1 Mbit/s computed | EVALUATION.md | todo | engine: precache 3.1 MiB without model or audio (`ARCHITECTURE.md`). `leaf.onnx` not delivered |
| R4 | At least one interaction in a named local language, voice or text (§06) | Swahili voice + text for all answers | Every answer ID has Swahili text and audio | Answer bank table | todo | engine: placeholder bank only. Swahili text and audio not delivered (content-voice C1 to C3) |
| R5 | Ready for "less-supported language" question (§06) | Kikuyu subset via MMS-TTS; process to add a language documented | Kikuyu clips play for at least 5 core answers; doc describes 30-clip recording path | LANGUAGES.md | todo | wave 1: `docs/LANGUAGES.md` draft describes the recording path. No Kikuyu clips yet |
| G1 | Human makes the final call (§06) | Act / wait / ask buttons; officer confirms | No code path performs an action without a user tap | Code review + demo | todo | engine: `useCheck().choose` saves locally and sends nothing; `smsHref` only builds a link. UI and officer confirm not built |
| G2 | Agentic steps check in with user (§06) | SMS opened pre-filled, user sends | Referral never auto-sends | Demo | todo | engine: no send path in the engine; Playwright hooks test asserts "nothing posted". UI not built |
| G3 | Avoid hallucinations (§06) | Fixed answer list; no generative runtime | Grep: no LLM calls in client; every rendered answer exists in the bank | Test | todo | engine: `tests/engine/noai.test.ts` passes (no AI API named in `src/`); `decide.ts` only returns cards from the bank, else `ask_officer`. "Rendered" half needs the UI |
| P1 | Fail-safe: "not sure, ask a person" (§09) | Calibrated threshold, quality gate, OOD, disagreement rule | Blurry, dark, non-leaf and mixed inputs all abstain | Test images + video | todo | engine: blurry, dark and tiny photos rejected in Playwright; 4 unsure of 10 routes to `too_many_unsure` in `decide.test.ts`; mixed problems route to `mixed_problems` in the placeholder rules, with no dedicated test found. Non-leaf needs the real model. No separate OOD score built |
| P2 | Credible privacy, consent, bias, oversight (§09) | RESPONSIBLE_AI.md, consent screens, on-device storage | Reviewer checklist passes | RESPONSIBLE_AI.md | todo | wave 1: `docs/RESPONSIBLE_AI.md` draft. engine: two-level consent and local storage in `storage.ts`, `sync.ts`. Consent screens not built |
| D1 | Cite all data sources (§07) | DATA_CARD.md and in-app "Sources" page | Every dataset and statistic has a citation | DATA_CARD.md | todo | wave 1: `docs/DATA_CARD.md` draft and `src/content/sources.json` (60 sources). Sources page not built |
| D2 | Problem data with source, year, country (§7.2) | Problem evidence table | Each figure has all three fields | README | todo | wave 1: problem table in `docs/DATA_CARD.md` section 1. README not written yet |
| D3 | Build data: name, source, licence, size (§7.2) | Data card | All four fields filled for every set | DATA_CARD.md | todo | wave 1: `docs/DATA_CARD.md` section 2, all four fields for each dataset. Our own background photos: size pending ml |
| D4 | State what data does not cover (§7.2, scored) | "Gaps" section per dataset and for the model | Section exists, specific, not generic | DATA_CARD.md | todo | wave 1: `docs/DATA_CARD.md` section 4 |
| D5 | Synthetic data labelled (§7.2) | `synthetic: true` flag and UI tag | Every synthetic record tagged | DB query | todo | geo: `public/geo/plots.geojson` and `outliers.json` carry `synthetic: true`. engine: real referrals carry `synthetic: false`. Seed referrals and UI tag not built |
| W1 | Working prototype (§05) | Live URL | URL loads on a fresh phone; full flow works | Live URL | todo | No live URL yet |
| W2 | Clear AI technique and why not simpler (§05) | Section 7 text in README and Video 3 | Present in both | README, Video 3 | todo | Not written yet (README is D3) |
| W3 | Proof it works on real examples (§05) | Cross-domain evaluation, worked examples | EVALUATION.md complete | EVALUATION.md | todo | wave 1: `docs/EVALUATION.md` skeleton only. No results (ml M5) |
| B1 | One better agricultural decision (Annex B) | Act / wait / ask on leaf problem, with timing and referral | Demo shows the decision being made | Video 2 | todo | engine: decision, season window and referral built. No demo yet |
| B2 | Addresses extension gap and registry precondition (Annex B) | Referral keyed to coop member number; officer queue | Officer dashboard receives referral | Video 2 | todo | engine: referral carries the member number (`referral.ts`); sync inserts into `referrals`. geo: plot data keyed to member numbers. Dashboard not built |
| S1 | Live project URL (platform) | Lovable publish or Vercel | Opens in incognito on mobile | URL | todo | No live URL yet |
| S2 | Code link; repo public after submission (platform) | GitHub repo, MIT licence, no secrets | `git log -p` secret scan clean; repo set public right after submit | Repo | todo | Repo exists. No `LICENSE` file yet. Secret scan not run |
| S3 | 3 videos, each MP4/MOV, max 60 s, max 1 GB (platform) | Section 11 | `ffprobe` duration under 60 s, size under 1 GB, container MP4/MOV | Files | todo | Not recorded |
| S4 | Videos jointly cover PDF items a to e (§08) | Section 11 mapping | Checklist ticked per video | Checklist | todo | Not recorded |
| S5 | Submitted before 4 Oct 2026 15:00 CEST | Freeze 13:30 | Submission confirmation screenshot | Screenshot | todo | Not submitted |
| J1 | Scalability and reuse (§09) | Model + rule table + answer bank are swappable per crop/language; cooperative-based rollout | REPLICATION.md describes cocoa in Côte d'Ivoire as an example swap | Doc | todo | wave 1: `docs/REPLICATION.md` draft with the cocoa sketch (no cocoa sources yet) |
