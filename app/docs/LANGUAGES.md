# Languages

Status: draft by the docs agent, 3 Oct 2026; sections 2 and 3 corrected against the build on 4 Oct 2026 (overnight fixer). This build has no recorded audio: `public/audio` does not exist, and the speaker button uses the phone's own offline voice when one exists. Clip counts stay `TODO(content-voice)` until audio is rendered.

## 1. Which languages and why

| Language | Role | Why |
|---|---|---|
| Swahili (Kiswahili) | Full voice and text for every answer | National language of Kenya and official with English (Constitution 2010, Art. 7, S10). It is the language Noor uses "when she needs it". |
| Gikuyu (Kikuyu) | Voice and text for a subset of core answers | The brief says she speaks her local language at home. The Kikuyu ethnic group numbers 8,148,668 people (KNBS 2019 census, S09). That counts the group, not speakers. We found no speaker count. Our reference area, the Mount Kenya highlands, is Kikuyu country. Ondera itself is fictional. |
| English | Text and audio for reviewers and videos | Team and judges |

A Swahili-only tool does not speak Noor's home language. Kikuyu is our live answer to "how would it fare in a less-supported language".

## 2. How each language was produced

| Step | Swahili | Kikuyu | English |
|---|---|---|---|
| Source text | English answer bank written by us from published guidance (`answers.json`) | Same | Same |
| Translation | Drafted by Claude (`translation_status: draft_claude`); Gemini cross-check not run; native Kenyan Swahili review pending, not done | Drafted by Claude, not a native draft (`draft_claude_not_native`); the planned NLLB-200 pass (`kik_Latn`, CC BY-NC 4.0, S31) was not run; low confidence | n/a |
| Voice (planned, no clips in this build) | ElevenLabs `eleven_v3`, the model that lists Swahili (S54), to be rendered once at build time and shipped as MP3 | Meta MMS-TTS `facebook/mms-tts-kik`, CC BY-NC 4.0 (non-commercial), S30, to be rendered once at build time | ElevenLabs |
| Runtime | No translation at runtime. With no clips, the play button uses the phone's own offline voice if it has one for the language (on-device only, nothing sent). | Same (phones rarely have a Kikuyu voice) | Same |

Both Meta models are licensed for non-commercial use. See `DATA_CARD.md`, section 2. Fallback voice for Swahili if ElevenLabs fails: `facebook/mms-tts-swh`, same licence (S40). ElevenLabs has no Kikuyu voice (S54). A route past the non-commercial licence for Kikuyu: Google WAXAL has Kikuyu and Swahili TTS recordings under CC BY 4.0 or CC BY-SA 4.0 (S56), enough to fine-tune an open voice. Not done for this prototype.

Audio would be rendered by `backend/scripts/render_audio.py` (not run for this build). It skips clips whose text has not changed and writes `public/audio/manifest.json` with engine, licence and review status per clip.

## 3. Review status

| Language | Answers with text | Answers with audio | Reviewed by | Status |
|---|---|---|---|---|
| Swahili | All answers (`answers.json`) | None (no audio in this build) | Nobody yet (`reviewed_by` is empty on every answer). `TODO(Arthur)` name, date | Draft, native review pending (STATUS L3). The app tags it "Draft, pending review". |
| Kikuyu | A subset of answers | None (no audio in this build) | Nobody yet | **Claude draft, pending native speaker review.** The app tags it "Machine translation, pending review"; answers without Kikuyu show Swahili tagged "Not translated yet". |
| English | all | None (no audio in this build) | Team | Checked |

Source of truth for per-string status: `translation_status` in `src/content/answers.json` and `kb/content/REVIEW_LOG.md`.

## 4. How the tool fares in a less-supported language

Short answer: well enough to demonstrate, and cheap to improve, because we do not train a language model.

- Jani has a **fixed list of answers**. Nothing is generated in any language. So a new language needs a translation and a recording of each fixed answer, not a new model.
- `answers.json` holds 28 answer IDs on 3 Oct 2026, so the full set is about **30 short clips**. The count may change before freeze; `TODO(content-voice)` update it from the file at the end.
- A local speaker can record these in about an hour with a phone (assumption, not measured).
- Where only a machine voice exists (Kikuyu today), we say so on screen, limit it to a subset, and send everything else to Swahili or to the officer.

What can go wrong in a less-supported language:

| Risk | Our response |
|---|---|
| Machine translation changes the meaning of agronomy advice | Subset only, flagged, native review before real use |
| Machine voice is hard to understand or mispronounces | Flagged. Text shown with the audio. Swahili is the full path. |
| Dialect and register differ by county | Not tested. `TODO(lead)`: ask the cooperative which Kikuyu variety to record. |
| No ASR for the language | Not needed. Input is a photo and three buttons, not speech. |

## 5. How to add a language

1. Copy `answers.json` text keys to a new language code (for example `ee` or `fr`). No code change is needed beyond the language list in `i18n`.
2. Get a translation from a local speaker. A machine draft (NLLB covers many languages, non-commercial) can speed this up but never replaces review.
3. Record each clip (about 30), 5 to 10 seconds each, in a quiet room, from a script. Name files by answer ID.
4. Put the files in `public/audio/<code>/`. The service worker precaches them.
5. Mark `review_status` for each string. The UI tags any status containing `machine` ("Machine translation, pending review") or `draft` ("Draft, pending review").
6. Run `python -m qa.run` from `app/`. It checks that every answer ID has text and audio.

## 6. Giving recordings back

With the speaker's written consent, clips and scripts could be offered to Mozilla Common Voice (the data is CC0 per Mozilla; we did not re-confirm this on the page we read, S32). We did not find Swahili hour counts. Kikuyu clips from a native speaker would help close a gap for low-resource speech data. `TODO(lead)`: decide whether to do this after the hackathon.
