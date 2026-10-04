# Judge pass 1 (overnight runner): Sun 4 Oct 2026, 01:30 CEST

Build judged: integrated tree `master` at 24b03a7 (engine a22f9bc, content d6d4b63, ui 4105b56), the static Vite PWA in `app/`. Read: `app/README.md`, `app/docs/*`, `kb/pitch/*` (laptop copy), `kb/EDGE_PLAN.md` sections 1 to 5, `kb/MASTER_PROMPT.md` 2.4 to 2.9, `app/qa/prompts/judge.md`. Ran: `PORT=4711 npm run e2e` (PASS), `python -m qa.run` (4 FAIL), my own Playwright probe in Swahili with 20 dataset photos, and a rules probe with fewer than 10 leaves. The Lovable live URL (https://jani-farm-assist.lovable.app) could not be reached from the cloud (egress 403), so the officer side is not scored from use.

Previous judge pass: `kb/judge/20261003_2355.md` (50/100). Fixes from it that landed: real model in the browser, offline proof, sheet gate with `retake_on_page`, merged farmer labels (4 tiles), synthetic flags on `public/geo/outliers.json`, demo SMS number labelled. Fixes that did not land: every docs fix (review claims, MASTER_PROMPT citations, Uganda n, problem statement, PIN and IndexedDB wording).

**Verdict in one line:** the build is now real and the fail-safe is real, but a judge who opens it can only ever see "not sure, ask the officer", the docs still read as a Saturday draft with 86 TODO or PENDING markers, and two gate holes remain. **56.5 / 100. Gate: FAIL as it stands, fixable in under 90 minutes.**

## 1. Score table

| Criterion | Weight | Score /10 | Justification (file, line or measurement) |
|---|---|---|---|
| Built solution, Small AI fidelity | 25% | 5 | For: `npm run e2e` PASS at 360 x 740: 25 files precached, offline reload, the real `leaf.onnx` v1 (3,077,051 bytes, fp16) runs in onnxruntime-web with no mock badge, act / wait / ask, `sms:` composer only on tap. Against: (1) no live URL for this build (`README.md:5` "TODO(ui)"); (2) nothing a judge can feed it gives a reading: all 12 bundled samples come back `not_a_leaf`, and in my probe 2 BRACOL whole leaves on white gave `unsure` (0.389, 0.332), 2 Uganda photos and 6 wild photos failed the sheet gate, and 10 JMuBEN crops failed `too_small`. 20 of 20 photos ended in `too_many_unsure`; (3) zero audio clips (`public/audio` absent), so every speaker button depends on a phone TTS voice for Swahili that most Android phones do not have offline; (4) officer dashboard is not in this build (README section 10 says `/officer` exists in `npm run dev`: it does not); (5) not run on a phone. |
| Development relevance and impact | 20% | 7 | Noor's week (`README.md:19-29`) fits the brief: weekend smartphone, phone at the house, SMS on the basic phone, one decision. Referral carries member and plot (`JANI1 M:OCC0412 P:P07 ...`, 86 chars). Against: `README.md:13` still says she "will know which coffee rows have leaf rust"; the corrected sentence is in `kb/pitch/PROBLEM_STATEMENT.md:7`. |
| Data grounding | 15% | 6 | `DATA_CARD.md` section 2 and 3 are specific (name, source, licence, size, gaps). Synthetic geo data is now flagged (`outliers.json`: `"ndvi_source": "synthetic"`, `"rainfall.synthetic": true`). Against: 10 open markers in `DATA_CARD.md` (lines 46-48, 53, 74, 100, 110, 119-120) although the ml numbers exist; `README.md` section 7 lists the Uganda set as 3,322 files "Test only" while `EVALUATION.md` scored 424 healthy-only images; RoCoLe listed as a test set and "NOT RUN"; 12 citations of `MASTER_PROMPT` as a source, which a judge cannot open. |
| Evidence it works | 15% | 4 | `EVALUATION.md` names every test set and shows the bad number (Uganda healthy slice 0.017). That earns trust. But the strongest evidence the team owns is not in any judge-facing file: EDGE_PLAN section 4 (BRACOL test coverage 54% with 90% selective accuracy; field set 61% confidently wrong before the gate, 0.6% after; 4,000 simulated plots per row with 0% spray advice on healthy plots and 0% all-clear on rusty plots). `README.md` section 8 and section 5 are all `[PENDING]`; `REQUIREMENTS.md` 26 of 26 `todo`; `check_parity` 9/10; no fresh phone photo has been through the app. |
| Clarity, design, inclusivity, AI value | 15% | 6 | The UI is clean and calm: one action per screen, large targets, icons, four count tiles, Swahili text throughout (screens checked in Swahili). The "why not a simpler tool" table (`README.md:41-46`) is the right answer. Against: with every run ending in "not sure", the AI's value is invisible in the demo, and a judge can fairly ask what the model adds; speakers are silent; header badges stay in English ("Works offline") on Swahili screens; Swahili text is an unreviewed Claude draft but is shown with no tag (`strings.ts:139` tags only `machine`, Swahili status is `draft`). |
| Scalability, replicability, what next | 10% | 6 | `REPLICATION.md` names swappable parts and owners, checks the brief's preconditions and gives an honest cocoa plan; the engine really is content-driven (`rules.json`, `answers.json`, `model.json`). Against: 8 open markers in `REPLICATION.md`; AgriConnect still `TODO(research)`; the KIAMIS and KPCU lines from EDGE_PLAN move 10 are not in README. |

## 2. Weighted total

| Criterion | Weight | Score | Points |
|---|---:|---:|---:|
| Built solution | 25 | 5 | 12.5 |
| Relevance and impact | 20 | 7 | 14.0 |
| Data grounding | 15 | 6 | 9.0 |
| Evidence it works | 15 | 4 | 6.0 |
| Clarity and AI value | 15 | 6 | 9.0 |
| Scalability | 10 | 6 | 6.0 |
| **Total** | 100 | | **56.5** |

Ceiling if the five fixes in section 6 land by 13:30: built 7, relevance 8, data 8, evidence 7, clarity 7, scale 7. That gives 17.5 + 16 + 12 + 10.5 + 10.5 + 7 = **73.5**.

## 3. Hard rules check

| Rule | Verdict | Evidence |
|---|---|---|
| Runs on a device the user has | Pass (emulated) | PWA at 360 x 740 in Chromium; no real Android run yet |
| Core feature offline | Pass | e2e: offline reload, full sample plot, referral, history |
| Small model | Pass | `leaf.onnx` 2.9 MB (cap 5 MB). Bundle 18.4 MB raw, about 7.3 MB gzip, over the team's own 15 MB target (QA `budgets:bundle_size` FAIL); not a brief rule |
| Named local language | Pass, weak | Swahili text on every screen; Kikuyu on 7 cards with a machine tag. No voice at all. Swahili is unreviewed |
| Human decides | Pass | Nothing pre-selected on the decision screen; SMS opens only on "Send SMS"; the user presses send in the SMS app |
| No hallucination | Pass, one false fixed line | No runtime generation (`client_clean:dist` PASS). But `healthy_all.not_sure` says "We only checked 10 leaves" for any n (see B1) |
| Data sources cited | Pass, untidy | `sources:*` PASS except `EVALUATION.md:16-19`; MASTER_PROMPT used as a citation 12 times |
| Synthetic labelled | Pass | Geo flags fixed; "Demo number, not a real cooperative line" on the referral screen |

## 4. Responsible AI gate: FAIL as it stands

Deciding sentence: **with fewer than 10 photos the app gives definitive answers, including "No leaf problem seen" on a single leaf with the false line "We only checked 10 leaves", and the gate document claims human review of answers and Swahili audio that never happened.**

What already counts towards a pass, and is strong: the fail-safe demonstrably fires (20 of 20 unreadable photos went to `too_many_unsure` and a referral); the sheet gate turns field photos into a retake card; EDGE_PLAN's plot simulation shows no spray advice on healthy plots and no all-clear on rusty plots; act / wait / ask with nothing pre-selected; nothing sends without two taps; cercospora, phoma and miner are never named to the farmer; no product or dose anywhere in `answers.json`.

## 5. Blockers

**B1. Definitive answers on fewer than 10 leaves (fail-safe hole).**
- Where: `app/src/pages/Capture.tsx:66` enables "See result" as soon as one photo exists; `app/src/engine/decide.ts:11-38` has no condition on `n`; `app/src/content/rules.json` thresholds are absolute counts written for n = 10.
- Evidence (rules probe through `summarisePlot` and `decide` on 4 Oct):
  - 1 healthy leaf: `healthy_all` (ok), "No leaf problem seen on these leaves", not-sure line "We only checked 10 leaves".
  - 2 healthy + 2 unsure: `healthy_all` (ok), same text.
  - 3 rust of 3: `rust_high_pre_rains` (act), "Copper goes on just before the rains and again three weeks later".
  - 1 rust of 1: `rust_low`, "Prune to open the trees ... check again next weekend".
- Why a judge fails it: an all-clear on one leaf is the exact guess the gate forbids, and the card then states a falsehood about the sample.
- Smallest fix: add `n_lt` to `RuleCondition` and `ruleMatches` (engine, 3 lines), put `{"if":{"n_lt":10},"then":"too_few_leaves","assumption":true}` first in `rules.json`, and add a `too_few_leaves` answer (severity `ask`: "Fewer than 10 leaves were checked. Take more photos, or ask the officer."). Belt and braces in the UI: keep "See result" disabled until accepted plus pending retakes reach 10. Reword `healthy_all.not_sure` to "We only checked a few leaves, and only leaves, not berries." Rerun `decision_matrix` and the conformance suite.

**B2. The gate document over-claims review and features.**
- Review claims that are false (`answers.json`: `reviewed_by` is null for all 29 answers; every Swahili string is `draft_claude`; no audio exists):
  - `app/docs/RESPONSIBLE_AI.md:12` "Fixed, reviewed answers".
  - `RESPONSIBLE_AI.md:88` "Swahili audio is reviewed".
  - `RESPONSIBLE_AI.md:93` "reviewed by a person before release".
  - `RESPONSIBLE_AI.md:103` Swahili "Translated and reviewed", audio "ElevenLabs, pre-rendered".
  - `app/docs/LANGUAGES.md:20` Kikuyu "NLLB-200 ... Machine draft"; `answers.json` says `draft_claude_not_native ... (NLLB pass not run)`.
  - `kb/pitch/SUBMISSION_FORM.md:32` and `kb/pitch/VIDEO3_tech.md:36` "reviewed by a person".
- Features claimed that are not in the build: 4-digit PIN (`RESPONSIBLE_AI.md:70`; `setPin` exists in the engine, no UI); photo sync after a second consent (`RESPONSIBLE_AI.md:54`, `:77`; `consent_photos` never shown, `syncPending` not wired); consent "read aloud" (`RESPONSIBLE_AI.md:76`; no clips).
- Swahili draft is shown to Noor untagged (`app/src/ui/strings.ts:139` tags only `/machine/`).
- Why a judge fails it: the gate asks for a credible account. One false "reviewed" line makes the whole document unreliable.
- Smallest fix: one truth pass on `RESPONSIBLE_AI.md` sections 1, 4, 5, 6, 7, 8 and `LANGUAGES.md` sections 2 and 3: "drafted by Claude, native review pending", "no audio clips in this build", PIN and photo sync "planned, not built". In `strings.ts:139` also tag `draft` ("Draft translation, pending review"). Or make it true: Arthur's 10-minute Swahili review of the 8 core cards, logged with name and date in `kb/content/REVIEW_LOG.md` and `reviewed_by`.

## 6. Top 5 fixes by 13:30 (ranked by weighted gain per hour)

1. **Close B1 and B2 (gate; unlocks every other point).** Owner: engine (`decide.ts`, `types.ts`), content (`rules.json`, `answers.json` `too_few_leaves` and `healthy_all.not_sure`), ui (`Capture.tsx:66`, `strings.ts:139`), docs (`RESPONSIBLE_AI.md`, `LANGUAGES.md`), pitch (`SUBMISSION_FORM.md:32`, `VIDEO3_tech.md:36`). About 75 minutes in total. Acceptance: the rules probe above returns `too_few_leaves` for n < 10; `grep -n "reviewed" app/docs/RESPONSIBLE_AI.md` shows no claim that is not backed by `reviewed_by`.

2. **Put the measured evidence where judges read it (Evidence +3, Data +2).** Owner: docs and ml. About 45 minutes.
   - `app/docs/EVALUATION.md`: add a section "Whole leaves and field photos" with the EDGE_PLAN section 4 tables as they stand (BRACOL test n = 175, coverage 54%, selective accuracy 90%, healthy 0 of 12 accepted; field n = 468, 61% confidently wrong before the gate, 0.6% after), and the plot table (4,000 simulated plots per row: spray advice on healthy plots 0%, all-clear on rusty plots 0%, ask rate 88 to 100%). Name the test set in every row and keep the caveat that gate thresholds were set on the same images. Add v2 beside v1 if the overnight model lands.
   - Add a section "Browser build" with measured values: precache 25 files, 18,432,447 bytes raw, about 7.3 MB gzip, offline-ready in 60 s at 1 Mbit/s with gzip (`README_DEPLOY.md` section 4), 10 photos in about 0.4 s on a 2 vCPU cloud browser (not a phone), e2e offline PASS.
   - Copy the headline rows into `README.md` sections 5 and 8 and delete every `[PENDING]` there. Fix `README.md:13` to the `PROBLEM_STATEMENT.md:7` sentence, the Uganda row to "424 healthy images scored", "int8" to "fp16" in `ARCHITECTURE.md:12,40` and `REQUIREMENTS.md:11`, and replace the 12 `MASTER_PROMPT` citations with S-IDs or "design target".
   - Set `REQUIREMENTS.md` rows that now pass (R2, R3 model, G1, G2, G3, D5) to `pass` with links to `tests/e2e/screens/` and `qa/report.md`.

3. **Let a judge see the AI read a leaf (Built +1, Clarity +1).** Owner: content and ml, ui. About 45 minutes.
   - Replace or add a second sample set: 10 BRACOL test whole leaves on white (CC BY 4.0, credited) chosen from `kb/edge/field_check.py` output so that the v1 (or v2) model accepts them, for example 6 rust and 4 phoma, which BRACOL test accepts at 35/69 and 50/55, all correct. Keep the current field photos as a second button, "Try field photos (shows the retake)". That gives the demo one real reading and one honest refusal.
   - Do not hand-pick a set that overstates accuracy: state in `public/demo/manifest.json` and on screen "chosen from photos the model accepts; see EVALUATION for the full rate".

4. **Ship the live URL for this build (Built +1; S1, W1).** Owner: ui and Arthur. About 30 minutes.
   - Deploy `app/dist` to Netlify with `kb/runner/pending/app/netlify.toml` moved into place; check the absolute `/model`, `/ort`, `/audio` paths (fine on a Netlify root, broken on a GitHub Pages subpath).
   - Put the URL in `README.md:5` and `SUBMISSION_FORM.md`. Decide which URL judges get: if `jani-farm-assist.lovable.app` still runs the mock engine, link it only as "officer dashboard (synthetic records)", never as the farmer app.
   - Open it once on a real Android phone in airplane mode and note the model time per leaf (closes R1 and the "not tested on a phone" gap).

5. **Give the local language a voice, or stop claiming one (Clarity +1, rule 4).** Owner: Arthur and content-voice. About 40 minutes.
   - Best: Arthur renders the 8 core Swahili clips with `backend/scripts/render_audio.py` (consent_main, how_to_pick_leaves, how_to_photograph, retake_on_page, too_many_unsure, too_few_leaves, rust_high_pre_rains, decision_ask) and they go into `public/audio/sw/`; the build already precaches them.
   - If no clips by 11:00: remove "Voices: ElevenLabs (Swahili, English), pre-rendered" from `README.md` section 12 and "Swahili voice + text" from R4, and say "text in Swahili; voice uses the phone's own offline voice where one exists". Also remove `elevenlabs` from `src/content/sources.json` (QA `client_clean` FAIL).
   - Translate the two header badges ("Works offline", "Saving for offline use") into the chosen language.

## 7. Slop signals

No marketing vocabulary found. No accuracy figure without a named test set. The problems are draft residue and claims ahead of the build:

1. **Draft residue a judge sees in the first minute.** `README.md:5-7` live URL, repo and videos all `TODO`. Marker counts: README 17, RESPONSIBLE_AI 20, REQUIREMENTS 18, DATA_CARD 10, REPLICATION 8, ARCHITECTURE 7, LANGUAGES 6. `README.md:9` says "Draft by the docs agent, 3 Oct 2026". The word "agent" in a status line tells a judge the docs were not read by a person.
2. **Review claimed, not done.** See B2.
3. **Features in the docs that the build does not have.** PIN, photo sync, read-aloud consent, IndexedDB photo sync, officer dashboard at `/officer` in this app (`README.md` section 10), "Kikuyu clips play for at least 5 core answers" (R5; there are none).
4. **Voices credited that do not exist.** `README.md` section 12 "Voices: ElevenLabs (Swahili, English), pre-rendered"; `ARCHITECTURE.md` section 4 build-time audio; `LANGUAGES.md` section 2.
5. **int8 in the diagram and requirements while fp16 ships** (`ARCHITECTURE.md:12,40`, `REQUIREMENTS.md:11`).
6. **Budgets stated at target, not measured.** `README.md` section 5 and `REPLICATION.md` section 4 compute cost at "15 MB"; the measured precache is 18.4 MB raw (about 7.3 MB gzip). Report the measured number and say which one the download actually moves.
7. **Labels the UI no longer shows.** `README.md` section 3 lists six classes as what the farmer gets; the UI shows four groups (rust, no problem seen, other spots: ask the officer, not sure). Say so: it is a good safety decision (EDGE move 5) and the README hides it.
8. **The demo plot cannot show the product.** "Try a sample plot" is 12 field photos (leaf on a palm, leaves on the tree) that the model calls `not_leaf`. `VIDEO2_demo.md` 0:21-0:30 expects "[N] of ten leaves show rust", which this build cannot produce on any photo I tried.
9. **A fixed answer that states something false.** `healthy_all.not_sure` "We only checked 10 leaves" whatever n is (B1).
10. **Internal documents as sources.** "(source: MASTER_PROMPT 5.2)" 12 times across README and docs.
11. **Problem statement out of step** (`README.md:13` versus `PROBLEM_STATEMENT.md:7`); `RESPONSIBLE_AI.md:86` "GSMA 2024" is the 2025 report on a 2024 survey.
12. **QA red on the team's own harness.** `requirements:all_pass` 26 of 26 todo, `budgets:bundle_size`, `client_clean` (elevenlabs in sources.json), `EVALUATION.md:16-19` lines without labels. A judge who runs `python -m qa.run` from the README sees 4 blocking issues.

## 8. The two hardest Q&A questions

**Q1. "I opened your app, tried your sample plot and three of my own photos, and every time it said 'not sure, ask the officer'. What does the AI add, beyond a button that says 'ask the officer'?"**
Best honest answer today: "On field photos our v1 model is wrong 61% of the time before the gate (468 photos from Uganda and iNaturalist, never trained on). So we built the app to refuse them: the sheet gate and the abstention rule cut that to 0.6%, and in 4,000 simulated plots it never advised a spray on a healthy plot and never gave a rusty plot the all-clear. On whole leaves laid on a plain page, the protocol the app asks for, it answers 54% of BRACOL test leaves and is right on 90% of those, and it reads rust and phoma well. It cannot yet read healthy leaves on paper, which is why a healthy plot goes to the officer. That is the gap we are closing, and we would rather show you a tool that refuses than one that guesses." This answer only works if fix 2 puts these numbers in EVALUATION and fix 3 gives the judge one real reading.

**Q2. "None of your Swahili or Kikuyu has been checked by a speaker, there is no audio, and no officer has signed your thresholds. Why should a cooperative trust a single card?"**
Best honest answer today: "It should not yet, and we say so on the card ('Assumption') and in RESPONSIBLE_AI section 9. Every card that could lead to a spray says to ask the cooperative which product and how much; we write no product or dose. Every threshold in rules.json is marked 'assumption, officer to confirm' because we found no Kenyan incidence threshold. Because the advice is a fixed list of 29 cards, a speaker can review all of it in an hour and an officer can audit every outcome in `qa/decision_matrix.md` (3,510 plot summaries). That is the point of keeping generation out of the runtime." This answer is credible only after B2: if the docs say "reviewed" anywhere, the judge stops listening.

## 9. Notes for the lanes

- engine: B1 (`n_lt` condition). Regenerate conformance fixtures after content changes (harness `toPct` bug noted in INTEGRATION).
- content: `too_few_leaves` card in sw, en (and kik only if marked machine); `healthy_all.not_sure` wording; on-page sample set (fix 3).
- ui: `Capture.tsx:66` minimum 10; `strings.ts:139` draft tag; translated header badges; second sample button.
- docs and pitch: B2 truth pass; fix 2 evidence port; README markers to zero; drop MASTER_PROMPT citations.
- Arthur: Netlify deploy and phone check (fix 4); Swahili review and clips (fix 5); move the 3 files from `kb/runner/pending/`.
