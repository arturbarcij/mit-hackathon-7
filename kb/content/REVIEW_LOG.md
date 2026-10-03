# Content review log

Date: 3 Oct 2026. Owner: content-voice. Status: draft. Not signed off for farmers.

No pesticide brand. No dose. No millilitres, grams, or product rate. No claim that shade reduces rust. No incidence percentage stated as fact. Swahili is a draft. Kikuyu is not translated. Audio was not rendered.

## What was drafted

`app/src/content/answers.json` is an array of 26 cards. Each has English and a Swahili draft. `text.kik` is null on every card. `translation_status.sw` is `draft`. `translation_status.kik` is `not_translated`. `reviewed_by` is null.

`app/src/content/rules.json` has 14 rules. First match wins. The last rule is `{"if": {}, "then": "ask_officer"}`.

`app/src/content/season.json` is a byte copy of `kb/research/season.json`. The science was not rewritten.

`app/src/content/i18n/en.json` and `sw.json` hold UI chrome only (buttons and step titles), not the answer cards. `kik.json` has the same keys set to null, plus `_note`: Kikuyu UI strings not translated. Pending native speaker.

`app/backend/scripts/render_audio.py` and `render_kikuyu.py` are in place. No mp3 files were written. There is no ElevenLabs key in this environment (`app/backend/.env` is absent). The scripts were not given a key.

## Answer ids

Guidance: `how_to_pick_leaves`, `how_to_photograph`, `retake_blurry`, `retake_dark`, `not_a_leaf`.

Results: `healthy_all`, `rust_low`, `rust_high_pre_rains`, `rust_high_in_rains`, `rust_high_dry`, `rust_high_pre_long_rains`, `cercospora`, `phoma`, `miner`, `mixed_problems`, `too_many_unsure`, `ask_officer`, `berries_out_of_scope`, `other_crop`.

Flow: `consent_main`, `consent_photos`, `decision_act`, `decision_wait`, `decision_ask`, `referral_ready`, `language_name`.

Every result card has `not_sure` in English and Swahili, and ends with the human choice: act, wait, or ask the officer.

## Assumptions (officer to confirm)

No Kenyan incidence threshold was found (GUIDANCE section 6). These cards are `assumption: true` because they depend on a count we chose:

- `rust_low`: a few leaves (`affected_gte` 1). Watch, and the officer confirms if unsure.
- `rust_high_pre_rains`, `rust_high_in_rains`, `rust_high_dry`, `rust_high_pre_long_rains`: many leaves (`affected_gte` 3). The spray dates are sourced. The count of leaves is not.
- `mixed_problems`: two or more problem labels (`distinct_problems_gte` 2).
- `too_many_unsure`: three or more unclear photos (`uncertain_gte` 3).

Rules that contain a number carry `"assumption": true` and the note: officer to confirm. No Kenyan incidence threshold was found (GUIDANCE section 6). That includes `uncertain_gte` 3, `distinct_problems_gte` 2, every `affected_gte` 3, `affected_gte` 1, and `affected_lte` 0 on `healthy_all`. The `healthy_all` card text does not state a percentage. Its rule is still flagged because the cut-off is a number we chose.

`how_to_pick_leaves` says ten leaves from the worst rows. That is the capture protocol, not a published disease threshold. It is not marked as an incidence assumption.

## Agronomy that is sourced

Rust looks like yellow to orange powder on the underside (S03, S17). Kenya spray starts in mid-October, before the short rains, with a second spray about three weeks later (S03). For the long rains, the first spray is late February or early March, then about three weeks later for copper (S03). Pruning helps leaves dry (S03), on the dry-season card. Product and amount come from the cooperative (S03). Wear covering clothes, gloves and boots (S20).

`rust_high_in_rains` is used for both `short_rains` and `long_rains`, so the card says "the rains are on" and does not name only one season.

`cercospora`, `phoma`, and `miner` give symptoms and "ask the officer". They give no spray time.

Leaf miner: do not spray on your own, because sprays can kill helpful wasps (S17).

`berries_out_of_scope`: dark sunken spots on green berries are coffee berry disease, and this tool does not check berries (S17). Swahili uses `ugonjwa wa matunda ya kahawa`. It does not use the Tanzanian word chulebuni.

## Weak sources, said on the card

`cercospora` says brown spots with a pale centre and a yellow ring, often when trees are short of food (S18, not Kenyan). `not_sure` says the sign is from a Pacific fact sheet, not a Kenyan guide. No shade sentence. The sources disagree on shade, and the Kenyan rust review says shade can raise rust severity, so shade is absent from every card.

`phoma` says dark round spots, or a shoot tip that dries and dies back, often in cool, windy, damp weather (S42, S43, not Kenyan). `not_sure` says the signs come from pages outside Kenya, not a Kenyan guide. No spray and no timing.

