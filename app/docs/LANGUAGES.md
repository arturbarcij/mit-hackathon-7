# Languages

Jani uses Kiswahili as the national language and Gĩkũyũ (Kikuyu) as the home language in the challenge story. A tool that speaks only the national language misses the language she uses at home.

Kiswahili is the national language. Kiswahili and English are the official languages (Constitution of Kenya 2010, Article 7, S10).

The Kikuyu community numbered 8,148,668 people in the 2019 census, out of 47,564,296 (KNBS, S09). That is ethnicity, not a count of speakers. A primary speaker count was NOT FOUND.

Infonet lists the vernacular names for the coffee plant as Kahawa (Swahili) and Kahûa / M ûhûa (Kikuyu). The space inside the Kikuyu form is in the source (S17, https://infonet-biovision.org/crops-fruits-vegetables/coffee-revised). Kikuyu terms for the diseases were NOT FOUND. The census table is S09 (https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-4-Distribution-of-Population-by-Socio-Economic-Characteristics.pdf). Article 7 is S10 (https://klrc.go.ke/index.php/constitution-of-kenya/108-chapter-two-the-republic/173-7-national-official-and-other-languages).

## Swahili

Status: draft text, pending native review. Audio has not been produced in this checkout.

The draft follows a glossary gathered on 3 Oct 2026. Almost all of the coffee-disease sentences in that glossary are Tanzanian (one Sokoine University booklet, copied on several blogs) or from a global app (Plantix). They are East African Swahili, not confirmed Kenyan farm usage.

Kenyan attestations that we do rely on:

- `kutu ya majani ya kahawa` for coffee leaf rust, on a Kenyan marketplace listing (Umoja, Kirimari, S47, https://umoja.co.ke/sw/a/grafted-ruiru-11-coffee-seedlings-24000018).
- `ugonjwa wa matunda ya kahawa` for coffee berry disease, on the same listing.
- `magonjwa ya kahawa` for coffee diseases in general, on Radio Jambo (S48, https://www.radiojambo.co.ke/habari/2023-06-12-walimuua-kaka-yangu-naibu-rias-gachagua-afichua).
- `wakulima wa kahawa` for coffee farmers, in Kenyan press (Taifa Leo).

Swahili for Phoma: NOT FOUND. Swahili for leaf miner: NOT FOUND. The copper word `mrututu` / `morututu` appears in the Tanzanian pages and is not confirmed as Kenyan. A Kenyan speaker has to choose the wording before release. Tanzanian spray schedules in those pages are not Kenyan advice and are not copied into the answer bank.

The planned voice path is ElevenLabs, at build time only. Clips would ship with the app and play offline. A person reviews each clip before release. ElevenLabs licence terms for the clips were NOT FOUND.

Meta MMS-TTS Swahili (`facebook/mms-tts-swh`, https://huggingface.co/facebook/mms-tts-swh) is a fallback if that render fails. It is CC-BY-NC-4.0 (S40). It is not the planned primary voice.

## Kikuyu

Status: not translated yet. No Kikuyu text and no Kikuyu audio have been produced. Pending native review.

The planned path, if a subset is rendered for the hackathon, is Meta MMS-TTS `facebook/mms-tts-kik`, at build time only (S30, https://huggingface.co/facebook/mms-tts-kik). That model is CC-BY-NC-4.0. The file `model.safetensors` is 145,226,744 bytes. It does not run on the phone. Only short clips would be bundled, and each clip would be marked as machine voice pending native speaker review.

NLLB (`facebook/nllb-200-distilled-600M`, https://huggingface.co/facebook/nllb-200-distilled-600M) can draft a translation. It is CC-BY-NC-4.0 (S31). `pytorch_model.bin` is 2,460,457,927 bytes. Language tokens `eng_Latn`, `kik_Latn` and `swh_Latn` appear in the model repo file that was checked. A draft from NLLB is not a reviewed translation.

## A less-supported language

The answer list is fixed. The leaf model does not speak. It returns a class.

Adding a language means recording the same short answers in that language. The design assumption is about 30 short recordings by a local speaker, not a new model. The number 30 is an assumption about the size of the answer list, not a measured corpus.

Those recordings are made at build time. ElevenLabs and MMS-TTS, if used, run at build time only. The phone plays files. It does not call a speech service.

## Giving recordings back

A speaker who records a language for this app could also donate the same short lines to Mozilla Common Voice, so the language has a public speech set. We do not train speech recognition. Swahili hours in Common Voice were NOT FOUND (S32, https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0). Mozilla states CC0 in general. That licence was not re-confirmed on the page that was read.

## Licences

MMS-TTS and NLLB are CC-BY-NC-4.0. They are not covered by the MIT licence on the code. Non-commercial terms are acceptable for this hackathon and must be flagged before any commercial use. Dataset licences are in [DATA_CARD.md](DATA_CARD.md).
