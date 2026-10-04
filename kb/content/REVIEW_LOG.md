# Content review log

Owner: content-voice. Updated Sat 3 Oct 2026, late evening. Nothing here has been reviewed by a native speaker yet.

## Summary

- 28 answers in `app/src/content/answers.json`. All have English and Swahili text. 8 core answers have Kikuyu text.
- Swahili status is `draft` for every entry. Drafted by Claude. The Gemini cross-check from the brief has **not been run**, so no entry is `cross_checked`.
- Kikuyu status is `machine_draft_pending_native_review`. The NLLB-200 pass from the brief was **not run** (no `transformers` on this machine). The Kikuyu lines were drafted by Claude directly. **Confidence in Kikuyu quality is low.** Sentences are kept very short on purpose. Treat them as a placeholder that shows the pipeline, not as correct Gĩkũyũ. The UI must show the "pending native review" label.
- No audio has been rendered. This log has no audio column to tick yet.
- Rules (`rules.json`) reviewed. Every numeric threshold carries `assumption: true` with "officer to confirm". The catch-all is `ask_officer`. No change needed.

## Changes made in the Sat night review

- Result cards cut to two sentences where possible (rust cards, cercospora, phoma, leaf miner).
- Added a "not sure" line to `mixed_problems`, `too_many_unsure`, `ask_officer`, and to the Kikuyu versions of `healthy_all` and `rust_high_pre_rains`.
- `cercospora`: dropped "worse on hungry or stressed trees". The only source is non-Kenyan (S18) and the sources disagree on shade. Treatment stays "ask the officer".
- `miner`: Swahili now says "viwavi wachimbaji wa majani" (caterpillars that mine leaves). The glossary found no Swahili term for leaf miner, so this is a descriptive phrase. Keeps the safety line against spraying on your own (S17).
- `decision_act`: no longer assumes the problem is rust. It says to ask the cooperative or officer what to do, and gives protective gear advice only "if you spray" (S20). This avoids contradicting the leaf miner card.
- `healthy_all`: marked as an assumption (it depends on the unsure-leaf cut-off).
- Swahili wording made consistent: "afisa wa kilimo" (officer), "chama cha ushirika" (cooperative), "dawa ya shaba" (copper), "kutu" (rust), "kupogoa" (prune), "kupalilia" (weed).
- Checked: no doses, no brands, no shade advice, no percentage thresholds stated as fact, no spray advice for phoma or leaf miner.

## Answer status

| Answer ID | Kind | Severity | Swahili | Kikuyu | Basis | Audio |
|---|---|---|---|---|---|---|
| how_to_pick_leaves | guidance | ok | draft | machine_draft_pending_native_review | sourced | audio: not rendered |
| how_to_photograph | guidance | ok | draft | n/a | plain | audio: not rendered |
| retake_blurry | guidance | watch | draft | n/a | plain | audio: not rendered |
| retake_dark | guidance | watch | draft | n/a | plain | audio: not rendered |
| not_a_leaf | guidance | watch | draft | n/a | plain | audio: not rendered |
| healthy_all | result | ok | draft | machine_draft_pending_native_review | assumption | audio: not rendered |
| rust_low | result | watch | draft | n/a | assumption | audio: not rendered |
| rust_high_pre_rains | result | act | draft | machine_draft_pending_native_review | assumption | audio: not rendered |
| rust_high_in_rains | result | act | draft | n/a | assumption | audio: not rendered |
| rust_high_dry | result | watch | draft | n/a | assumption | audio: not rendered |
| cercospora | result | ask | draft | n/a | sourced | audio: not rendered |
| phoma | result | ask | draft | n/a | sourced | audio: not rendered |
| miner | result | ask | draft | n/a | sourced | audio: not rendered |
| mixed_problems | result | ask | draft | n/a | assumption | audio: not rendered |
| too_many_unsure | result | ask | draft | machine_draft_pending_native_review | assumption | audio: not rendered |
| ask_officer | result | ask | draft | machine_draft_pending_native_review | assumption | audio: not rendered |
| berries_out_of_scope | guidance | ask | draft | n/a | sourced | audio: not rendered |
| other_crop | guidance | watch | draft | n/a | plain | audio: not rendered |
| consent_main | flow | ok | draft | n/a | plain | audio: not rendered |
| consent_photos | flow | ok | draft | n/a | plain | audio: not rendered |
| decision_act | flow | ok | draft | machine_draft_pending_native_review | sourced | audio: not rendered |
| decision_wait | flow | ok | draft | machine_draft_pending_native_review | plain | audio: not rendered |
| decision_ask | flow | ok | draft | machine_draft_pending_native_review | plain | audio: not rendered |
| referral_ready | flow | ok | draft | n/a | plain | audio: not rendered |
| language_name | flow | ok | draft | n/a | plain | audio: not rendered |
| nudge_leaf_check | nudge | ok | draft | n/a | plain | audio: not rendered |
| nudge_weather_everyone | nudge | ok | draft | n/a | plain | audio: not rendered |
| nudge_officer_visit | nudge | ok | draft | n/a | plain | audio: not rendered |

