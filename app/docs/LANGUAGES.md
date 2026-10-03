# Languages

Jani speaks Swahili in full, Kikuyu (Gĩkũyũ) for a subset of answers, and English. This file says why, how each was made, how far each has been checked, and how to add a new language.

Status: first draft. The final answer bank and the audio are not delivered yet (content-voice, tasks C1 to C3). The engine already reads text and audio per language and falls back safely.

## Why these languages

- **Swahili.** Kiswahili is Kenya's national language, and Kiswahili and English are the official languages [constitution-2010]. Noor uses it "when she needs it". Every answer has Swahili text and audio.
- **Kikuyu.** Noor speaks her home language at home. In the Nyeri area that is Gĩkũyũ. About 8.1 million people identify as Kikuyu in the 2019 census [statskenya-ethnicity]; this counts ethnicity, not speakers. We found no published count of Gĩkũyũ speakers. Kikuyu is also our live answer to "how does it fare in a less-supported language".
- **English.** For the officer, judges and reviewers.

## How each language is produced

All generation happens once, at build time, on a laptop. The phone only plays files that ship with the app. No AI service is called at runtime.

| Language | Text | Audio | Licence of the output | Review status |
|---|---|---|---|---|
| Swahili | Written from the English source and checked by a Swahili speaker | ElevenLabs text to speech, pre-rendered to `public/audio/sw/<answer id>.mp3` | ElevenLabs commercial terms; text is ours | Machine-drafted text; native review not done yet. Audio not rendered yet |
| Kikuyu | Drafted with Meta NLLB-200 (`kik_Latn`) [model_nllb_600m] | Meta MMS-TTS `facebook/mms-tts-kik`, pre-rendered to `public/audio/kik/<answer id>.mp3` [model_mms_tts_kik] | **CC BY-NC 4.0, non-commercial use.** Excluded from the MIT licence of the code | Marked "machine voice, pending native speaker review". Not rendered yet |
| English | Source text, written from KALRO guidance | ElevenLabs, optional | Ours | Team review |

Notes:
- MMS-TTS takes Gĩkũyũ in Latin script with the tilde vowels (ĩ, ũ) directly. No romanisation step [model_mms_tts_kik].
- MMS-TTS has a single voice. We found no published native-speaker quality check for it.
- NLLB-200 has not been evaluated on agricultural terms in Kikuyu. Some disease names may have no Kikuyu word. Those keep the Swahili or English term.
- Kikuyu must cover at least 5 core answers (requirement R5). The list is set by content-voice and is not delivered yet.

## How the app handles a missing clip

The engine plays the clip in the chosen language. If it is missing, it plays the Swahili clip. If that is missing too, it stays silent and the text stays on screen (`app/src/engine/audio.ts` on branch `cursor/engine-offline-core-d90f`). The UI is told to pick card text in the same order: chosen language, then Swahili, then English (`kb/CONTRACTS.md`). The UI should tell Noor when the language has changed; not built yet.

## Licence notes

- `facebook/mms-tts-kik` and `facebook/nllb-200-distilled-600M` are **CC BY-NC 4.0** [model_mms_tts_kik], [model_nllb_600m].
- We use them only at build time, for a non-commercial prototype. Their weights are not in the repo.
- Kikuyu clips and NLLB-drafted Kikuyu text are labelled "generated with Meta MMS-TTS / NLLB-200, CC BY-NC 4.0, non-commercial use". We treat model output as covered by the model licence; the law on this is unsettled. This is our reading, not legal advice.
- A commercial deployment needs a commercially licensed voice and translation, or the recording path below.

## How it fares in a less-supported language

Because every answer is in a fixed list, a new language does not need a new model. It needs one short recording per answer, made by a local speaker. The model reads leaves, not words, so it does not change.

The engine's current answer bank has 25 answer IDs (placeholder set on the engine branch). That is where "about 30 clips" comes from; the final count depends on the delivered bank.

### Adding a language with about 30 clips

1. Pick a speaker the cooperative trusts. Ideally the officer or a lead farmer.
2. Translate each answer from the Swahili or English source with that speaker. Write it into `answers.json` under a new language code.
3. Record one clip per answer ID on any phone, in a quiet room. Short sentences, one clip each.
4. Name each file `<answer id>.mp3` and put it in `public/audio/<language code>/`.
5. Add the language code to the engine's language list and to the language picker (one icon that plays the language's own name).
6. Have a second speaker listen to every clip against the text. Log the review in `kb/content/REVIEW_LOG.md`.
7. Rebuild. The service worker caches the new clips for offline use.

What this costs: one speaker for a few hours, no GPU, no data collection. What it does not fix: answers that need new agronomy for a new place; that is the rule table, see `REPLICATION.md`.

Steps 5 and 6 need small engine and UI changes that are not built yet. Today the engine knows three codes: `sw`, `kik`, `en`.

### Giving recordings back

Recordings made this way could be offered to Mozilla Common Voice, which collects read speech under CC0 for speech recognition. This needs the speaker's consent, and Common Voice uses its own sentence prompts, so our answer clips would not fit as they are. We have not checked whether Common Voice already has a Gĩkũyũ project. Not done yet.

## Speech input

Not in scope. Noor taps; she does not speak to the app. Common Voice Swahili 27.0 (730,758 clips, 1,064.9 hours recorded) [ds_cv_sw_27] would be a starting point for future voice input. It is not used in this build.
