# Jani app check

Checked at 2026-10-04 09:00 UTC.

The static matrix reads the git tree. It does not trust the status board.

## Orchestration

Every seat is an audit. Builder seats report gaps and do not edit owned product paths. This orchestrator does not generate the product.

research before content and docs; ml before engine; content and engine before ui; research, ml, engine, ui, content, and docs before qa; qa before redteam and judge. An edge is kept only when both seats are selected.

| Seat | Kind | State | After |
|---|---|---|---|
| research | builder | blocked | none |
| ml | builder | blocked | none |
| engine | builder | blocked | ml |
| ui | builder | blocked | content, engine |
| content | builder | blocked | research |
| docs | builder | blocked | research |
| qa | reviewer | blocked | research, ml, engine, ui, content, docs |
| redteam | reviewer | blocked | qa |
| judge | reviewer | blocked | qa |

Edges:

- research -> content
- research -> docs
- ml -> engine
- content -> ui
- engine -> ui
- research -> qa
- ml -> qa
- engine -> qa
- ui -> qa
- content -> qa
- docs -> qa
- qa -> redteam
- qa -> judge

ANTHROPIC_API_KEY is not set. Add it to app/backend/.env (git-ignored) or the environment. The file is not in this checkout.

## Requirement matrix

Pass 0, fail 20, missing 6. Blockers 22.

| ID | Status | Severity | Claim | Evidence |
|---|---|---|---|---|
| R1 | fail | blocker | The app is not set up as an installable PWA on a phone the household already has. | app/package.json has no vite-plugin-pwa and app/public/manifest.webmanifest is absent |
| R2 | fail | blocker | Nothing caches the app, model, audio, or rules for offline use. | no service worker, workbox, or vite-plugin-pwa reference |
| R3 | fail | blocker | The on-device model file is not in the tree. | app/public/model/leaf.onnx |
| R4 | fail | blocker | There is no Swahili answer bank. | app/src/content/answers.json |
| R5 | fail | blocker | No Kikuyu answer text or audio is in the app. | app/src/content and app/public/audio/kik |
| G1 | fail | blocker | The farmer cannot choose act, wait, or ask the officer. | app/src has no decision controls |
| G2 | missing | blocker | There is no referral SMS path to review for auto-send. | app/src |
| G3 | fail | blocker | The client does not call a model API, but farmer-facing text is not loaded from a fixed answer bank. | app/src/App.tsx is hard-coded; app/src/content/answers.json is absent |
| P1 | fail | blocker | There is no fail-safe that says not sure and asks a person. | app/src and app/src/content |
| P2 | fail | blocker | The responsible-AI document is missing from the app docs. | app/docs/RESPONSIBLE_AI.md |
| D1 | fail | blocker | Cited data sources are not in the app docs. Notes under kb/research do not meet this row. | app/docs/DATA_CARD.md |
| D2 | fail | blocker | The README is not the Jani problem statement with source, year, and country. | app/README.md |
| D3 | fail | blocker | Build data is not recorded with source, licence, and size. | app/docs/DATA_CARD.md |
| D4 | fail | blocker | The app docs do not state what the data does not cover. | app/docs/DATA_CARD.md |
| D5 | missing | major | No synthetic officer records are in the app to check the tag. | app/ |
| W1 | fail | blocker | The running UI is the Vite starter, not a leaf-check prototype. | app/src/App.tsx contains the starter counter |
| W2 | fail | blocker | The README does not explain the model or why a simpler tool fails. | app/README.md |
| W3 | fail | blocker | There is no evaluation write-up with a named test set. | app/docs/EVALUATION.md |
| B1 | fail | blocker | The one agricultural decision is not implemented. | app/src |
| B2 | fail | blocker | There is no officer dashboard route. | app/src |
| S1 | missing | blocker | No live project URL is recorded in the README. | app/README.md |
| S2 | fail | major | There is no licence file. | app/LICENSE |
| S3 | missing | major | No MP4 or MOV video is in the tree. | repo |
| S4 | missing | major | No video coverage checklist is in the tree. | video/COVERAGE.md |
| S5 | missing | note | No submission confirmation is in the tree. | repo |
| J1 | fail | major | There is no replication note with a worked swap example. | app/docs/REPLICATION.md |
| UI0 | fail | blocker | app/src/App.tsx is the Vite starter: a counter, hero art, and links to Vite and React. | app/src/App.tsx |
| TREE | fail | blocker | Expected product paths are absent: app/src/engine, app/src/pages, app/src/content/answers.json, app/src/content/rules.json, app/src/content/season.json, app/public/model/model.json, app/docs/ARCHITECTURE.md, app/docs/LANGUAGES.md, app/ml. | repo tree |

## Agent calls

ANTHROPIC_API_KEY is not set. Add it to app/backend/.env (git-ignored) or the environment. The file is not in this checkout.

The static matrix above is the check that ran.
No Claude output was invented.
Audit seats do not edit the app. Builder seats report gaps. Fixes stay with the path owner.
