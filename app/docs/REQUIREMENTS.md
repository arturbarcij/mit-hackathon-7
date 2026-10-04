# Requirements traceability matrix

Status: skeleton by the docs agent, 3 Oct 2026. Source: `kb/MASTER_PROMPT.md` section 12. Nothing is "pass" until its test passes and the evidence link works. The qa agent owns the Status and Evidence link columns after this first version.

Status values: todo, pass, fail. Doc cross-references (for example `DATA_CARD.md` section 3) show where the docs agent has written the supporting text; they do not mean the test has passed.

| ID | Requirement (source) | How we meet it | Acceptance test | Evidence needed | Evidence link | Status |
|---|---|---|---|---|---|---|
| R1 | Runs on a device the user already has (§06) | PWA on the household Android smartphone; SMS on her basic phone | Install and run on a real Android phone (or throttled Chrome mobile emulation, stated) | Screen recording | `TODO(qa)` screen recording | todo |
| R2 | Core feature works offline (§06) | Service worker caches app, model, audio, rules | Airplane mode: full leaf check end to end | Video 2 clip | `TODO(qa)` Video 2 clip; `app/tests` offline test | todo |
| R3 | Model small enough to side-load or send over weak link (§06) | int8 ONNX, at most 5 MB; bundle at most 15 MB | File sizes printed in build log; download time at 1 Mbit/s computed | EVALUATION.md | `EVALUATION.md` section 5 `[PENDING: ml]` | todo |
| R4 | At least one interaction in a named local language, voice or text (§06) | Swahili voice + text for all answers | Every answer ID has Swahili text and audio | Answer bank table | `src/content/answers.json` `TODO(qa)` | todo |
| R5 | Ready for "less-supported language" question (§06) | Kikuyu subset via MMS-TTS (CC BY-NC 4.0, flagged in docs); process to add a language documented | Kikuyu clips play for at least 5 core answers; doc describes 30-clip recording path | LANGUAGES.md | `LANGUAGES.md` section 3 | todo |
| G1 | Human makes the final call (§06) | Act / wait / ask buttons; officer confirms | No code path performs an action without a user tap | Code review + demo | `TODO(qa)` code review note | todo |
| G2 | Agentic steps check in with user (§06) | SMS opened pre-filled, user sends | Referral never auto-sends | Demo | `TODO(qa)` demo clip | todo |
| G3 | Avoid hallucinations (§06) | Fixed answer list; no generative runtime | Grep: no LLM calls in client; every rendered answer exists in the bank | Test | `TODO(qa)` grep log; `qa/report.md` | todo |
| P1 | Fail-safe: "not sure, ask a person" (§09) | Calibrated threshold, quality gate, OOD, disagreement rule | Blurry, dark, non-leaf and mixed inputs all abstain | Test images + video | `EVALUATION.md` section 3 `[PENDING: ml]`; `RESPONSIBLE_AI.md` section 3 | todo |
| P2 | Credible privacy, consent, bias, oversight (§09) | RESPONSIBLE_AI.md, consent screens, on-device storage | Reviewer checklist passes | RESPONSIBLE_AI.md | `RESPONSIBLE_AI.md` | todo |
| D1 | Cite all data sources (§07) | DATA_CARD.md and in-app "Sources" page | Every dataset and statistic has a citation | DATA_CARD.md | `DATA_CARD.md`; `src/content/sources.json` | todo |
| D2 | Problem data with source, year, country (§7.2) | Problem evidence table | Each figure has all three fields | README | `DATA_CARD.md` section 1 | todo |
| D3 | Build data: name, source, licence, size (§7.2) | Data card | All four fields filled for every set | DATA_CARD.md | `DATA_CARD.md` section 2 | todo |
| D4 | State what data does not cover (§7.2, scored) | "Gaps" section per dataset and for the model | Section exists, specific, not generic | DATA_CARD.md | `DATA_CARD.md` section 3 | todo |
| D5 | Synthetic data labelled (§7.2) | `synthetic: true` flag and UI tag | Every synthetic record tagged | DB query | `DATA_CARD.md` section 4; `TODO(ui)` DB query | todo |
| W1 | Working prototype (§05) | Live URL | URL loads on a fresh phone; full flow works | Live URL | `TODO(ui)` live URL | todo |
| W2 | Clear AI technique and why not simpler (§05) | Section 7 text in README and Video 3 | Present in both | README, Video 3 | `README.md` section 4 | todo |
| W3 | Proof it works on real examples (§05) | Cross-domain evaluation, worked examples | EVALUATION.md complete | EVALUATION.md | `EVALUATION.md` `[PENDING: ml]` | todo |
| B1 | One better agricultural decision (Annex B) | Act / wait / ask on leaf problem, with timing and referral | Demo shows the decision being made | Video 2 | `TODO(pitch)` Video 2 | todo |
| B2 | Addresses extension gap and registry precondition (Annex B) | Referral keyed to coop member number; officer queue | Officer dashboard receives referral | Video 2 | `TODO(pitch)` Video 2 | todo |
| S1 | Live project URL (platform) | Lovable publish or Vercel | Opens in incognito on mobile | URL | `TODO(lead)` URL | todo |
| S2 | Code link; repo public after submission (platform) | GitHub repo, MIT licence, no secrets | `git log -p` secret scan clean; repo set public right after submit | Repo | `TODO(qa)` secret scan log | todo |
| S3 | 3 videos, each MP4/MOV, max 60 s, max 1 GB (platform) | Section 11 | `ffprobe` duration under 60 s, size under 1 GB, container MP4/MOV | Files | `TODO(pitch)` ffprobe log | todo |
| S4 | Videos jointly cover PDF items a to e (§08) | Section 11 mapping | Checklist ticked per video | Checklist | `TODO(pitch)` `video/COVERAGE.md` | todo |
| S5 | Submitted before 4 Oct 2026 15:00 CEST | Freeze 13:30 | Submission confirmation screenshot | Screenshot | `TODO(Arthur)` screenshot | todo |
| J1 | Scalability and reuse (§09) | Model + rule table + answer bank are swappable per crop/language; cooperative-based rollout | REPLICATION.md describes cocoa in Côte d'Ivoire as an example swap | Doc | `REPLICATION.md` | todo |

Counts: 26 rows. Rows R1 to R5, G1 to G3 are engine and content; P1 and P2 are safety (pass/fail gate); D1 to D5 and J1 are documents; W, B, S rows are product and submission.
