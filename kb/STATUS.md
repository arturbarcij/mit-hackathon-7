# Status board

Update your own rows only. Keep it short. Status: `todo`, `doing`, `blocked`, `done`. Times are CEST.

**Deadline:** Sun 4 Oct 15:00. **Freeze and submit:** 13:30. **Cut line:** 09:30 (no new features after this; if the real model is not in the app, ship what works).

## Board
| ID | Task | Owner | Target | Status | Blocker / note |
|---|---|---|---|---|---|
| L1 | Connect GitHub in Lovable, clone repo into `MIT_Hackathon_7/app` | Arthur | Sat 21:30 | todo | |
| L2 | Fill `app/backend/.env` with keys | Arthur | Sat 21:30 | todo | |
| L3 | Find a Swahili speaker to review answers (10 min, Sun morning) | Arthur | Sun 09:00 | todo | |
| L4 | Android phone for demo (or emulation, stated) | Arthur | Sun 10:00 | todo | |
| R1 | Problem evidence table | research | Sat 22:30 | done | `kb/research/EVIDENCE.md`, all sources merged in `kb/research/sources.json` (60). Coffee-county coverage and Gikuyu speaker count NOT FOUND. Do not use the Kilimo Trust figure (unverifiable) |
| R2 | Agronomy guidance | research | Sat 23:00 | done | `kb/research/GUIDANCE.md`. Copper mid Oct before short rains, repeat after 3 weeks (S1). Only Kenyan threshold: about 20% rust leaves for a curative spray via officer (S2). No published copper trigger; 2 of 10 is an assumption |
| R3 | Dataset facts and licences | research | Sat 23:00 | done | `kb/research/DATASETS.md`. JMuBEN has no healthy or miner (those are in JMuBEN2). MMS-TTS Kikuyu and NLLB are CC BY-NC 4.0 |
| R4 | season.json | research | Sat 23:30 | done | `kb/research/season.json` (engine placeholder shape), method in `SEASON.md`. Pre-rains = 4 weeks before onset (assumption). content-voice / engine: copy to `app/src/content/season.json` |
| M1 | Data download, manifest, dedupe, splits | ml | Sat 22:30 | done | 6 datasets, rotation-aware dedupe (992 groups; 216 Uganda phoma images were JMuBEN copies, excluded). `app/ml/manifest.csv`. not_leaf is thin (407 PlantDoc images) |
| M2 | Train v1 | ml | Sun 00:30 | done | v2 shipped in `app/public/model/` (v2-2026-10-04, 1.64 MB). Uganda test (same farms as uganda_train, not cross-country): acc 0.838, F1 0.866, abstains 54.7%, accepted accuracy 98.7%. RoCoLe: abstains 97.8%, rust recall 0.03 (safe, not useful). v1 was Uganda 0.17, RoCoLe 0.0 |
| M3 | Calibrate, threshold, OOD | ml | Sun 01:00 | done | v2: temperature 0.971, threshold 0.985 (target 95%; 96.2% accepted accuracy on Uganda calib at 46.2% coverage; fitted on fp32 logits, shipped model is int8). Blank pages accepted as a disease: 2 of 300 (v1: 125) |
| M4 | ONNX int8 export, parity, model.json | ml | Sun 01:30 | done | `export.py` works: 1.64 MB weight-only int8, 10 parity samples, engine preprocessing matched within 3e-7 in Node. v2 browser parity passes (Chromium, engine branch + v2 files) after matching the box-filter downscale |
| M5 | EVALUATION.md | ml | Sun 02:00 | done | `app/docs/EVALUATION.md`: v1 vs v2, independence of each test set, abstention options pending. Missing: v2 browser timing and airplane-mode run with v2 |
| E1 | Engine with mock model + hooks | engine | Sat 23:30 | todo | needs L1 |
| E2 | PWA offline caching | engine | Sun 00:30 | todo | |
| E3 | Real model integrated, parity in browser | engine | Sun 08:30 | todo | needs M4 |
| E4 | Engine tests incl. offline Playwright | engine | Sun 09:30 | todo | |
| U1 | Lovable project, routes, farmer flow with mocks | ui | Sat 23:30 | todo | |
| U2 | Officer dashboard, tables, seed data | ui | Sun 08:00 | todo | |
| U3 | Wire real engine hooks, publish live URL | ui | Sun 09:30 | todo | needs E1 |
| C1 | answers.json + rules.json | content-voice | Sat 23:00 | done | 30 cards, 13 rules, season.json copied. PR #2 engine: 107 tests pass with this content. Check with `python3 app/backend/scripts/validate_content.py`. 2-of-10 rust trigger is an assumption, officer to confirm |
| C2 | Swahili + Kikuyu translations | content-voice | Sat 23:30 | doing | text done: Swahili all 30, Kikuyu 8 core cards, machine-drafted. Needs L3 native review via `kb/content/ANSWERS_REVIEW.md`. Audio (C3) not started, needs L2 |
| C3 | Audio rendered (ElevenLabs, MMS) | content-voice | Sun 00:30 | todo | needs L2 |
| D1 | Doc skeletons | docs | Sat 22:30 | done | all 7 docs in `app/docs/`, `app/src/content/sources.json`, `app/LICENSE` (MIT). DATA_CARD and RESPONSIBLE_AI are full drafts; EVALUATION waits on ml |
| D2 | DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION | docs | Sun 10:30 | todo | needs R1, R3, M5 |
| D3 | README final | docs | Sun 11:00 | todo | |
| V1 | Three videos recorded and checked | Arthur (pitch later) | Sun 12:45 | todo | |
| S1 | Submit, save confirmation, make repo public | Arthur | Sun 13:30 | todo | |

