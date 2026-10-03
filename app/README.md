# Jani

Jani is a small offline tool that helps a Kenyan coffee farmer check leaf photos at home and decide whether to act, wait, or ask the extension officer.

Live URL: not published yet.

Ondera, the place in the challenge story, is fictional. Kenya is the evidence anchor. The leaf model is not trained in this checkout.

## Problem statement

Because of Jani, Noor will know which coffee rows have leaf rust and can protect them before the short rains, on the weekend she checks, when she would otherwise find out only after the yield has dropped or when the extension officer next visits; we know because the extension agent to farmer ratio in Kenya is 1:1,380 (Agriculture Extension Manual, Ministry of Agriculture and Livestock Development, February 2025, [S02](https://fsrp.go.ke/sites/default/files/2025-08/Agriculture%20Extension%20Manual%20v1%20final.pdf)) and rust peaks after the rains with yield losses in excess of 75% where outbreaks are severe ([S03](https://www.mdpi.com/2073-4395/11/12/2590), Agronomy 2021).

The 75% figure is a statement in that review, cited there from an earlier work. It is not a new measurement from one Kenyan field season. In the main coffee regions, fungicide sprays for leaf rust start in mid-October, just before the short rains, with a second spray three weeks later (S03). East of the Rift, the review lists rust peaks in May to June and January to March, after the rains (S03).

KASEP does not state the current ratio. It states a target of 1 extension worker to 600 farmers by 2029 (S01, S02). S02 also quotes an FAO recommendation of 1:400. KASEP gives about 6.4 million farming households in the 2019 census (S01). A published figure for how often an officer visits a sub-county was NOT FOUND. The line "twice a year" is the challenge brief, not a statistic we verified.

Her yield drop is the brief's farm story. The national series is a different fact. In 2024 Kenya produced 49,500 t of green coffee at 435.7 kg/ha (FAOSTAT, S04). In 2015 to 2024 the lowest production was 2021 (34,500 t) and the lowest yield was 2020 (308.3 kg/ha) (S04).

Full table: [docs/DATA_CARD.md](docs/DATA_CARD.md).

## Noor's week

The brief's persona (a scenario, not a surveyed household) is a woman of 38 who farms 2 ha and has been a cooperative member for 11 years. She speaks a home language at home and Kiswahili when she needs it. Kiswahili is the national language (Constitution of Kenya 2010, Article 7, S10).

She has two phones in the story. Her own basic phone does calls, SMS and mobile money. Her daughter's smartphone is at home when her daughter is back from school at the weekend. For most of the day Noor is on the slope and the phone is at the house.

That two-phone pattern matches a national pattern, not a Nyeri survey. In the GSMA Consumer Survey 2024, 42% of women in Kenya owned a smartphone and 50% of men did (S06, adults 18+). The Findex 2024 API value for women who own a mobile phone is 91.8080408756395% (S07, Kenya, age 15+). The publisher rounds that on its own pages.

Saturday on the slope she picks 10 leaves from the rows that worry her (the sampling count is the capture protocol, a design choice). Saturday at the house, offline, she photographs them on a plain sheet in daylight. The app reads the photos, speaks a fixed answer, and she chooses act, wait, or ask. If she asks, she sends one SMS to the cooperative herself. During the week the reminder, if used, arrives on her basic phone. That reminder is a simulation and is tagged synthetic.

## What the AI does

The AI is computer vision. A small network on the phone reads leaf photos and estimates which leaf problem is present, and on how many of the sampled leaves. It is also built to say when it does not know.

A simpler tool does not turn a photo into a class:

- An SMS hotline needs her to name the disease. Naming it is the hard part.
- A spreadsheet needs a symptom code as input. The photo is the input she has.
- A web search needs a data bundle, a page she can read, and a name to type.
- An extension officer can do the job. The public ratio is 1:1,380 (S02, Kenya, 2025).

Advice is a rule table an officer can read. Season timing is a calendar file. A price card, if one is ever added, is a lookup and is outside the core tool. Nothing in the farmer flow calls a language model at runtime.

## Guardrails

- Every spoken and written answer is an ID in a fixed list. The phone does not generate advice.
- The check abstains when the top class is below the threshold, when leaves disagree, when the photo fails the quality gate, or when the image is not a coffee leaf. The threshold and the share of images it covers are [PENDING: ml].
- Uncertain leaves stay in their own count.
- Noor taps act, wait, or ask. The tool does not choose for her.
- The officer confirms or corrects a referral.
- The SMS composer opens pre-filled. She presses send. Nothing is sent on its own.
- The answer never names a pesticide product or a dose. Product and dose come from the cooperative or the officer.

## Small AI

| Item | Target (design) | Measured in this checkout |
|---|---|---|
| Model file | 3 MB or less, hard cap 5 MB | [PENDING: ml] |
| Offline bundle (app, model, audio) | 15 MB or less | [PENDING: engine] |
| Inference | Under 1 second per leaf on a low-end Android, or in Chrome with 4x CPU throttling if no handset is available. State which. | [PENDING: ml] |
| Offline use | After the first install, the leaf check runs with no data connection | [PENDING: engine] |

The model file is not in this checkout. The model is not trained here.

If a bundle were 15 MB, download time at 1 Mbit/s would be 120 seconds (15 MB x 8 = 120 Mbit). The 5 MB model cap alone would be 40 seconds. That is my calculation on the target, from the research notes (E8). It ignores protocol overhead. It is not a measured download.

A Safaricom daily bundle of 250 MB costs KSh 20 and lasts 24 hours (S11, page accessed 3 Oct 2026). A 15 MB target is 6.0% of 250 MB (my calculation, E8). A 1.5 GB daily bundle is KSh 99 (S11). Prices change. Re-check the tariff before quoting it on camera. National 3G or better covers over 96 percent of the population (World Bank, 2023, S08). County coverage for the coffee counties was NOT FOUND. Signal on a slope can be worse than a population figure.

## Languages

Swahili text for the answer bank is a draft. It was drawn from a glossary that is mostly Tanzanian, plus a few Kenyan attestations (`kutu ya majani ya kahawa`, `ugonjwa wa matunda ya kahawa`). It is pending native review.

Kikuyu is not translated yet. No Kikuyu audio has been produced. It is pending native review.

Detail: [docs/LANGUAGES.md](docs/LANGUAGES.md).

## Data

| Role | Set | Licence | What to remember |
|---|---|---|---|
| Train | JMuBEN (Kenya) | CC BY 4.0 | Rust, cercospora, phoma only. Counted 22,588 images (S22). |
| Train | JMuBEN2 (Kenya) | CC BY 4.0 | Healthy and miner. Counted 35,962 images (S23). |
| Train | BRACOL (Brazil) | CC BY 4.0 | No Phoma class (S26). |
| Held-out test | Uganda | CC BY 4.0 | Augmented. Not a clean held-out set (S25). |
| Held-out test | RoCoLe (Ecuador) | CC BY 4.0 | Robusta, not Arabica (S27). |

The full card, including gaps, is [docs/DATA_CARD.md](docs/DATA_CARD.md).

## Results

No accuracy is claimed. The model is not trained in this checkout.

When numbers exist they will name the test set: a held-out split of JMuBEN, JMuBEN2 and BRACOL; the Uganda set; and RoCoLe. Every metric in [docs/EVALUATION.md](docs/EVALUATION.md) is [PENDING: ml].

## Limits

- The tool looks at coffee leaves. It does not diagnose berries, roots, wilt or nutrient deficiency.
- It does not know the variety. SL28, Ruiru 11 and Batian are not labels in the image sets.
- Photos in the Kenyan sets are cropped to the lesion. A leaf still on the tree, a night photo, and a mixed infection are gaps.
- It does not name a product or a dose.
- Kikuyu is not in the app yet. Swahili is a draft pending review.
- Officer seed referrals and the SMS reminder are synthetic and must stay tagged as synthetic.
- Ondera is not a real registry. A real deployment needs the cooperative's member list, phones people already have, and trust in the advice.

## Tech stack and how to run

Planned stack: Vite, React, TypeScript, an installable PWA, `onnxruntime-web` for an int8 ONNX model, IndexedDB for checks and photos. This checkout's `package.json` includes React, Vite, `onnxruntime-web`, `idb` and `vite-plugin-pwa`. `vite.config.ts` currently registers the React plugin.

From `app/`:

```bash
npm install
npm run dev
```

`npm run build` writes a production build. `npm run lint` runs oxlint.

Do not put API keys in any `VITE_` variable. Keys stay in `backend/.env`, which is git-ignored.

## Our take

Localising this kind of tool means the photos, the labels and the words come from the place where it is used. For this design that is a cooperative officer correcting labels on local leaves, and short voice clips a speaker of that place can check. A further language is a set of about 30 short recordings (assumption, design choice), not a new model.

## Credits and licences

Code is MIT. See [LICENSE](LICENSE).

Dataset licences and the voice-model licences are separate. JMuBEN, JMuBEN2, BRACOL, the Uganda set, RoCoLe and PlantDoc are CC BY 4.0. Meta MMS-TTS and NLLB are CC-BY-NC-4.0 and are not part of the MIT code licence. See [docs/DATA_CARD.md](docs/DATA_CARD.md).

Problem figures come from the Kenyan Ministry of Agriculture (S01, S02), the 2021 Agronomy review (S03), FAOSTAT (S04), KNBS (S05, S09), GSMA (S06), World Bank Findex (S07), the World Bank Kenya CCDR digital note (S08), the Constitution (S10), Safaricom's published tariffs (S11) and AFA (S13). Season timing uses NASA POWER, which is modelled (S33).
