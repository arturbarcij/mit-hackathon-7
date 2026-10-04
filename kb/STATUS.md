# Status board

Update your own rows only. Keep it short. Status: `todo`, `doing`, `blocked`, `done`. Times are CEST.

**Deadline:** Sun 4 Oct 15:00. **Freeze and submit:** 13:30. **Cut line:** 09:30 (no new features after this; if the real model is not in the app, ship what works).

## Board
| ID | Task | Owner | Target | Status | Blocker / note |
|---|---|---|---|---|---|
| L1 | Connect GitHub in Lovable, clone repo into `MIT_Hackathon_7/app` | Arthur | Sat 21:30 | todo | |
| L2 | Set up local build-time tools | Arthur | Sat 21:30 | todo | |
| L3 | Find a Swahili speaker to review answers (10 min, Sun morning) | Arthur | Sun 09:00 | todo | |
| L4 | Android phone for demo (or emulation, stated) | Arthur | Sun 10:00 | todo | |
| R1 | Problem evidence table | research | Sat 22:30 | done | kb/research/EVIDENCE.md. 9 items. NOT FOUND: county-level coverage, Kikuyu speaker count, cooperative member counts. Use 1:1,380 (MoALD 2025), not the "5,000 officers" figure. |
| R2 | Agronomy guidance | research | Sat 23:00 | done | kb/research/GUIDANCE.md. Rust is well sourced (Kenya). Phoma: NOT FOUND. Leaf miner and cercospora: non-Kenyan sources only. No Kenyan incidence threshold: mark all cut-offs "assumption, officer to confirm". No brands or doses. |
| R3 | Dataset facts and licences | research | Sat 23:00 | done | kb/research/DATASETS.md. JMuBEN has only rust, cercospora, phoma; healthy and miner are in JMuBEN2. See Requests. |
| R4 | season.json | research | Sat 23:30 | done | kb/research/season.json. NASA POWER 1991-2020, one point, modelled. Spray windows from the Kenyan review. CHIRPS not done. |
| R5 | Gap fill: phoma, brown eye spot, leaf miner (GUIDANCE sections 2 to 4) | research | Sat 23:30 | done | Pass 3: CABI still "No access" or empty. KALRO KEEP is a JS shell. Leaf miner remains the only Kenyan-sourced gap disease (Infonet). Phoma and brown eye spot: secondary non-Kenyan only. Raw: kb/research/raw/gaps/ |
| R6 | Wild test set (CC photos, wild_set.csv, data_raw/wild/) | research | Sun 00:30 | done | 254 images in data_raw/wild/ (188 iNaturalist, 66 Commons). 58 rust hints. Flickr NOT FOUND (Bright Data KYC). Manifest kb/research/wild_set.csv. Labels are hints; many arabica shots are not close-up leaves. |
| R7 | Swahili glossary | research | Sun 01:30 | done | kb/research/swahili_glossary.md. Kenyan: kutu ya majani ya kahawa, ugonjwa wa matunda ya kahawa (Umoja); magonjwa ya kahawa (Radio Jambo). Phoma and leaf miner Swahili still NOT FOUND. Reviewer (L3) must confirm. |
| R8 | Prices (optional) | research | Sun 02:30 | done | kb/research/prices.json. NCE USD/50kg sales 30 to 41 from PDFs; Sale 42 from The Standard (Sh44,462 / 50 kg, 17,765 bags, Sh841.3m). AFA county prices NOT FOUND. |
| R9 | Prior art: scrape AI Repository agriculture cases (kb/prompts/10_prior_art.md) | research | Sun 00:30 | todo | PRIOR_ART.md started by Claude |
| M1 | Data download, manifest, dedupe, splits | ml | Sat 22:30 | done | 63,687 files. pHash: 1,244,500 near-dup pairs, 24,236 clusters. After cap: train 31,477 / val 6,764 / test 6,714. Uganda 424 held-out only. RoCoLe not on disk yet. |
| M2 | Train v1 | ml | Sun 00:30 | doing | run `ml/runs/20261003_211853`, CUDA 4060, full fine-tune (not head-only). Epoch 1 in progress. |
| M3 | Calibrate, threshold, OOD | ml | Sun 01:00 | todo | bundled at the end of train.py |
| M4 | ONNX int8 export, parity, model.json | ml | Sun 01:30 | todo | |
| M5 | EVALUATION.md | ml | Sun 02:00 | todo | |
| E1 | Engine with mock model + hooks | engine | Sat 23:30 | done | Mock labels, quality gate, rules, referral, IndexedDB, farmer flow and officer queue in the app. Real ONNX still waits on M4. |
| E2 | PWA offline caching | engine | Sun 00:30 | done | vite-plugin-pwa. Precache 348 KiB before model and audio. Production preview reloaded from the service worker while Chrome DevTools was set to offline. |
| E3 | Real model integrated, parity in browser | engine | Sun 08:30 | todo | needs M4 |
| E4 | Engine tests incl. offline Playwright | engine | Sun 09:30 | todo | |
| EC1 | PWA offline proof on a Lovable mirror (TanStack Start, ort wasm, Playwright offline), bundle size | engine-cowork (Claude Cowork) | Sun 00:45 | doing | recipe for E2/E4 lands in kb/engine-cowork/pwa/; never edits app/src/engine or app/tests |
| EC2 | Preprocessing parity harness: train.py eval_transform reproduced in TS, ort-web vs Python onnxruntime, ort wasm size | engine-cowork (Claude Cowork) | Sun 00:45 | doing | kb/engine-cowork/parity/; feeds E3 |
| EC3 | Contract test suite for CONTRACTS.md, Lovable UI compatibility audit, L3 prompt draft | engine-cowork (Claude Cowork) | Sun 00:45 | doing | kb/engine-cowork/conformance/; feeds E1 and E4 |
| U1 | Lovable project, routes, farmer flow with mocks | ui | Sat 23:30 | done | project 4619dfd1-32ea-4daa-aaf8-89b51321cbe1, workspace MIT HACKATHON 7 (workspace_01m41rmrvcea8v9c7rxmerc4ar); editor https://lovable.dev/projects/4619dfd1-32ea-4daa-aaf8-89b51321cbe1 ; knowledge set |
| U0 | Connect Lovable to GitHub (new repo jani-web), clone into MIT_Hackathon_7/web | Arthur | Sat 23:15 | todo | Lovable creates a new repo; web/ is git-ignored by the root repo |
| U2 | Officer dashboard, tables, seed data, outlier map (L2 sent) | ui | Sun 00:15 | doing | message umsg_01m41rsrzhf1brge8fntzkh6t1 |
| U3 | Wire real engine hooks, publish live URL | ui | Sun 09:30 | todo | needs E1 |
| C1 | answers.json + rules.json | content-voice | Sat 23:00 | done | reviewed against GUIDANCE.md; QA content checks pass; thresholds all flagged assumption |
| C2 | Swahili + Kikuyu translations | content-voice | Sat 23:30 | partial | Swahili draft only (Gemini check not run). Kikuyu 8 core drafted by Claude, low confidence, not native-reviewed; see kb/content/REVIEW_LOG.md |
| C3 | Audio rendered (ElevenLabs, MMS) | content-voice | Sun 00:30 | todo | needs L2 |
| D1 | Doc skeletons | docs | Sat 22:30 | done | Skeletons and research-derived sections filled. Open TODO(owner) and [PENDING: ml] markers are in app/README.md and app/docs/*. |
| D2 | DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION | docs | Sun 10:30 | todo | needs R1, R3, M5 |
| D3 | README final | docs | Sun 11:00 | todo | |
| G1 | Synthetic plots + Sentinel-2 STAC working | geo | Sat 23:45 | done | 80 synthetic plots, 63 members, on perennial-looking land at Mathira West, Nyeri. Earth Search STAC, tile 37MBV, SCL mask |
| G2 | NDVI per plot per dry season | geo | Sun 01:15 | done | 4 dry-season composites (1 Jan to 15 Mar, 2023 to 2026, 12 to 15 scenes each) plus a wet-season 2025 composite. No cut needed |
| G3 | Deliveries, rainfall, outlier model, outputs | geo | Sun 01:45 | done | `public/geo/plots.geojson`, `outliers.json`, `ndvi_change.png`. 78 of 80 planted cases as expected; 30 seeds: 98% match, 0.27 false outliers per 63 normal plots (synthetic). Contract `kb/geo/CONTRACT.md`, report `kb/geo/REPORT.md` |
| G3b | Rain onset and season windows from NASA POWER | geo | Sun 01:45 | done | `app/geo/data/season_support.json`. Short-rains onset median 19 Oct, sd 17 days, before 15 Oct in 47% of years |
| G3c | Officer visit plan (ranked, tiers, 8-stop route) and 18 synthetic seed referrals | geo | Sun 01:45 | done | `public/geo/visit_plan.json`, `referrals_seed.json`. Top 8 hold 93% of planted problems over 30 seeds vs 15% by chance (synthetic) |
| G4 | Officer map renders outliers + referrals | ui | Sun 09:00 | todo | Reference map in `app/public/geo/map.html` (fallback). G3 done: see `kb/geo/CONTRACT.md`, also `visit_plan.json` and `referrals_seed.json` |
| Q1 | QA harness built (`app/qa`) | qa (Claude) | Sat 22:00 | done | run: `python -m qa.run` from app/ |
| Q2 | QA runs at 01:00, 08:30, 09:30, 11:00, 12:30 | qa | Sun | todo | see kb/agents/qa.md |
| J1 | Judge passes at 01:30, 09:45, 12:00 | judge | Sun | todo | see kb/agents/judge.md |
| X1 | Red-team passes at 02:00, 09:45, 12:00 | redteam | Sun | todo | see kb/agents/redteam.md; zero open blockers at the end |
| PT1 | Problem statement + three scripts + coverage checklist | pitch | Sat 23:30 | done | Draft v1 of the three scripts. All three within 55 s and 2.5 words/s. Open: team names, map not demoable yet (G1 to G4 todo), numbers PENDING ml. |
| PT2 | ffprobe checks + submission form text | pitch | Sun 13:00 | todo | needs V1 |
| V1 | Three videos recorded and checked | Arthur (pitch later) | Sun 12:45 | todo | |
| S1 | Submit, save confirmation, make repo public | Arthur | Sun 13:30 | todo | |
| AF1 | Concurrent Claude review framework (`app/backend/agent_framework`) | lead | Sun 10:45 | done | Static check: pass 0, fail 20, missing 6, 22 blockers. The tree is still the Vite starter. Claude wave did not run in this environment. |
| AF2 | Orchestrate audit seats in a DAG (`app/backend/agent_framework`) | lead | Sun 11:00 | done | Static check: pass 0, fail 20, missing 6, 22 blockers. Claude wave did not run in this environment. |

## Lane rhythm (one person running four lanes)
| Lane | Machine | Runs alone for | Check it |
|---|---|---|---|
| ML training and export | laptop GPU | 45 to 90 min per run | every 45 min |
| Engine (offline logic) | Cursor agent, background | 20 to 40 min per task | when it reports |
| UI | Lovable | 10 to 20 min per turn | when the preview rebuilds |
| Content, docs, QA, briefs | Claude (cloud session) | continuous | when handed over |
Rules: Arthur dispatches and reviews, never codes by hand. The next prompt is ready before the current one finishes. Anything over 10 minutes runs in the background. This board is the queue; DECISIONS.md stops re-deciding at 3 am.

## Measured budgets
| Item | Target | Measured |
|---|---|---|
| leaf.onnx | at most 5 MB | not in this copy |
| Total offline precache | at most 15 MB | 348 KiB (production build, no model, no audio) |
| Audio total | at most 4 MB | 0 (clips not rendered) |
| Inference per leaf (4x throttle) | under 1 s | not measured: no ONNX file |

## Requests between agents
- engine-cowork to engine: Cowork runs three helper lanes in parallel with you (EC1 to EC3). They write only to kb/engine-cowork/** and never touch app/src/engine or app/tests. Adopt what helps: a proven PWA recipe for Lovable's TanStack Start stack, a TS preprocessing module matching train.py eval_transform (Resize(224) on the shorter side with PIL bilinear, centre crop, ImageNet normalisation), and a vitest suite that checks any engine against CONTRACTS.md. Heads-up: Lovable's mock engine drifts from CONTRACTS (summarisePlot semantics, free-text referral instead of JANI1, hard-coded cards instead of rules.json and answers.json).
- research to lead / ml: MASTER_PROMPT section 6.1 needs correcting. JMuBEN (22,591) holds only rust, cercospora and phoma. Healthy (18,984) and miner (16,978) are in the separate JMuBEN2 record (tgv3zb82nd). Uganda set (stated 3,312, 3,322 files) is augmented, so it is not a clean held-out set. BRACOL has no Phoma class. RoCoLe: 4 images per plant, split by plant. Details in kb/research/DATASETS.md.
- research to content-voice: no Kenyan source for any incidence threshold; treat every rules.json cut-off as "assumption, officer to confirm". Phoma and leaf miner treatment: answer is "ask the officer".
- research to docs: Meta MMS-TTS and NLLB are CC-BY-NC-4.0 (non-commercial). Say so in DATA_CARD, LANGUAGES and RESPONSIBLE_AI.
- research to ml: wild field set ready. 254 CC photos in `data_raw/wild/` (manifest `kb/research/wild_set.csv`). 58 rust (iNaturalist Hemileia, research grade); 196 Coffea arabica / Commons, label_hint only, many are not close-up leaves. 151 are CC BY-NC. Flickr failed. Use as a messy field test, not as train. See DATASETS.md section 6.
- research to content-voice: Kenyan Swahili now attested for rust as "kutu ya majani ya kahawa" and CBD as "ugonjwa wa matunda ya kahawa" (Umoja listing, S47). Prefer those over Tanzanian "chulebuni" until L3 reviews. Phoma and leaf miner still have no Swahili term.
- qa to lead: the challenge PDF was untracked. Agent briefs in `kb/` stay in the public tree on purpose.
- qa to docs: README.md:91-95 dataset table has sizes and counts with no `(S##)` tag. Add the source tag per row. DATA_CARD.md:24 (P2 accuracy figures) and :51 (58,550 count) and REPLICATION.md:3 need a tag or "our calculation".
- qa to engine / content-voice / ml: `[PENDING]` rows in README, EVALUATION and ARCHITECTURE (bundle, audio, latency) stay FAIL until measured. Not a harness fault. Fill with measured values and the device used.
- qa harness note (fixed, my lane): the sources check accepted only `[S07]`; docs use `(S07)`. Now accepts both. No check was relaxed otherwise.

- cowork-claude to research / content-voice / docs (Sat 23:40): independent cross-check in kb/research/raw/crosscheck_cowork_20261003.md. Confirms EVIDENCE/GUIDANCE/DATASETS. Upgrades: CA 4G 97.3% (Jun 2025) and smartphones 63.7% of phones (Mar 2026); KMSA OND 2026 onset forecast 2nd to 3rd week Oct for the coffee counties (why-now); out-of-bundle worst case KSh 64.5 for 15 MB. For C3: ElevenLabs Swahili needs model eleven_v3 (Multilingual v2 and Flash v2.5 do not do Swahili). Batian is intermediate rust resistance, never "resistant".

- geo to lead: `kb/agents/geo.md` and MASTER_PROMPT sections 3.4 and 3.5 are not on `main`, so geo built from the task text. If they differ from `kb/geo/CONTRACT.md`, tell geo which wins. Please add `app/geo/**`, `app/public/geo/**`, `kb/geo/**` to `kb/OWNERSHIP.md`.
- geo to engine: please add a "Geo outputs" section to `kb/CONTRACTS.md` pointing to `kb/geo/CONTRACT.md`.
- geo to research: NASA POWER gives short-rains onset median 19 Oct, sd 17 days, onset by 15 Oct in 47% of years and by 1 Oct in 13% (simplified rule, assumption). A fixed "mid October" window is right about half the time. Cross-check against `season.json` and the KMSA OND forecast. Details and suggested windows in `app/geo/data/season_support.json`.
- geo to lead and engine: because onset varies by weeks, consider one yes/no question in the farmer flow ("have the rains started?") feeding `seasonWindow`. The person answers; the tool does not guess. Your call.
- geo to engine and content-voice: `kb/agents/content-voice.md` puts `distinct_problems_gte: 2` before the rust rule, but the contract example `JANI1 ... R:6 ... L:1 ... A:rust_high_pre_rains` has two problems. Rule order and example disagree. Geo seeds follow the rule order and give Noor 6 rust only.
- geo to ui: officer map reads `/geo/plots.geojson`, `/geo/outliers.json`, `/geo/visit_plan.json` (ranked plots, route, signal text) and `/geo/referrals_seed.json` (18 synthetic referrals matching the `referrals` table plus `sms`, `lon`, `lat`). Overlay `/geo/ndvi_change.png` with `overlay.bounds`. Always show a ranked plot with its `signals`. Mark everything synthetic. Rules in `kb/geo/CONTRACT.md`.

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 21:25: Bright Data MCP configured; research agent started in Cursor.
- Sat (late): research finished R1 to R4 in kb/research/ (EVIDENCE, GUIDANCE, DATASETS, season.json, sources.json with 40 sources).
- Sat 21:55: QA harness built and tested on fixtures; qa agent brief added. Workflow file waits in kb/github-workflows/qa.yml for Arthur to move to .github/workflows/.
- Sat 22:15: decision_matrix check added (enumerates 3,510 plot summaries through the rules; officer-reviewable table in app/qa/decision_matrix.md).
- Sat 22:30: research delivered (EVIDENCE, GUIDANCE, DATASETS, season.json, sources.json). ml brief and MASTER_PROMPT corrected from it.
- Sat 22:45: geo lane added (outlier map). MASTER_PROMPT 3.4 and 3.5.
- Sat 23:05: Lovable project created (L1 prompt), project knowledge set. Prompts for every lane in kb/prompts/. sync_to_web.py written (app/ assets to web/).
- Sat 23:20: PRIOR_ART.md: Nuru multi-leaf evidence, KIAMIS registry (6.5m farmers), WB AI-for-agriculture report quotes, AI Repository entries. MASTER_PROMPT 3.2 updated.
- Sat 23:35: Lovable project moved to workspace MIT HACKATHON 7 by Arthur; L1 farmer flow done; L2 officer dashboard + outlier map sent.
- Sat 23:15: ml. JMuBEN+JMuBEN2 extracted. Env `jani` + CUDA 4060 confirmed. Scripts written (`manifest.py`, `train.py`, `export.py`, `eval.py`). Manifest hashing started. Uganda/RoCoLe will stay held-out and are not in the training loaders.
- Sat 23:19: ml M1 done. manifest.csv written. 24,236 pHash clusters, 18,308 healthy/miner images capped out. Train started on CUDA (run 20261003_211853).
- Sat (late): content-voice reviewed answers.json and rules.json, tightened cards, added 8 Kikuyu draft entries (pending native review), wrote kb/content/REVIEW_LOG.md with Swahili checklist. Audio not rendered (C3 still todo).
- Sat 23:50: pitch PT1 draft: PROBLEM_STATEMENT, three video scripts with draft SRTs, SUBMISSION_FORM skeleton. 75% quoted as a review figure; 1:1,380 used. Map beat in Video 2 and 3 is conditional on G4. Questions for Arthur listed in the pitch reply.
- Sat 23:15+: research pass 2 (R5 to R8). GUIDANCE 2 to 4 re-checked (CABI still closed). Wild set 254 photos. Swahili glossary with two Kenyan pages. prices.json NCE 30 to 41 plus Sale 42 from The Standard. AFA county prices NOT FOUND.
- Sat (late): docs: D1 done. app/README.md, app/docs/{DATA_CARD,RESPONSIBLE_AI,LANGUAGES,REPLICATION,ARCHITECTURE,REQUIREMENTS,EVALUATION}.md, app/LICENSE, app/src/content/sources.json created; ml numbers left as [PENDING: ml].
- Sat 23:20: Cowork (Claude) started engine-cowork helper lanes EC1 to EC3 in parallel with the Cursor engine agent; outputs in kb/engine-cowork/.
- Sun 00:20: Claude (lead). Sent Lovable follow-up umsg_01m41tcrs5fw281bgepzf47hgx (answers.json text per language, 160-char referral with member/plot/date, remove auto officer role, insert cap, synthetic badges, publish). PWA left to engine-cowork. Untracked the challenge PDF and ignored *.pdf; QA secrets_git now passes. PDF is still in the initial commit history and kb/ is tracked: decide before making the repo public. Gemini prompt: kb/prompts/09b_gemini_crosscheck.md.
- Sun 00:45: engine shipped the offline farmer flow with a mock model, fixed answer bank, rule table, referral SMS, and a simulated officer queue. No trained model and no voice clips yet.
- Sun 01:10: browser pass on the production preview at 360px. Fill-10 summary was 6 rust and 1 unsure, card rust_high_pre_rains, referral JANI1 under 160 characters, blur sample could not be kept, offline reload served the app. Officer seed now inserts the syn-01 to syn-16 rows even when a farmer check is already marked synthetic. Chrome DevTools offline does not change navigator.onLine, so the header pill stayed "On the network".
- Sun (early): research verified and shipped kb/research. JSON valid, all cited S-ids defined, wild set 254 files present with no ND licence, 176 price rows with KES derivation checked, pass-2 quotes match saved pages. kb/research/raw/ (third-party page copies) is git-ignored and stays local. raw/crosscheck_cowork_20261003.md lists upgrades (CA 4G 97.3%, KMSA OND onset, ElevenLabs v3 Swahili) not yet merged into EVIDENCE.
- Sat 23:50: geo: G1 to G3 done, plus season/rain-onset analysis (G3b) and officer visit plan with seed referrals (G3c). Real Sentinel-2 and NASA POWER both working.
- Sat 23:55: geo: unit tests (18), `classify()` extracted, standalone officer map `public/geo/map.html` checked in headless Chrome.
- Sun 10:40: lead. Agent framework added at `app/backend/agent_framework`. Roster: qa, redteam, judge, engine, ui, content, docs, ml. They share one evidence pack and return JSON. Static probes do not treat `kb/STATUS.md` or `kb/research` as proof that `app/` contains the product.
- Sun 10:45: lead. Static check of this checkout: pass 0, fail 20, missing 6. Blockers include no PWA, no model, no answer bank, no officer route, Vite starter still in `app/src/App.tsx`. Claude reviewers were not called.
- Sun 11:00: lead. Orchestrator schedules the audit DAG and writes `plan.json`. Static check: pass 0, fail 20, missing 6, 22 blockers. Claude wave did not run in this environment.
