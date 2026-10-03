# Responsible AI, data and safety

How Jani keeps a person in charge, says "not sure" instead of guessing, and protects Noor's data.

Status: first draft. It describes the engine as built on branch `cursor/engine-offline-core-d90f` ([PR #2](https://github.com/arturbarcij/mit-hackathon-7/pull/2), not merged). The farmer screens and the officer dashboard are not built yet. Where something is not built, this file says so. The leaf model is not trained yet, so there are no accuracy or coverage figures here; those are pending ml.

## 1. What the AI does and does not do

- The AI does one thing: it reads a photo of one picked coffee leaf and gives a label (healthy, rust, Cercospora, Phoma, leaf miner, not a coffee leaf) with a confidence, or "unsure".
- The advice is not AI. A rule table (`rules.json`) maps the plot summary and the season window to a fixed answer ID. Every answer Noor can see or hear is in a fixed list (`answers.json`). Nothing is generated on the phone.
- There is no chatbot, no free text and no runtime call to any AI service. An engine test (`app/tests/engine/noai.test.ts`) fails if the client code mentions an AI API.

## 2. Human oversight

- **Noor decides.** After the answer card she chooses "I will act", "I will wait" or "Ask the officer". The engine records her choice (`useCheck().choose`) and does nothing else. It never picks for her.
- **Nothing is sent without a tap.** The referral SMS is built on the phone and opened in the phone's own SMS app with the text filled in (`sms:` link). Noor presses send herself. The engine only builds the link; the UI must open it from her tap on "Send SMS".
- **The officer confirms.** Every referral is meant to be checked by the extension officer, who confirms or corrects the label. Corrections become new labelled examples. The officer dashboard is not built yet.
- **No automatic actions anywhere.** No code path sprays, orders, pays or messages on Noor's behalf.

## 3. Fail-safe and abstention

When the data is not enough, the tool says "not sure, ask the officer" and offers a ready referral. It abstains at four points.

| Point | What triggers it | What Noor sees | Status |
|---|---|---|---|
| Photo quality gate | Photo too dark (mean brightness below 45 of 255), too blurry (sharpness score below 0.0012), or too small (short side under 224 px) | "Retake" card with audio. No inference is run on a failed photo | Built. Thresholds tuned on synthetic images only; still need 10 sharp and 10 blurry real phone photos |
| Per-leaf confidence | Top calibrated probability below the threshold in `model.json` | The leaf shows as "?" and counts as unsure. It is never forced into a class | Built. Threshold value pending ml |
| Not a coffee leaf | The model's `not_leaf` class wins | If at least half the photos are not leaves, the card says "this does not look like a coffee leaf" | Built in the engine. Depends on the real model |
| Plot level | 3 or more unsure leaves, or 2 or more different problems across the leaves, or no rule matches | "Not sure, ask the officer" (`too_many_unsure`, `mixed_problems`, `ask_officer`) | Built with placeholder rules. Final cut-offs come from content-voice |

Further safety in the rules engine:
- The last rule is always "ask the officer". An unknown rule key or a bad value makes that rule fail to match, so a broken table falls through to "ask the officer", never to an action.
- A check with no photos returns "ask the officer".
- If the real model file is missing, the engine says so, uses a mock model and reports `mock: true`. The UI must show a visible "mock model" badge.
- The model file is checked against a SHA-256 checksum in `model.json` before use.

**Calibration.** The engine applies temperature scaling to the model's outputs before the threshold. The temperature, the threshold, and coverage against accuracy at that threshold are pending ml (see `EVALUATION.md`).

**What the fail-safe does not catch.** A confident wrong answer on a leaf that looks like the training data. A disease the model has never seen that looks like one it knows. The rule-level checks reduce this; the officer's review is the backstop.

## 4. Privacy

Where data sits:

| Data | Where | Who can read it | When it leaves the phone |
|---|---|---|---|
| Check results (labels, counts, answer ID, decision) | IndexedDB on the phone | Anyone holding the unlocked phone | Only if Noor chose "Ask the officer" and gave main consent, and the phone is online |
| Leaf photos (re-encoded, longest side at most 800 px) | IndexedDB on the phone, saved only with main consent | As above | Only with the second, separate photo consent. Photo upload is not built yet |
| Referral SMS | Noor's SMS app, after she taps | The cooperative number she sends it to | When she presses send |
| Consent and PIN record | IndexedDB on the phone | The app | Never |

What the referral SMS carries: format version, cooperative member number, plot number, date, leaf counts per class, unsure count, answer ID, mean confidence and her decision. Example: `JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask`. No name, no phone contacts and no GPS location. The member number comes from the cooperative's existing registry.

Store and forward: when the phone comes online, the engine pushes only referrals where Noor chose "Ask the officer" and gave main consent. It uses the public (publishable) database key, which is meant to ship to browsers. Row-level security so the farmer app can insert but not read is the ui agent's job and is not built yet.

No location finer than the plot number is collected. No accounts or passwords on the farmer side. No analytics.

## 5. Shared phone and lost phone

- **The smartphone belongs to her daughter.** Records sit under one household profile on the phone.
- **Optional 4-digit PIN.** It hides the check history. The PIN is stored as a salted PBKDF2 SHA-256 hash with 50,000 iterations; it is never stored in plain text. This is a privacy screen against other family members, not encryption: four digits can be guessed by someone with technical access to the phone, and on a page served over plain HTTP the engine falls back to a weak hash. The live site must be served over HTTPS. There is no live URL yet.
- **Delete everything.** The engine can wipe all checks, photos, consent and the PIN (`clearAll`). A button for it is not built yet.
- **Lost phone.** Data is local and small: results, and photos only if consent was given. No password or account is on the phone. The cooperative holds the member registry, not Jani.

## 6. Consent

Two levels, asked in the chosen language and read aloud.

1. **Main consent** before first use: what is stored, where (on this phone), who can see it, and that nothing is sent unless she chooses. Without it, photos are not saved and nothing is ever queued to send. The check still runs and the result is kept on the phone so she can see it again.
2. **Photo consent**, separate: may photos go to the officer with a referral? She can say no and still send the SMS. The engine never stores photo consent as "yes" unless main consent is also "yes", and checks both the stored consent and the consent on the check before any photo upload.

Consent can be changed at any time. The consent cards exist in the answer bank as placeholders (`consent_main`, `consent_photos`). Their final wording, audio and the consent screens are not built yet.

## 7. Bias

Known sources of bias in the training data (details in `DATA_CARD.md`):
- **Country and farm.** Kenyan images come from one farm in Kirinyaga, one camera and one preprocessing pipeline. The second source is Brazilian.
- **Variety.** SL28, Ruiru 11 and Batian are not labelled in any dataset.
- **Lighting and background.** Training images are cropped, filtered or on white backgrounds. Low light appears only in the Uganda test set.
- **Leaf side.** BRACOL shows the leaf underside only.
- **Class balance.** Kenyan healthy leaves far outnumber Brazilian Cercospora images.
- **Sampling.** Noor picks 10 leaves from the rows she is worried about. That sample will overstate incidence across the whole plot. The rule table is written with this in mind and points to the officer for any curative spray.

How we report it: per-class and per-dataset results for Kenya (in-domain), Uganda (cross-country) and Ecuador (field, Robusta), shown even when worse. Pending ml.

How we would reduce it: officer corrections on referrals become locally labelled photos from Ondera's own plots, in Ondera's own light. The correction loop is not built yet.

## 8. Content safety

- Every answer in the bank is written from published Kenyan guidance (KALRO Coffee Research Institute review and leaflets [S1], [S2], [S3]) and reviewed by a person before release.
- **No product names and no doses.** Pesticide guidance says "ask the cooperative or officer for product and dose". Products and rates in Kenya are set through the Pest Control Products Board registered list [S1].
- Spray timing follows the calendar in the guidance: copper in mid October before the short rains, repeated about three weeks later [S1], [S3].
- The one Kenyan incidence figure, about 20% of leaves with rust, is for a curative spray that needs the officer [S2], [S3]. Mapping it to 2 of Noor's 10 leaves is an assumption for the officer to confirm.
- Answers marked as resting on an assumption carry `assumption: true` in the bank.
- Safety handling (protective clothing, storage, empty containers) follows FAO and WHO guidance [S8].
- Out of scope, with a referral card: berries, other crops, roots.

The current answer bank in the engine branch is a placeholder set marked "[placeholder]". The reviewed bank is not delivered yet.

## 9. Language risk

- **Swahili** text and audio are reviewed by a Swahili speaker before release. Review is not done yet.
- **Kikuyu** text is machine-drafted (NLLB-200) and the audio is machine-generated (Meta MMS-TTS). The app must mark both "machine voice, pending native speaker review" (screens not built yet). Both models are CC BY-NC 4.0 [model_mms_tts_kik], [model_nllb_600m].
- A machine translation of farm advice can be wrong in ways a non-speaker will not notice. That is why Kikuyu covers only a subset of answers, the card text stays visible, and Swahili is always available.
- If a Kikuyu clip is missing, the engine plays the Swahili clip instead. The UI should say so, so Noor knows the language changed. Not built yet.
- Details in `LANGUAGES.md`.

## 10. What a real deployment would need first

- Native speaker review of every Kikuyu and Swahili answer, text and audio.
- Extension officer sign-off on the rule table and every answer card.
- Local photos collected through officer corrections, with consent, and a fresh evaluation on them.
- Quality-gate thresholds tuned on real phone photos.
- A data agreement with the cooperative: who holds referrals and photos, for how long, and how a member can ask for deletion.
- A commercially licensed voice and translation, or native recordings, before any commercial use.
- A test on a real low-end Android phone. So far the engine is tested in Chromium with 4x CPU throttling.

## 11. Reviewer checklist

| Check | Where to look | Status |
|---|---|---|
| No runtime AI call in the client | `app/tests/engine/noai.test.ts` (engine branch) | Passes on the engine branch |
| Rule table always ends in "ask the officer" | `app/src/engine/decide.ts`, `app/tests/engine/decide.test.ts` | Passes on the engine branch, placeholder rules |
| Referral is never sent automatically | `app/src/hooks/useEngine.ts` (`choose` saves only; `smsHref` builds a link) | Engine side done. UI not built yet |
| Photos leave only with photo consent | `app/src/engine/sync.ts` | Engine side done. Upload not built yet |
| Abstention on blurry, dark, non-leaf and mixed inputs | `app/tests/e2e/offline.spec.ts` | Blur, dark and tiny rejected with the fixture model. Non-leaf needs the real model |
| Calibrated threshold and coverage reported | `EVALUATION.md` | Pending ml |
| Per-dataset bias results | `EVALUATION.md` | Pending ml |
| Answer bank reviewed | `kb/content/REVIEW_LOG.md` | Not started |
