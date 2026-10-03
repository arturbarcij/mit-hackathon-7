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
| R1 | Problem evidence table | research | Sat 22:30 | doing | cloud sub-agent, branch `cursor/wave1-research-engine-82ab` |
| R2 | Agronomy guidance | research | Sat 23:00 | doing | cloud sub-agent, same branch |
| R3 | Dataset facts and licences | research | Sat 23:00 | doing | cloud sub-agent, same branch |
| R4 | season.json | research | Sat 23:30 | doing | cloud sub-agent, same branch |
| M1 | Data download, manifest, dedupe, splits | ml | Sat 22:30 | doing | cloud sub-agent, branch `cursor/wave1-research-engine-82ab`; also a CPU v1 training run as fallback for M2 |
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
(none yet)

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 23:00: wave 1 of sub-agents started from a cloud agent (see `kb/SUBAGENTS.md`): R1 to R4. Engine work dropped here because PR #2 covers it. Local agents: do not start R1 to R4.
