# Reusable abuse cases (redteam)

One line each: input or action -> expected safe outcome. Run every pass on the live URL and on the rules (`qa.checks.decision_matrix.decide`). Window for date-dependent cases: 4 Oct = `pre_short_rains`.

## Abstention and few leaves
- A01: finish after 5 leaves, 5 healthy -> no "Looks okay"; ask card or "take 10 leaves".
- A02: 5 leaves, 3 healthy + 2 unsure -> ask card, never `healthy_all`.
- A03: 5 leaves, 3 rust + 2 healthy, 4 Oct -> ask card, never an act card.
- A04: 10 leaves, 8 healthy + 2 unsure -> `healthy_all` allowed only with not_sure naming what it cannot see; review the 20% unsure.
- A05: 10 leaves, 7 healthy + 3 unsure -> `too_many_unsure` (ask).
- A06: 10 leaves, 3 rust + 2 unsure, 4 Oct -> act card shows the assumption tag and no "Act today" directive.
- A07: 20 leaves, 3 rust + 17 healthy -> not an act card (3 of 20 is not "3 of 10").
- A08: 10 leaves, 2 rust + 2 cercospora -> `mixed_problems` (ask).
- A09: 10 leaves, 6 not_leaf + 4 healthy -> `too_many_unsure` or `not_a_leaf`; never `healthy_all`.
- A10: 10 leaves all unsure -> `too_many_unsure` (ask).
- A11: 0 leaves (open summary with nothing) -> `ask_officer`, no crash.

## Bad photos and out of scope
- B01: photo of a hand, soil, sky or paper -> retake prompt (`not_a_leaf`), leaf not counted.
- B02: green coffee berries with dark sunken spots -> not counted as a leaf; berries-out-of-scope message.
- B03: black or very dark frame -> `retake_dark`.
- B04: motion-blurred leaf -> `retake_blurry`.
- B05: non-coffee leaf (maize, banana, tea) -> not_leaf or unsure; never a disease label with high confidence.
- B06: any image sized 1080 x 2340 (screenshot) of anything -> must not return "rust" from the mock; unsure only until the real model is in.
- B07: non-image file or corrupt image via gallery -> unsure or retake, never a label.
- B08: leaf still on the tree, cluttered background -> unsure or retake.
- B09: night photo under torch -> retake or unsure.

## Serious problems it cannot see
- C01: clean leaves, berries blackening (CBD) -> result card says it cannot see berries and to ask the officer.
- C02: clean leaves, tree wilting -> result card names wilt as out of scope, ask the officer.
- C03: yellowing leaves (nutrient hunger) -> not "Looks okay" without naming nutrients as unseen.
- C04: drought-stressed plot, leaves look healthy -> card names drought as unseen.

## Human in the loop
- D01: reach the result screen and do nothing -> no SMS, no upload, no state leaves the phone.
- D02: tap "I will act" -> no action taken by the app; PPE and "ask which product" text only.
- D03: tap "Open SMS" -> SMS app opens pre-filled; nothing sent until she presses send there.
- D04: go online with photo switch on, no further tap -> nothing uploads unless a separate tap and consent exist.
- D05: officer map "Send leaf-check nudge" -> SMS app opens; officer presses send.
- D06: officer confirm, correct, visit -> only on tap; status changes only for signed-in officers.

## Privacy and consent
- E01: answer "No" on the consent screen -> no check starts; nothing stored.
- E02: Kikuyu selected on the consent screen -> consent text and audio in Kikuyu, or in Swahili with a clear label; never untagged English.
- E03: consent audio button -> plays the consent in the chosen language.
- E04: type member number, reload app on a shared phone -> not pre-filled unless she ticked "remember"; a "forget" control exists.
- E05: referral SMS body -> member number, plot, date, counts, answer ID, confidence, decision; no name, no GPS, at most 160 characters.
- E06: photo upload (when sync exists) -> EXIF GPS stripped; only with the second consent, asked at that moment.
- E07: anonymous insert into `referrals` with `status: confirmed` or `synthetic: false` or `photo_urls` -> rejected by RLS.
- E08: anonymous select on `referrals` or `corrections` -> zero rows.
- E09: new officer sign-up -> no officer role, sees no referrals.
- E10: corrections CSV export -> excludes synthetic referrals and member numbers.

## Language
- F01: switch to Gĩkũyũ -> every untranslated string is tagged; fallback is Swahili, not English.
- F02: any Kikuyu string -> tagged "machine draft, pending native review"; never "reviewed".
- F03: any Swahili string -> tagged "draft, review pending" until a named reviewer signs off.
- F04: back-translate each Kikuyu act or ask card -> the "ask the officer / officer confirms" clause survives.
- F05: docs describe how each language was produced -> matches `translation_status` in answers.json.

## Data honesty and over-claiming
- G01: grep docs and pitch for "reviewed" -> every hit backed by a non-null `reviewed_by`.
- G02: every accuracy or coverage figure -> names its test set.
- G03: officer map -> synthetic deliveries and plots tagged; satellite and rainfall either real (with source) or labelled placeholder.
- G04: README and RESPONSIBLE_AI present-tense features (PIN, spoken consent, quality gate, sync) -> each exists in the live code.
- G05: pitch scripts -> no "the phone decides"; the farmer decides, the officer confirms.
- G06: any product name, dose or percentage threshold in a card -> absent, or sourced in GUIDANCE.md and tagged assumption.

## Secrets
- H01: repo and Lovable tree -> no service-role key, no ElevenLabs key, no `.env` with private keys; `VITE_*` only public values.
