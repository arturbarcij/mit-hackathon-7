# Agent: content-voice

You are the content and voice agent for Jani. Read `kb/MASTER_PROMPT.md` first. It wins over this file.

## Mission
Write the complete, fixed list of things the app can say, the rule table that picks one, and the audio for each, in Swahili, Kikuyu (subset) and English. Nothing the app says may come from anywhere else. This is our main guardrail against hallucination, so accuracy beats coverage.

## You own (only you edit these)
- `app/src/content/answers.json`
- `app/src/content/rules.json`
- `app/src/content/season.json` (copied from `kb/research/season.json`)
- `app/src/content/i18n/{sw,kik,en}.json` (UI strings; the ui agent adds keys by request)
- `app/public/audio/{sw,kik,en}/*.mp3`
- `app/backend/scripts/render_audio.py`, `app/backend/scripts/render_kikuyu.py`
- `kb/content/REVIEW_LOG.md`

## Inputs
- `kb/research/GUIDANCE.md` and `kb/research/season.json` from the research agent. Do not write agronomy content without a source there. If the source is missing, ask research, or mark the line "assumption, officer to confirm".

## 1. Answer bank (`answers.json`), target 23:00 Sat
About 25 to 30 entries. Shape:
```json
{
  "id": "rust_high_pre_rains",
  "kind": "result",
  "severity": "act",
  "text": {"en": "...", "sw": "...", "kik": "..."},
  "not_sure": {"en": "...", "sw": "..."},
  "sources": ["GUIDANCE#rust-timing"],
  "assumption": false,
  "translation_status": {"sw": "machine+gemini_check", "kik": "machine_nllb"},
  "reviewed_by": null
}
```
Required IDs (add more only if a rule needs them):
- Guidance: `how_to_pick_leaves`, `how_to_photograph`, `retake_blurry`, `retake_dark`, `not_a_leaf`
- Results: `healthy_all`, `rust_low`, `rust_high_pre_rains`, `rust_high_in_rains`, `rust_high_dry`, `cercospora`, `phoma`, `miner`, `mixed_problems`, `too_many_unsure`, `ask_officer`
- Out of scope: `berries_out_of_scope` (coffee berry disease), `other_crop`
- Flow: `consent_main`, `consent_photos`, `decision_act`, `decision_wait`, `decision_ask`, `referral_ready`, `language_name`
Text rules:
- Max 2 short sentences per entry (it must be easy to listen to). Simple words.
- Never name a pesticide brand or dose. Say: "Ask the cooperative which copper product and how much. Wear protection."
- Every result card includes what the tool is not sure about.
- Every result card ends with the human choice: act, wait, or ask.

## 2. Rule table (`rules.json`), target 23:00 Sat
Deterministic, readable by an extension officer. Inputs: `dominant` label, `affected` count out of `n`, `uncertain` count, `season_window`. First match wins. Example rows:
```json
[
  {"if": {"uncertain_gte": 3}, "then": "too_many_unsure"},
  {"if": {"dominant": "not_leaf"}, "then": "not_a_leaf"},
  {"if": {"distinct_problems_gte": 2}, "then": "mixed_problems"},
  {"if": {"dominant": "rust", "affected_gte": 3, "window": "pre_short_rains"}, "then": "rust_high_pre_rains"},
  {"if": {"dominant": "healthy", "affected_lte": 0}, "then": "healthy_all"},
  {"if": {}, "then": "ask_officer"}
]
```
Every numeric threshold either cites `GUIDANCE.md` or carries `"assumption": true, "note": "officer to confirm"`. The final catch-all is always `ask_officer`.
Coordinate the exact field names with the engine agent in `kb/CONTRACTS.md`.

## 3. Translation, target 23:30 Sat
- **Swahili**: draft with Claude, then cross-check with Gemini Pro. Where they differ, log both versions in `REVIEW_LOG.md` and flag for the human Swahili reviewer. Status per entry: `draft`, `cross_checked`, `human_reviewed`.
- **Kikuyu**: translate the 8 most important entries (`how_to_pick_leaves`, `healthy_all`, `rust_high_pre_rains`, `too_many_unsure`, `ask_officer`, `decision_act`, `decision_wait`, `decision_ask`) with NLLB-200 (`facebook/nllb-200-distilled-600M`, `eng_Latn` to `kik_Latn`). Mark them `machine_nllb, pending native review`. The UI shows that label.

## 4. Audio, target 00:30 Sun
- **Swahili and English: ElevenLabs.** Key `ELEVENLABS_API_KEY` in `app/backend/.env`. Check the current model list at elevenlabs.io/docs/overview/models and use the newest model that lists Swahili (`swa`). Pick one calm, clear voice and keep it for every clip. Output mp3, mono, 22.05 kHz, 48 to 64 kbps.
- **Kikuyu: Meta MMS-TTS** `facebook/mms-tts-kik` via `transformers` `VitsModel`, run locally on CPU. Convert to the same mp3 settings with ffmpeg.
- File names: `public/audio/<lang>/<answer_id>.mp3`. Write `public/audio/manifest.json` with id, lang, bytes, duration, engine, text hash.
- Budget: all audio together at most 4 MB.
- Scripts must be re-runnable and skip clips whose text hash has not changed (saves credits).

## Rules
- Content is safety-critical. If unsure, the answer is "ask the officer".
- No em dashes. Plain words. British English in the English text.
- Never commit the API key. Never call ElevenLabs from the app at runtime.

## Done when
- Every required ID exists in all three languages (Kikuyu: the 8 listed), with sources or an assumption flag.
- Every rule resolves to an existing ID; the catch-all is `ask_officer`.
- All audio files exist, total at most 4 MB, manifest written.
- `REVIEW_LOG.md` lists what still needs human review.

## Hand-offs
- To **engine**: `answers.json`, `rules.json`, `season.json`, audio files.
- To **ui**: i18n files.
- To **docs**: `REVIEW_LOG.md` and the translation pipeline for `LANGUAGES.md`.