Swahili status scale: `draft`, `cross_checked`, `human_reviewed`. Kikuyu: `machine_draft_pending_native_review`, then `human_reviewed`.

## Kikuyu drafts (all pending native review)

- `how_to_pick_leaves`: Oya mathangũ 10 kuuma mĩhari ĩrĩa mĩũru makĩria. Mahaandĩke karatasi-inĩ, mũthia wa thĩ ũrorete igũrũ.
- `healthy_all`: Gũtirĩ thĩna wonekete mathangũ-inĩ marĩa. Thiĩ na mbere kũrora, makĩria thutha wa mbura.
- `rust_high_pre_rains`: Mathangũ maingĩ marĩ na kutu, na mbura ĩrĩ hakuhĩ. Ũria kooperatĩvu dawa ya copper na ũigana wayo.
- `too_many_unsure`: Tũtiramenya mathangũ maingĩ. Ũria mũrũgamĩrĩri wa ũrĩmi, kana ũhũre picha ingĩ mũthenya.
- `ask_officer`: Tũtingĩhota gũkuuga wega ũhoro wa mathangũ maya. Ũria mũrũgamĩrĩri wa ũrĩmi.
- `decision_act`: Wacagua gũthondeka. Ũria kooperatĩvu kana mũrũgamĩrĩri ũrĩa ũgwĩka. Ũngĩkunyũrũria, ĩhumbe gloves, buti na nguo ya moko marũku, na ũthambe thutha.
- `decision_wait`: Wacagua gũtegereza. Rora rĩngĩ wikendi ĩrĩa ĩkoka.
- `decision_ask`: Wacagua kũria mũrũgamĩrĩri wa ũrĩmi. Ũhoro waku ũrĩ mũhaano wa gũtũmwo.

Terms the reviewer must supply or confirm: kutu (rust, a Swahili loan here), "mũrũgamĩrĩri wa ũrĩmi" (agriculture officer, guessed), kooperatĩvu (cooperative, loan), copper, picha (photo, Swahili loan), gloves and buti (loans), "nguo ya moko marũku" (long sleeves, guessed). Timing detail ("just before the rains, again after three weeks") is left out of the Kikuyu rust card to keep it short; the Swahili and English cards carry it.
Licence note: Meta MMS-TTS and NLLB are CC-BY-NC-4.0 (non-commercial). Say so in LANGUAGES.md.

## Swahili review checklist (10 minutes, Sunday morning)

Reviewer: a Kenyan Swahili speaker, ideally from central Kenya. Read the English line, then the Swahili line, and mark each answer OK or write a fix. Score 1 to 5 for "would a farmer understand this when listening".

1. **Kenyan, not Tanzanian.** The only coffee Swahili we found is from Tanzania. Say if any word sounds Tanzanian or too formal for Kenya.
2. **Key terms.** Confirm or replace each:
   - kutu (coffee leaf rust)
   - dawa ya shaba (copper spray). Tanzanian sources say "mrututu"; we avoided it.
   - kunyunyiza (to spray) and kupogoa (to prune)
   - afisa wa kilimo (agriculture officer). Alternative: afisa wa ugani.
   - chama cha ushirika (cooperative)
   - mvua inakaribia (rains are close), wikendi (weekend)
3. **Words with no source.** These are our own wording and need a real check:
   - `miner`: "viwavi wachimbaji wa majani" (leaf miner). Is there a better farmer word?
   - `phoma`: "madoa meusi ya mviringo ... Phoma". Does a farmer need the name Phoma at all?
   - `cercospora`: "ugonjwa wa madoa ya kahawia" (brown eye spot).
   - "nyigu wasaidizi" (helpful wasps) and "nondo" (moths) in the leaf miner card.
   - "Chuma majani" (pick leaves) in `how_to_pick_leaves`.
   - Protective gear in `decision_act`: glavu, buti, nguo za mikono mirefu.
4. **Safety.** Confirm that no line tells the farmer to spray without asking, that `miner` clearly says not to spray alone, and that no line names a product or amount.
5. **Tone.** Polite "wewe" form, no jargon, each line under about 12 seconds when read aloud.
6. **SMS nudges.** Three nudges, each under 160 characters. Check they read naturally as a text message.
7. **Consent lines** (`consent_main`, `consent_photos`): is it clear that nothing is sent unless the farmer presses send, and that saying no is allowed?
8. **Sign-off.** Name, date, and whether the Swahili is fit to record. Set `reviewed_by` and `review_status.sw` to `human_reviewed` in `answers.json` for each checked entry.

