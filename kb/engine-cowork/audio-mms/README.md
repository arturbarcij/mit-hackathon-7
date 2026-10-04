# MMS-TTS fallback audio for Jani (for content-voice)

This folder holds a free, offline-ready voice bank made with Meta MMS-TTS. It exists so the demo has clips even if ElevenLabs is late. Read `RESULTS.md` first: in this run the weights could not be downloaded, so the mp3 folders are empty and the manifest is a dry run.

## Roles of the two engines

- Swahili: ElevenLabs is the planned voice. When its clips exist, they replace `sw/` completely. MMS Swahili is a fallback only.
- Kikuyu: MMS-TTS (`facebook/mms-tts-kik`) is the Kikuyu voice. There is no ElevenLabs Kikuyu.
- English: not rendered here. The brief gives English to ElevenLabs.

## How to render

```
python3 render.py ../../app/src/content/answers.json --out . 
```

Needs: python3, torch, transformers, scipy, numpy, ffmpeg, and network access to huggingface.co on the first run (about 290 MB for both models). Re-runs skip unchanged text by hash. `--force` re-renders everything. `--langs kik` renders one language. `--dry-run` writes the manifest with no audio.

## How to adopt

1. Copy `sw/*.mp3` to `app/public/audio/sw/` and `kik/*.mp3` to `app/public/audio/kik/`. File names already match `<answer_id>.mp3`.
2. Delete the three `sw/nudge_*.mp3` files if you follow the brief (nudges are SMS only). Decide whether `kik/language_name.mp3` is wanted.
3. Merge `manifest.json` rows into `app/public/audio/manifest.json`. The app manifest wants `id, lang, bytes, duration, engine, text hash`. Map: `id` to `id`, `lang` to `lang`, `bytes` to `bytes`, `duration_s` to `duration`, `model` to `engine`, `text_hash` to `text hash`.
4. Listen to `SPOTCHECK_sw.mp3` and `SPOTCHECK_kik.mp3` (three clips each) before copying anything.
5. Check the total of all audio stays at or under 4 MB.

## What to copy into LANGUAGES.md

- Engine per language: Swahili ElevenLabs (planned) with MMS-TTS `facebook/mms-tts-swh` as fallback; Kikuyu MMS-TTS `facebook/mms-tts-kik`.
- Licence: both MMS models are CC-BY-NC-4.0 (non-commercial). Say so plainly. A commercial release needs a different voice.
- Voice status: "machine (MMS-TTS), pending native speaker review". Nobody has heard these clips who speaks the language.
- Text changes made for the voice only, never in `answers.json`: digits read as words ("10" to kumi / ikũmi, "1" to moja). If the Kikuyu tokenizer lacks ĩ and ũ, they are read as plain i and u; the manifest records this under `report.tokenizer.kik.tilde_strategy` and in each clip's `substitutions`.
- Determinism: seed 42, default speaking rate and noise scale, 16 kHz mono mp3 at 32 kbps.

## Manifest fields

`lang, id, file, bytes, duration_s, chars, s_per_char, peak_dbfs, silence_ratio, text_rendered, text_original, text_hash, substitutions[], flags[], model, licence, voice, seed, status`. Flags to look at: `duration_per_char_outlier`, `unk_tokens:N`, `unmapped_digits`, `nudge_is_sms_only_in_spec`.

## Note for the docs agent (5 lines)

1. Audio engines: Swahili ElevenLabs (planned, not yet rendered), fallback Meta MMS-TTS `facebook/mms-tts-swh`; Kikuyu Meta MMS-TTS `facebook/mms-tts-kik`.
2. Licence: MMS-TTS is CC-BY-NC-4.0, non-commercial. State this in LANGUAGES.md next to the NLLB note.
3. Voice status: machine voice, pending native speaker review; no clip has been heard by a Swahili or Kikuyu speaker.
4. Render status on 3 Oct: blocked in the sandbox by the egress proxy (huggingface.co denied); script and manifest ready, see `RESULTS.md`.
5. Reproducibility: `render.py <answers.json>`, seed 42, digits spoken as words, text hash skip on re-run, output 16 kHz mono mp3 at 32 kbps.