## Swahili: draft, needs a Kenyan speaker

Status on every card: `draft`. Not cross-checked with Gemini. Not human reviewed.

Prefer these Kenyan terms, already used: `kutu ya majani ya kahawa`, `ugonjwa wa matunda ya kahawa`, `magonjwa` only by sense in "this tool will not guess", `kahawa`, `mkulima` (on the consent card).

Do not use, and not used: chulebuni, mrututu, morututu, bakajani. `dawa ya shaba` was avoided. Cards say ask the cooperative which product and how much (`uliza ushirika ni dawa gani na kiasi gani`). A reviewer may still want a Kenyan word for a copper fungicide. If they choose `dawa ya shaba`, it stays a flagged draft until they sign it. Do not copy the Tanzanian line that says spray after the rains. Kenya sprays before the rains (S03, S17).

`afisa wa ugani` is used for "extension officer" and is unsourced. The glossary says the phrase was not found on a fetched page. Reviewer to confirm, or replace with the Kenyan title they use (the glossary suggests checking `afisa wa kilimo`). Same flag on the Swahili UI string `ask`.

Terms with no attested Swahili source, descriptive on purpose:

- Phoma: no Swahili term found. Card says `Madoa meusi ya duara, au ncha ya chipukizi inayokauka na kufa` and keeps the name Phoma. Reviewer to approve or replace.
- Leaf miner: no Swahili term found. Card says `viwavi wanaochimba ndani ya jani` (caterpillars that mine inside the leaf). Do not borrow another pest name. `nyigu wasaidizi` for the helpful wasps is also a draft.
- Brown eye spot: `ugonjwa wa madoa ya jicho` is an unattested calque. `bakajani` is Tanzanian and was not used. `madoa ya kahawia` is a plain description, not a sourced disease name.
- Cooperative: `ushirika` is a draft. Not in the glossary.
- Spray verb: `kunyunyizia` is from the Tanzanian booklet. Reviewer to pick the Kenyan verb (`kupulizia` is the other fetched form).
- Prune: `pogoa` / `kupogoa` is from the Tanzanian booklet.
- Short rains: `mvua za vuli`. Long rains: `mvua za masika`. Both need a Kenyan check.
- Protective clothes: `nguo zinazofunika mwili, glavu na buti`. No Swahili PPE source was found. `glavu` and `buti` are draft loanwords.
- UI drafts to check: `Imeigizwa` (simulated), `Mfano wa majaribio` (mock model), `Ficha kwa PIN`, `Jani la {n} kati ya {total}`.

Language button labels are endonyms in both English and Swahili files: Kiswahili, Gĩkũyũ, English.

## Kikuyu: not done

No Kikuyu was invented. There is no NLLB runtime here, and MMS-TTS was not run. `text.kik` is null. `translation_status.kik` is `not_translated`. UI values in `kik.json` are null.

These eight core ids still need Kikuyu, then native speaker review, before any clip:

1. `how_to_pick_leaves`
2. `healthy_all`
3. `rust_high_pre_rains`
4. `too_many_unsure`
5. `ask_officer`
6. `decision_act`
7. `decision_wait`
8. `decision_ask`

`render_kikuyu.py` documents Meta MMS-TTS `facebook/mms-tts-kik`, licence CC-BY-NC-4.0, and exits 0 while text or tools are missing. It does not invent audio. Any future clip is pending native speaker review.

## Audio: not rendered

`render_audio.py` reads `answers.json` and would call ElevenLabs for `sw` and `en` only when `ELEVENLABS_API_KEY` is loaded from `app/backend/.env`. The key is absent, so the script exits 0 and writes no clips and no manifest. It never prints a key. Unchanged text hashes are skipped once a manifest exists. Target format is mono mp3, 22050 Hz, 64 kbps, under `app/public/audio/manifest.json`.

No mp3 files were created.

## Source tags on the cards

`GUIDANCE#rust-symptoms` is GUIDANCE section 1.1. `GUIDANCE#rust-timing` is section 1.3. `GUIDANCE#rust-pruning` is section 1.5. `GUIDANCE#rust-product` is section 1.4 (the register, not a dose). `GUIDANCE#ppe` is section 7. `GUIDANCE#thresholds` is section 6. `GUIDANCE#cercospora` is section 2. `GUIDANCE#phoma` is section 3. `GUIDANCE#miner` is section 4. `GUIDANCE#cbd` is section 5.

Source ids: S03, S17, S18, S20, S42, S43.

## Still open before release

- Kenyan speaker reviews every Swahili card and the UI file.
- Officer confirms every numeric rule.
- Native speaker supplies Kikuyu for the eight ids, then reviews any MMS-TTS clip.
- ElevenLabs render only after a key is present and the Swahili text is signed off. Do not render the current draft as final voice.