Fixes go back to content-voice. Any changed line needs its audio re-rendered (the render script skips unchanged text by hash).

## Kikuyu reviewer checklist (if a native speaker is available)

Same sheet, 8 core entries only. First question: is this understandable at all? If most lines need rewriting, drop the Kikuyu audio from the demo or play one clip and say plainly it is a machine draft.

## Sun 4 Oct 2026, 00:50 CEST: overnight content pass (runner, content lane)

Branch `content`. Drafted by Claude. Still nothing reviewed by a native speaker. `answers.json` now has 29 answers; JSON shape unchanged (no new fields). Checks: `python -m qa.run --only content` passes with one warning (Kikuyu core 7 of 8, see F20); `npx vitest run` 135 passed, 1 todo.

### What changed and why

| Answer ID | Change | Request |
|---|---|---|
| retake_on_page | **New** guidance card, severity watch. en "Lay the leaf flat on a plain page and take the photo again." sw "Weka jani bapa kwenye karatasi safi upige picha tena." No Kikuyu (left absent rather than guessed). | EDGE_PLAN move 2 |
| cercospora | Farmer text no longer names brown eye spot: "Some leaves show other spots that need the officer's eye." Fertiliser line restored as "ask about fertiliser too: spots like these are often worse on underfed trees" (S18; no product, no amount). New not_sure without the disease name. | Move 5, F14 |
| phoma | Farmer text no longer names Phoma: "Some leaves show dark spots that need the officer's eye." Dying shoot tips now "show the officer that too, as it has more than one cause". Cool, windy, damp weather hint dropped (it implied a diagnosis). New not_sure without the name. | Move 5, F13 |
| miner | Farmer text no longer names leaf miner: "Some leaves show brown marks that need the officer's eye." Safety line kept as "Do not use insect sprays on your own: they can kill helpful wasps and make it worse." not_sure no longer names the pest. | Move 5, F12 wording |
| rust_high_pre_rains | Dry-day and heavy-rain line added ("on a dry day", "ask ... what to do if heavy rain falls"). not_sure adds "If your trees are Ruiru 11 or Batian, tell the officer before you spray for rust." Swahili uses "kutu ya majani" and "mvua za vuli au za masika". **Kikuyu text and not_sure removed.** | F10, F11, F20, F22 |
| rust_high_in_rains | "Spray on a dry day; if heavy rain falls the same day, ask." Ruiru 11 / Batian line in not_sure. "kutu ya majani". To fit 220 characters, "prune so the trees dry faster" was cut (pruning stays on rust_low and rust_high_dry). | F10, F11, F22 |
| rust_high_dry | "plan with the officer to spray on a dry day before the next rains". Ruiru 11 / Batian line in not_sure. Swahili "kutu ya majani", "mvua zijazo za vuli au za masika". | F10, F11, F22 |
| rust_low | Swahili only: "kutu" becomes "kutu ya majani" (text and not_sure). English unchanged. | F22 |
| mixed_problems | "Ask the cooperative or the officer before you spray anything. Do not use insect sprays on your own." | F12 |
| nudge_weather_everyone | "Weather may be one reason." replaces "It is likely the weather, not only your farm." | F17 |
| how_to_photograph | "in bright shade, not direct sun" replaces "in daylight". | F21 |
| retake_dark | "Move to bright shade, not direct sun" replaces "Move into daylight". | F21 |

Decisions made without a human (record for Arthur):
- **Move 5, officer hint.** The engine maps no officer-only field from `answers.json` (AnswerCard has text, notSure, sources, assumption, kind, reviewStatus). So the fine label is in no farmer-facing field. It stays only in the internal `note` (marked "Internal, not shown to the farmer"), and the officer already gets it through the referral counts C:, H:, L:. Card ids are unchanged, so `rules.json` still points at them.
- **Ruiru 11 / Batian line goes in not_sure**, not the main text. It fits there ("We cannot see your trees' variety") and keeps the main text under the 220-character limit. Result cards speak text plus not_sure, so it is still heard.
- **"mvua za vuli".** `rust_high_pre_rains` fires in both pre_short_rains and pre_long_rains, and `rust_high_dry` covers Dec to Feb (next rains: masika) and Jun to Sep (next rains: vuli). Naming only "vuli" would be wrong half the year, so the Swahili says "mvua za vuli au za masika". A short-rains-only card would need a rules.json change, which this lane may not make.
- **"kopa" vs "shaba".** Left as "dawa ya shaba" for the reviewer (L3) to choose. Not changed on a guess.
- **F20.** I am not confident writing Kikuyu for the longer rust card, so the Kikuyu lines were removed rather than half-matched. The UI falls back to Swahili audio and text. The QA check warns (Tier 2), it does not fail.
- **Swahili "jua kali" avoided** for "direct sun": in Kenya it also means the informal sector. Used "jua moja kwa moja".
- Not done in this pass (outside the F10 to F22 scope given): F1 rub check, F2 prune wording, F3, F5, F6, F7, F9 and the mathematician requests on `not_a_leaf`, `how_to_pick_leaves`, `healthy_all`, `rust_low`.