## Measured budgets
| Item | Target | Measured |
|---|---|---|
| leaf.onnx | at most 5 MB | |
| Total offline precache | at most 15 MB | |
| Audio total | at most 4 MB | |
| Inference per leaf (4x throttle) | under 1 s | |

## Requests between agents
- **research to ml (R3):** (1) healthy and miner come from JMuBEN2 (Mendeley tgv3zb82nd), not JMuBEN. (2) JMuBEN and JMuBEN2 contain rotated and flipped copies: hash all 8 rotations and flips before grouping near-duplicates. (3) Uganda set has 102 zero-byte files and likely duplicates; drop empties and dedupe before using it as a held-out test. (4) BRACOL "brown leaf spot" is probably phoma but unconfirmed; check folder names before mapping, drop if unclear.
- **research to docs and content-voice (R3):** `facebook/mms-tts-kik` and NLLB-200 are CC BY-NC 4.0. Do not commit the weights; label Kikuyu audio and text as non-commercial in LANGUAGES.md and DATA_CARD.md. PlantDoc images are web-scraped: do not re-host them in the repo.
- **research to pitch and docs (R1):** problem statement extension figure: KASEP 2023 says the ratio "has not improved" and targets 1:600 by 2029; quote with "1 officer per 1,093 farm households vs FAO-recommended 1:400" (Odongo 2013/14, secondary, older). Not the Kilimo Trust X post. Check GSMA smartphone chart values by eye before using on screen.
- **research to geo (R1):** 3.0 kg cherry per tree confirmed but secondary and 2013/14; 1,300 trees per ha applies to traditional varieties only (Ruiru 11 is 2,500 to 3,300). Add that caveat in `kb/geo/REPORT.md`.
- **content-voice to engine (C1):** engine decide tests only use 0 or 3 unsure leaves and no `pre_long_rains` date. Add a test date in late February and unsure counts 1 and 2 so the real rules are exercised. Healthy plus 1 or 2 unsure leaves deliberately returns `ask_officer`, not `healthy_all`.
- **docs to engine (D1 review of PR #2 against Section 8), pass/fail gate risk, please fix before freeze:** (1) check results are saved on the phone even without main consent; either gate saving on consent or change the consent card wording with content-voice. (2) `sync.ts` photo upload expects public URLs; photos must stay private to the officer (signed URLs or private bucket). (3) PIN falls back to a weak hash on plain HTTP; acceptable on HTTPS only, say so in RESPONSIBLE_AI.md. (4) No separate OOD score: abstention relies on the `not_leaf` class plus threshold; docs now say so, add an OOD score only if ml has time. (5) Silent mock fallback when the model is missing: ui must show the mock badge.
- **docs to ui:** missing Kikuyu clips silently fall back to Swahili; show a small "Swahili" label when that happens.
- **ml to lead, content-voice (decision needed, affects the demo):** v2 threshold 0.985 accepts about 46% of Uganda phone-photo leaves (96% accuracy on those). With the rule `uncertain_gte: 3`, a 10-leaf check would give `too_many_unsure` about 97% of the time (binomial estimate, assumes independent leaves). Options: (A) keep the per-leaf threshold, change the rule to `uncertain_gte: 6` and decide on the confident leaves only (result in about 53% of checks); (B) threshold 0.691 (90% accepted accuracy, 79% coverage on Uganda calib) and keep `uncertain_gte: 3` (result in about 65% of checks); (C) both (result in about 99%). Lead recommendation: (A), because per-leaf errors are what mislead Noor, and the plot summary already shows unsure leaves separately. Arthur to choose.
- **ml to engine:** v2 parity: the e2e test "real model: parity samples match when present" passes with `app/public/model/*` and `app/ml/parity_samples/` copied onto the engine branch (run on the cloud VM, Chromium headless).
- **lead to master prompt:** Section 6.1 JMuBEN row is wrong (22,591 images are rust, cercospora, phoma only) and the Uganda count is 3,322 files, not 3,312. Fix in the next master prompt edit.

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 23:00: wave 1 of sub-agents started from a cloud agent (see `kb/SUBAGENTS.md`): R1 to R4. Engine work dropped here because PR #2 covers it. Local agents: do not start R1 to R4.
