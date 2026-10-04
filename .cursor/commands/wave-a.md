# Wave A: build in parallel

Read `kb/WORKFLOW.md` sections 2 and 4 first. Then, in ONE message, launch these as parallel `Task` calls with `run_in_background: true` (subagent_type in brackets). Each prompt must start with "Follow kb/agents/<name>.md. Edit only your owned paths. Update your rows in kb/STATUS.md." and end with "When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."

1. [ml] Tasks M1 then M2. Download with `app/ml/download.py` into `data_raw/` (never commit it), build manifest, near-duplicate hashing before split, train v1. Run long jobs in the background and log inside `app/ml/runs/`. Use `kb/research/DATASETS.md` as the data source list; note the JMuBEN vs JMuBEN2 correction.
2. [content-voice] Tasks C1 and C2. Use `kb/research/GUIDANCE.md` and `season.json`. No brands, no doses. Mark every threshold "assumption, officer to confirm". Do not render audio yet.
3. [engine] Tasks E1 and E2 start. Mock model, hooks, quality gate stub, rule decision, IndexedDB, referral SMS, against `kb/CONTRACTS.md`.
4. [ui] Task U1. Write the Lovable prompts for the farmer flow; do not edit `app/src/pages/**` directly.
5. [docs] Task D1. Skeletons for README, DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION, ARCHITECTURE, REQUIREMENTS using `kb/research/EVIDENCE.md` and `DATASETS.md`. Missing numbers are `[PENDING: owner]`.
6. [pitch] Task PT1. Problem statement and three draft scripts from `kb/research/EVIDENCE.md`.
7. [research] On call. Only the optional Tier 3 price reference, and only if nothing else is requested in kb/STATUS.md.

After launching, report which agents are running, then stop. Do not do their work yourself.