### Swahili lines that need the native reviewer (all `draft`)

New or changed this pass. Please check these first:
1. `retake_on_page`: "Weka jani bapa kwenye karatasi safi upige picha tena." Is "bapa" (flat) natural?
2. `how_to_photograph`, `retake_dark`: "kivuli chenye mwanga, si kwenye jua moja kwa moja" (bright shade, not direct sun). Note: this is about photo light, not shade advice for trees.
3. All rust cards: "kutu ya majani" (Kenyan form per the glossary, Umoja listing). Is "Kutu ya majani imeonekana kwenye majani mengi" natural, or too repetitive?
4. `rust_high_pre_rains`, `rust_high_dry`: "mvua za vuli au za masika". Does Kenyan "vuli" mean the October to December rains?
5. `rust_high_pre_rains`: "dawa ya shaba" or "kopa"? (F22, L3 to choose.) Also "siku kavu" (dry day) and "mvua kubwa ikinyesha" (if heavy rain falls).
6. Rust not_sure: "Kama miti yako ni Ruiru 11 au Batian, mwambie afisa wa kilimo kabla ya kunyunyiza dawa ya kutu ya majani."
7. `cercospora`: "mbolea" (fertiliser) and "miti isiyolishwa vizuri" (underfed trees). Neither is in the glossary.
8. `phoma`: "ncha za matawi zinakauka" (shoot tips drying back), "chanzo chake ni zaidi ya kimoja" (it has more than one cause).
9. `miner`, `mixed_problems`: "dawa za wadudu" (insect sprays). "wadudu" is attested in Kenyan Swahili (Radio Jambo); the phrase is not.
10. `nudge_weather_everyone`: "Hali ya hewa inaweza kuwa sababu moja."

### Audio now stale

No audio files exist in this snapshot (`app/public/audio/` absent). If any clips were rendered on the laptop, these are stale and must be re-rendered (the render script skips unchanged text by hash, so a normal run picks them up; nudges get no audio):
- en and sw: `retake_on_page` (new), `how_to_photograph`, `retake_dark`, `rust_high_pre_rains`, `rust_high_in_rains`, `rust_high_dry`, `cercospora`, `phoma`, `miner`, `mixed_problems`.
- sw only: `rust_low`.
- kik: `rust_high_pre_rains.mp3` must be **deleted**, not re-rendered (Kikuyu text removed).
- SMS text only, no audio: `nudge_weather_everyone`.

### Status rows changed

| Answer ID | Kind | Severity | Swahili | Kikuyu | Basis | Audio |
|---|---|---|---|---|---|---|
| retake_on_page | guidance | watch | draft | n/a | plain | audio: not rendered |
| rust_high_pre_rains | result | act | draft | removed (F20) | assumption | audio: not rendered |

## Sun 4 Oct, overnight fixer (gate blockers B1 and B2)

Changes to `app/src/content/answers.json`:
- New answer `too_few_leaves` (result, severity ask, assumption). Shown when a check has fewer than 10 leaves (`decide.ts` MIN_LEAVES), because the rule cut-offs assume 10 leaves. English: "We need photos of 10 leaves to give an answer. Take more photos, or ask the officer." Swahili is a builder draft for the native reviewer: "Tunahitaji picha za majani 10 ili kutoa jibu. Piga picha zaidi, au muulize afisa wa kilimo." Not sure line (en/sw draft): "A few leaves cannot show how much of the plot is affected." / "Majani machache hayawezi kuonyesha sehemu ya shamba iliyoathirika." No Kikuyu: left absent rather than guessed.
- `healthy_all` not sure line no longer states a count it cannot know: en "We only checked these leaves, and only leaves, not berries."; sw draft "Tumeangalia majani haya tu, na majani pekee, si matunda."; kik draft "Tweroretie mathangũ maya tu, ti matunda." (all pending native review).
- No agronomy changed. No audio exists, so nothing new is stale; if clips are rendered later, include `too_few_leaves` (en, sw) and `healthy_all` (en, sw, kik).

UI change: Swahili and other draft text now shows the tag "Draft, pending review" on screen (`src/ui/strings.ts` cardText).

| Answer ID | Kind | Severity | Swahili | Kikuyu | Basis | Audio |
|---|---|---|---|---|---|---|
| too_few_leaves | result | ask | draft | n/a | assumption | audio: not rendered |
| healthy_all | result | ok | draft (not sure line changed) | machine draft (not sure line changed) | assumption | audio: not rendered |
