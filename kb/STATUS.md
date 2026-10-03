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
| R1 | Problem evidence table | research | Sat 22:30 | todo | |
| R2 | Agronomy guidance | research | Sat 23:00 | todo | |
| R3 | Dataset facts and licences | research | Sat 23:00 | todo | |
| R4 | season.json | research | Sat 23:30 | todo | |
| M1 | Data download, manifest, dedupe, splits | ml | Sat 22:30 | todo | needs R3 (can start from ml.md list) |
| M2 | Train v1 | ml | Sun 00:30 | todo | |
| M3 | Calibrate, threshold, OOD | ml | Sun 01:00 | todo | |
| M4 | ONNX int8 export, parity, model.json | ml | Sun 01:30 | todo | |
| M5 | EVALUATION.md | ml | Sun 02:00 | todo | |
| E1 | Engine with mock model + hooks | engine | Sat 23:30 | todo | needs L1 |
| E2 | PWA offline caching | engine | Sun 00:30 | todo | |
| E3 | Real model integrated, parity in browser | engine | Sun 08:30 | todo | needs M4 |
| E4 | Engine tests incl. offline Playwright | engine | Sun 09:30 | todo | |
| U1 | Lovable project, routes, farmer flow with mocks | ui | Sat 23:30 | todo | |
| U2 | Officer dashboard, tables, seed data | ui | Sun 08:00 | todo | |
| U3 | Wire real engine hooks, publish live URL | ui | Sun 09:30 | todo | needs E1 |
| C1 | answers.json + rules.json | content-voice | Sat 23:00 | todo | needs R2 |
| C2 | Swahili + Kikuyu translations | content-voice | Sat 23:30 | todo | |
| C3 | Audio rendered (ElevenLabs, MMS) | content-voice | Sun 00:30 | todo | needs L2 |
| G1 | Real data: Sentinel-2 dry-season NDVI (Earth Search, SCL mask) and NASA POWER rainfall, Mathira West, Nyeri | geo | Sun 02:00 | done | 4 composites (Jan to mid Mar 2023 to 2026, 12 to 15 scenes each); rainfall 1991 to Sep 2026. NDVI kept, no cut |
| G2 | Synthetic registry (80 plots, 66 members) and deliveries with planted scenarios, labelled synthetic | geo | Sun 02:00 | done | Noor is OCC0412-2 (`drop_with_canopy_loss`) |
| G3 | Robust-z outlier model, reason codes, abstention; `public/geo/plots.geojson`, `outliers.json`, `ndvi_change.png` | geo | Sun 02:00 | done | 78 of 80 planted cases as expected, 0 false flags on 63 normal (synthetic). Contract `kb/geo/CONTRACT.md`, report `kb/geo/REPORT.md` |
| D1 | Doc skeletons | docs | Sat 22:30 | todo | |
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
- geo to lead: `kb/agents/geo.md`, `kb/research/EVIDENCE.md` and MASTER_PROMPT sections 3.4 and 3.5 were not in the repo when geo ran. Built from the task spec instead. Please add the geo paths (`app/geo/**`, `app/public/geo/**`, `kb/geo/**`) to `kb/OWNERSHIP.md`.
- geo to engine: please add a "Geo outputs" section to `kb/CONTRACTS.md` pointing to `kb/geo/CONTRACT.md`.
- geo to research: yield baseline (E3) used 3.0 kg cherry per tree, Nyeri, MOALF 2014 via Mugendi et al. 2015, and 1,300 trees per ha (Coffee Year Book 2022/23). Replace if E3 says otherwise.
- geo to ui: officer map reads `/geo/plots.geojson` and `/geo/outliers.json`; overlay `/geo/ndvi_change.png` with `overlay.bounds`. Show the synthetic tag. Rules in `kb/geo/CONTRACT.md`.

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 23:00: geo G1 to G3 done. Sentinel-2 and NASA POWER both working.
