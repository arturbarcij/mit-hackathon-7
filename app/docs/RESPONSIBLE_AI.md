# Responsible AI, data and safety

Status: draft by the docs agent, 3 Oct 2026. Truth pass against the build on 2026-10-04 (overnight fixer: every claim below now says what the build does, and what is planned is marked "planned"). This is the pass/fail section of the brief. Measured numbers are `[PENDING: ml]` until `EVALUATION.md` is filled. Requirement IDs (P1, P2, G1 to G3) link to `REQUIREMENTS.md`.

## 1. Summary

| Risk | What we do | Where to check |
|---|---|---|
| The tool guesses | It abstains and says "not sure, ask the officer" | Section 3, `EVALUATION.md` |
| The tool decides for Noor | It cannot. She picks act, wait or ask. | Section 2 |
| Private data leaks | Everything stays on the phone unless she agrees twice | Section 4 |
| Wrong or invented advice | No runtime text generation. Fixed answers from a written list; English written by us, Swahili drafted, native review pending. No doses. | Section 7 |
| A machine voice or translation is wrong | No recorded audio in this build. Draft text is tagged on screen ("Draft, pending review" or "Machine translation, pending review") | Section 8 |
| Bias toward the data we had | Per-dataset results, stated gaps | Section 6 |

## 2. Human oversight

- Noor makes the final call with three buttons: "I will act", "I will wait", "Ask the officer". No code path performs an action without a tap (G1).
- The referral SMS opens in her messaging app, pre-filled. She presses send. Nothing is sent automatically (G2).
- Planned, not in this build: an officer dashboard where the officer confirms or corrects each referral, with corrections stored as new labelled examples. In this build the officer receives the SMS only.
- Officer sign-off on the rule table is required before real use. `TODO(lead)`: record the name of the officer who reviews `rules.json`, or state that none has yet.
- The AI reads leaf photos only. The advice comes from a rule table that a person can audit (`qa/decision_matrix.md` lists every outcome).

## 3. Fail-safe and abstention

The tool says "not sure, ask the officer" and offers a ready referral in each of these cases (P1):

| Trigger | Rule | Source of the cut-off |
|---|---|---|
| Photo too blurry or dark | Quality gate (Laplacian variance, brightness) asks for a retake | `src/engine/quality.ts`: MIN_BLUR 60, MIN_BRIGHTNESS 0.18, MIN_SIDE 224 px (assumption, not tuned on field photos) |
| Not a coffee leaf, or leaf not on a plain page | "Not a leaf" model class, plus the sheet gate (leaf must lie on a plain page). There is no separate out-of-distribution score in this build. | `[PENDING: ml]` |
| Low confidence on a leaf | Top-class probability below a calibrated threshold, counted as "unsure" | `[PENDING: ml]` threshold |
| Leaves disagree | Two or more problem types in one plot go to the officer | `rules.json`, assumption |
| Too many unsure leaves | 3 or more of 10 unsure go to a person | `rules.json`, assumption |
| Fewer than 10 leaves | No plot answer: "We need photos of 10 leaves" card (`too_few_leaves`, ask). See result stays off until 10 photos are in. The same photo added twice counts once. | `decide.ts` MIN_LEAVES; the 3-of-10 cut-offs assume 10 leaves |
| Model did not load | Every leaf counts as unsure (no made-up labels), so the plot goes to too many unsure or ask the officer. The demo mock runs only when built with `VITE_USE_MOCK_MODEL=true` and then shows a badge. | `src/engine/model.ts` |
| Problem outside scope (berries, nutrients, roots) | Fixed "outside what this tool can see" card | `answers.json` |

Measured performance of the abstention rule:

| Measure | Value | Test set |
|---|---|---|
| Calibration method | temperature scaling on a validation split | `[PENDING: ml]` |
| Chosen threshold | `[PENDING: ml]` | `[PENDING: ml]` |
| Coverage (share of leaves answered) at that threshold | `[PENDING: ml]` | `[PENDING: ml]` |
| Accuracy on answered leaves | `[PENDING: ml]` | named test set, `[PENDING: ml]` |
| Share of non-coffee photos rejected | `[PENDING: ml]` | `[PENDING: ml]` |
| Blurry, dark, non-leaf and mixed inputs that abstain | `[PENDING: qa]` | `app/qa` test images |

The cut-offs in `rules.json` (for example "3 of 10 leaves") are assumptions. We found no Kenyan incidence threshold (see `DATA_CARD.md`, section 3). They are labelled "assumption, officer to confirm" in the file.

## 4. Privacy and data flow

| Data | Where it sits | Who can read it | When it leaves the phone |
|---|---|---|---|
| Leaf photos | IndexedDB on the phone | Whoever uses the phone | Never in this build. Photo sync with a second, separate consent is planned, not wired. |
| Check results and decisions | IndexedDB on the phone | Whoever uses the phone | Only inside the referral SMS, and only if Noor sends it |
| Referral SMS | Her SMS app, then the cooperative number | The cooperative and the officer | When Noor presses send. Content: member number, plot, date, counts, confidence. Under 160 characters. |
| Name, ID number, GPS | Not collected | Nobody | Never. No location finer than the plot ID unless she consents. |
| Officer dashboard rows | Planned (Lovable Cloud / Supabase); no dashboard in this build | The officer | Demo rows would be synthetic and tagged (see `DATA_CARD.md`, section 4) |

