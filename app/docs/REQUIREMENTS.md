# Requirements

Traceability matrix from the project brief. Status is `todo` on every row until a test passes and the evidence exists. This file does not mark a pass. The evidence column names the document or test that will prove the row.

Live URL: not published yet. The leaf model is not trained in this checkout.

| ID | Requirement (source) | How we meet it | Acceptance test | Status | Evidence |
|---|---|---|---|---|---|
| R1 | Runs on a device the user already has (brief section 06) | PWA on the household Android smartphone. SMS on her basic phone | Install and run on a real Android phone, or throttled Chrome mobile emulation, and state which | todo | Screen recording, not yet made |
| R2 | Core feature works offline (section 06) | Service worker caches app, model, audio and rules | Airplane mode: full leaf check from photo to answer | todo | Video 2 clip, not yet made. Architecture target in `docs/ARCHITECTURE.md` |
| R3 | Model small enough to side-load or send over a weak link (section 06) | int8 ONNX, hard cap 5 MB. Bundle target 15 MB or less | File sizes in the build log. Download time at 1 Mbit/s computed from the measured size | todo | `docs/EVALUATION.md` size rows, currently [PENDING: ml]. Targets in `docs/ARCHITECTURE.md` |
| R4 | At least one interaction in a named local language, voice or text (section 06) | Swahili text and voice for the answer list | Every answer id has Swahili text and audio | todo | Answer bank table, not in this checkout. Draft status in `docs/LANGUAGES.md` |
| R5 | Ready for a less-supported language (section 06) | Kikuyu is the home language in the design. It is not translated yet | Kikuyu clips for at least 5 core answers, and a written path for about 30 recordings (assumption) | todo | `docs/LANGUAGES.md` |
| G1 | A person makes the final call (section 06) | Act, wait and ask. The officer confirms | No code path acts without a user tap | todo | Code review and demo, not yet run |
| G2 | Agentic steps check in with the user (section 06) | SMS opens pre-filled. She sends | Referral never auto-sends | todo | Demo, not yet recorded |
| G3 | Avoid hallucinations (section 06) | Fixed answer list. No generative runtime | No LLM calls in the client. Every rendered answer exists in the bank | todo | Automated test, not yet written |
| P1 | Fail-safe: not sure, ask a person (section 09) | Threshold, quality gate, out-of-distribution check, disagreement rule | Blurry, dark, non-leaf and mixed inputs all abstain | todo | Test images and video, not yet made. Threshold coverage [PENDING: ml] in `docs/RESPONSIBLE_AI.md` |
| P2 | Credible privacy, consent, bias and oversight (section 09) | Two consents, on-device storage, written bias gaps | Reviewer checklist | todo | `docs/RESPONSIBLE_AI.md` |
| D1 | Cite all data sources (section 07) | Data card and in-app sources list | Every dataset and statistic has a citation | todo | `docs/DATA_CARD.md` and `src/content/sources.json` |
| D2 | Problem data with source, year and country (section 7.2) | Problem evidence table | Each figure has all three fields | todo | `README.md` and `docs/DATA_CARD.md` |
| D3 | Build data: name, source, licence and size (section 7.2) | Build data table | All four fields for every set | todo | `docs/DATA_CARD.md` |
| D4 | State what the data does not cover (section 7.2, scored) | Gaps by dataset and for the model | Section is specific | todo | `docs/DATA_CARD.md` gaps section |
| D5 | Synthetic data labelled (section 7.2) | `synthetic: true` and a visible tag | Every synthetic record tagged | todo | Database query once referral storage exists |
| W1 | Working prototype (section 05) | Live URL and the offline leaf check | URL loads on a fresh phone and the full flow works | todo | Live URL: not published yet |
| W2 | Clear AI technique, and why a simpler tool would not do the job (section 05) | Computer vision on the phone. Rules, calendar and price stay non-AI | Text present in the README and in video 3 | todo | `README.md`. Video 3 not yet made |
| W3 | Proof it works on real examples (section 05) | Named test sets and worked examples | Evaluation file complete with test sets named | todo | `docs/EVALUATION.md`. All metrics [PENDING: ml] |
| B1 | One better agricultural decision (Annex B) | Act, wait or ask on a leaf problem, with timing and a referral | Demo shows her making the decision | todo | Video 2, not yet made |
| B2 | Extension gap and registry precondition (Annex B) | Referral keyed to the cooperative member number. Officer queue | Officer dashboard receives a referral | todo | Video 2, not yet made |
| S1 | Live project URL (platform) | Publish when the prototype runs | Opens in a private browser window on a phone | todo | Live URL: not published yet |
| S2 | Code link. Repo public after submission (platform) | GitHub repo, MIT licence, no secrets | Secret scan clean. Repo set public after submit | todo | This repo and `LICENSE` |
| S3 | Three videos, each MP4 or MOV, max 60 seconds, max 1 GB (platform) | Section 11 of the project brief | `ffprobe` duration under 60 seconds, size under 1 GB | todo | Video files, not yet made |
| S4 | Videos jointly cover PDF items a to e (section 08) | Mapping in section 11 of the project brief | Checklist ticked per video | todo | Checklist, not yet filled |
| S5 | Submitted before 4 Oct 2026, 15:00 CEST | Internal freeze 13:30 CEST | Submission confirmation screenshot | todo | Screenshot, not yet made |
| J1 | Scalability and reuse (section 09) | Model, rule table, answer bank and season file are swappable | Cocoa in Côte d'Ivoire written up as an illustration, not a built product | todo | `docs/REPLICATION.md` |