Other points:

- No user accounts or passwords on the farmer side.
- The referral carries a member number, not a name.
- Our services hold no farmer registry. The cooperative does.
- No API key ships in the client. This build has no recorded audio; the speaker button uses the phone's own offline voice when one exists. Planned clips would be pre-rendered at build time, so no ElevenLabs key would be in the app. Keys live in `backend/.env`, which is git-ignored.
- `TODO(engine)`: confirm in the final build that the app makes no network request during a leaf check (offline test in `app/tests`).

## 5. Shared phone, lost phone, consent

**Shared phone.** In the brief, the smartphone is the daughter's. Records sit under a household profile. Planned, not in this build: a 4-digit PIN that hides the history (the storage code has it; no screen uses it yet).

**Lost phone.** Data is local and minimal: no name, no ID, no location. The cooperative holds the registry, not us. A lost phone exposes leaf photos and counts for one plot.

**Consent, two levels.**

1. Before first use: the consent screen, in the chosen language, says what is stored, where, and who can see it. Noor says yes or no. It has a play button that reads it with the phone's own offline voice when the phone has one; there is no recorded clip in this build.
2. Planned, not in this build: before any sync of photos, a separate yes, asked again at that moment. Photo sync is not wired, so photos never leave the phone.

`TODO(content-voice)`: consent wording reviewed by a Swahili speaker (STATUS L3).

## 6. Bias and representativeness

- We report performance per dataset and per class, not one pooled number. The results are `[PENDING: ml]` and will sit in `EVALUATION.md`: Kenya in-domain, Uganda held-out, Ecuador held-out.
- Known gaps (full list in `DATA_CARD.md`, section 3): no labelled Kenyan varieties, mostly cropped or augmented photos, few real field backgrounds, one Robusta farm, no night photos.
- Class balance in the training sets is uneven (healthy and miner dominate). `[PENDING: ml]`: how we corrected for it.
- Gender and access: 42% of Kenyan women own a smartphone against 50% of men (GSMA 2024). The design assumes the smartphone may not be Noor's. Her own phone gets only SMS and voice.
- Literacy: every instruction has an icon and a play button. This build has no recorded clips, so the play button depends on the phone having an offline voice for the language.
- Language bias: Swahili text is a draft pending native review, and Kikuyu text is a lower-confidence draft; there is no recorded audio in either (section 8).
- Plan to reduce bias (planned, not in this build): officer corrections create local labelled photos of Ondera leaves, so the model can be retrained on them.

## 7. Content safety

- No runtime text generation. Every answer shown or spoken is in a fixed list (`answers.json`). No answer has had native speaker review yet: `reviewed_by` is empty for all of them, and the Swahili and Kikuyu text is tagged as a draft on screen. Review by a person is required before release (G3).
- No pesticide product names or doses are written by us. The card says "ask the cooperative which product and dose".
- The cards use general safety wording only (source: WHO guidance, S20). `TODO(content-voice)`: confirm what safety wording is on the cards.
- Where we found no Kenyan source (phoma, brown eye spot), the answer is "ask the officer".
- Review log: `kb/content/REVIEW_LOG.md` (Swahili items listed for the native reviewer; none signed off yet).

## 8. Language risk

| Language | Text | Audio | Review status |
|---|---|---|---|
| Swahili | Drafted by Claude (builder draft), native Kenyan Swahili review pending | No audio in this build (ElevenLabs clips planned) | Not reviewed. Tagged "Draft, pending review" on screen. `TODO(Arthur)`: reviewer name and date (STATUS L3) |
| English | Written by us | No audio in this build (ElevenLabs clips planned) | Checked by team |
| Kikuyu | Drafted by Claude, not a native draft (the NLLB pass was not run); low confidence | No audio in this build (Meta MMS-TTS, CC BY-NC, planned) | **Pending native speaker review.** Tagged "Machine translation, pending review" on screen. Answers with no Kikuyu text show Swahili with "Not translated yet". |

Details in `LANGUAGES.md`. A wrong machine translation in a farm advice setting is a real harm. Kikuyu text covers a subset of answers and is tagged in the UI; there are no Kikuyu clips in this build. The short Swahili button labels (`src/ui/strings.ts`) are also an unreviewed builder draft and carry no tag; there are no Kikuyu button labels.

## 9. Before any real deployment

1. Native speaker review of all Swahili and Kikuyu text (none done yet), and of any audio once it is recorded.
2. Written sign-off of `rules.json` by a named extension officer, with real incidence thresholds.
3. Local photo collection and labelling by the officer, then re-evaluation on Ondera leaves.
4. A data-sharing agreement with the cooperative (who holds the member list, how referrals are stored, how long).
5. A field test with Noor-like users on the real two-phone pattern, with consent.
6. A commercial-safe route for voices and translation, since MMS-TTS and NLLB are non-commercial.
7. Legal review of data protection obligations in Kenya. `TODO(lead)`: we have not researched the Kenyan Data Protection Act for this document.
8. A route for farmers to report a wrong answer, and a person who reads those reports.

## 10. What we do not claim

- We do not claim the model is safe for use without an officer.
- We do not claim accuracy on Noor's farm. We have no photos from it.
- We do not claim a national yield decline.
- Simulated parts (SMS reminders, seed referrals, delivery records) are labelled as simulated or synthetic.
