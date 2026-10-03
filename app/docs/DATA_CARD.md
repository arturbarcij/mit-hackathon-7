# Data card

What data Jani uses, where it comes from, its licence and size, and what it does not cover.

Every figure has a source id in square brackets. The ids point to `app/src/content/sources.json` (the same list the in-app Sources page shows). Figures we worked out ourselves say "derived". Anything made up says "synthetic". Anything we chose says "assumption".

All sources were accessed on 3 October 2026.

Status: first draft. Model training and the final split are still in progress (ml agent). Sections that depend on the trained model say "pending ml".

## 1. Problem data

Why the problem matters. Each row gives country, year and source.

| Figure | Country | Year | Source | Kind |
|---|---|---|---|---|
| The extension staff to farmer ratio "has not improved" | Kenya | 2023 | KASEP, Ministry of Agriculture [kasep-2023] | primary |
| Government target: 1 extension officer per 600 farmers by 2029 | Kenya | 2023 (target 2029) | KASEP [kasep-2023] | primary |
| 1 extension officer per 1,093 farm households, against an FAO-recommended 1:400 | Kenya | 2013/14 paper; data year not stated | Odongo, Agricultural Information Worldwide [odongo-aiw-2014]; repeated by The Guardian in 2024 [guardian-2024] | secondary, older |
| Extension ratio "at best 1: 1000" nationally, up to 1:2000 in some counties | Kenya | about 2019 (article undated) | Kilimo News [kilimonews-extension] | secondary |
| About 6.4 million farming households | Kenya | 2019 census, quoted 2023 | KASEP [kasep-2023] | primary (quoting census) |
| Coffee leaf rust can cause yield losses "in excess of 75%" where outbreaks are severe | Kenya (review) | 2021 | Gichuru et al., Agronomy 11(12):2590 [gichuru-2021] | secondary (review citing earlier work) |
| Rust peaks soon after the rains. East of the Rift: peaks May to June and January to March | Kenya | 2021 | [gichuru-2021] | secondary |
| Copper sprays start in mid October, before the short rains, with a second spray three weeks later | Kenya | 2021 | [gichuru-2021] | secondary |
| Green coffee production 34,500 t (2021) to 49,500 t (2024); yield 318.9 kg/ha (2021) to 435.7 kg/ha (2024) | Kenya | 2014 to 2024 | FAOSTAT QCL bulk file [faostat-qcl-africa] | primary |
| Output fell 6% in coffee year 2022/23, attributed to drought and coffee berry disease in the Central Highlands | Kenya | 2022/23 | AFA Coffee Year Book 2022/23 [afa-yearbook-2022-23] | primary |
| Smallholders produce 71% of coffee (estate to smallholder 29:71) | Kenya | 2022/23 | [afa-yearbook-2022-23] | primary |
| 605 cooperative societies and 1,122 factories (the same book also says 637 cooperatives) | Kenya | 2022/23 | [afa-yearbook-2022-23] | primary, internally inconsistent |
| About 1.2 million coffee farmers; smallholders in practice must join a cooperative and receive a membership number | Kenya | 2026 | European Forest Institute, citing the Coffee Directorate [efi-eudr-kenya-coffee] | secondary |
| Mobile phone ownership: women 93%, men 95% | Kenya | 2024 survey | GSMA Mobile Gender Gap Report 2025 [gsma-mggr-2025] | primary |
| Smartphone ownership: women 42%, men 50% | Kenya | 2024 survey | [gsma-mggr-2025] | primary (read from chart labels; check the chart by eye before showing on screen) |
| Mobile money account: women 83.5%, men 91.7% | Kenya | 2024 | World Bank Global Findex [findex-mm-female], [findex-mm-male] | primary |
| Population coverage: 2G 98.7%, 3G 97.7%, 4G 97.9% | Kenya (national only) | FY 2024/25 | Communications Authority of Kenya [ca-annual-2024-25] | primary |
| 29.5 million active feature phones and 43.8 million smartphones | Kenya | 30 June 2025 | [ca-annual-2024-25] | primary |
| Kiswahili is the national language; Kiswahili and English are official | Kenya | 2010 | Constitution, Article 7 [constitution-2010] | primary |
| About 8.1 million people identify as Kikuyu (ethnicity, not a count of speakers) | Kenya | 2019 census | Stats Kenya, quoting census Volume IV [statskenya-ethnicity]; rank confirmed in [knbs-census-2019-vol4] | secondary |
| Safaricom daily bundles: KES 5 for 7 MB, KES 10 for 15 MB, KES 20 for 50 MB; out-of-bundle rate KES 4.57 per MB | Kenya | page live on 3 Oct 2026 | [safaricom-data-faq], [safaricom-data-terms] | primary (operator pages disagree; we use the smaller bundle sizes) |

Problem data we looked for and did not find:
- A primary, current national extension ratio. KASEP gives none.
- Mobile coverage for the coffee counties (Nyeri, Kiambu, Murang'a, Kirinyaga, Embu). Only national figures are published in the sources checked. We do not claim coverage on Noor's slope.
- A count of Gĩkũyũ speakers. The census counts ethnicity, not home language.

We do not use the Kilimo Trust post on X (fewer than 5,000 officers for over 8 million farmers). It could not be checked without a login.

## 2. Build data

What the leaf model learns from and is tested on. Sizes are byte counts reported by the hosting API, not measured downloads. MB values are derived (bytes divided by 1,000,000).

| Dataset | Source | Licence | Size | Classes | Country | Capture conditions | Our use |
|---|---|---|---|---|---|---|---|
| JMuBEN | Mendeley Data, DOI 10.17632/t2r6rszp5c.1 [ds_jmuben], paper [paper_jmuben] | CC BY 4.0 | 22,591 images; 549,107,532 bytes (about 549 MB) | Cercospora 7,682; rust 8,337; Phoma 6,572. No healthy, no miner | Kenya (Mutira, Kirinyaga county) | Fujifilm X-T4 camera; cropped to the lesion, filtered, resized; augmented by rotation and flipping | Train, validation, in-domain test |
| JMuBEN2 | Mendeley Data, DOI 10.17632/tgv3zb82nd.1 [ds_jmuben2], paper [paper_jmuben] | CC BY 4.0 | 35,964 images; 1,291,694,151 bytes (about 1.29 GB) | Healthy 18,985; miner 16,979 | Kenya (Mutira, Kirinyaga county) | As JMuBEN; heavily augmented | Train, validation, in-domain test. The only Kenyan source of healthy leaves |
| BRACOL | Mendeley Data, DOI 10.17632/yy2k5y8mxg.1 [ds_bracol], paper [paper_bracol] | CC BY 4.0 | 1,747 leaf photos (1,685 in the leaf set); 164,516,964 bytes (about 165 MB) | Healthy 272; miner 387; rust 531; brown leaf spot 348; Cercospora 147 | Brazil (Espírito Santo) | Five smartphone models; leaf underside on a white background | Second training source. "Brown leaf spot" maps to Phoma only if the ml agent confirms it; otherwise dropped [paper_sbc_wsis_bracol] |
| Uganda coffee leaf dataset | Mendeley Data, DOI 10.17632/k36wnd6knb.1 [ds_uganda] | CC BY 4.0 | 3,312 images per the description, 3,322 files listed, 102 of them empty; 25,409,168 bytes (about 25 MB) | Healthy 1,179; rust 1,023; Phoma 1,110 | Uganda (district not stated) | Smartphone, daylight and low light, 256 x 256 px; augmented with rotation, flipping and brightness changes | Held-out cross-country test only. Never trained on |
| RoCoLe | Mendeley Data, DOI 10.17632/c5yvn32dzg.2 [ds_rocole], paper [paper_rocole] | CC BY 4.0 | 1,560 images (390 plants, 4 each); 2,270,913,636 bytes in total, of which JPEGs 1,566,761,118 bytes | Healthy 791; rust levels 1 to 4: 344, 166, 62, 30; red spider mite 167 | Ecuador (Manabí) | 5 MP smartphone, leaves on the plant, field background, sun, cloud and wind | Held-out field-condition test only (healthy versus rust). Red spider mite maps to "unsure" |
| PlantDoc (cropped) | GitHub [ds_plantdoc], paper [paper_plantdoc] | CC BY 4.0 on the repo; images scraped from the web, photographers' rights not cleared | 2,578 images in the repo; repo 955,318 KB | 28 folders over 13 species. No coffee | Not stated (web images) | Mixed web photos, field and indoor, cluttered backgrounds | Negatives for the "not a coffee leaf" class. **Not re-hosted in our repo** |
| Our own background photos | Team, 3 to 4 Oct 2026 | Ours (MIT with the code, if committed) | pending ml | Not leaves (soil, hands, sheets, tables) | Not applicable | Phone camera | Negatives for "not a coffee leaf". Not built yet |
| CoLeaf-DB | Mendeley Data, DOI 10.17632/brfgw46wzb.2 [ds_coleaf], paper [paper_coleaf] | CC BY 4.0 | 1,006 images; 2,061,021,043 bytes | Nine nutrient deficiencies, plus 6 healthy | Peru | Controlled set-up, Canon camera | Not used. Named only as a future extension for nutrient deficiency |

Speech and language resources (build time only, nothing runs on the phone):

| Resource | Source | Licence | Size | Our use |
|---|---|---|---|---|
| Meta MMS-TTS Kikuyu, `facebook/mms-tts-kik` | Hugging Face [model_mms_tts_kik] | **CC BY-NC 4.0** | `model.safetensors` 145,226,744 bytes | Pre-render Kikuyu audio clips at build time. Weights not in the repo |
| NLLB-200 distilled 600M, `facebook/nllb-200-distilled-600M` | Hugging Face [model_nllb_600m] | **CC BY-NC 4.0** | `pytorch_model.bin` 2,460,457,927 bytes | Draft Kikuyu text at build time, for human review. Weights not in the repo |
| Common Voice Swahili 27.0 | Mozilla Data Collective [ds_cv_sw_27] | CC0 1.0 plus download terms (do not re-share, do not identify speakers) [cv_access_change] | 730,758 clips, 1,064.9 hours recorded, 392.2 hours validated | Not used in this build (no speech recognition in scope). Reference for future voice input |
| ElevenLabs text to speech | Commercial service | Commercial terms | Not applicable | Pre-render Swahili and English audio at build time. No key ships in the app |

Season calendar: NASA POWER daily rainfall (`PRECTOTCORR`), one grid point at -0.42, 36.95 (Mathira West, Nyeri), 1991 to 2020 [nasa_power_daily_1991_2020], checked against monthly and climatology series [nasa_power_monthly_1991_2020], [nasa_power_climatology_2001_2020] and county descriptions [nyeri_pcra_2023], [nyeri_cidp_2013], [moalf_nyeri_crp_2016], [kmd_nyeri_mam_2026]. Method in `kb/research/SEASON.md`. CHIRPS was not pulled.

Agronomy for the answer bank: KALRO Coffee Research Institute review and leaflets [S1], [S2], [S3], the JMuBEN paper [S4], fact sheets [S5], [S6], [S7], FAO and WHO on pesticide handling [S8], and one non-Kenyan comparison [S9].

## 3. Licences and what they mean for us

- **CC BY 4.0 datasets** (JMuBEN, JMuBEN2, BRACOL, Uganda, RoCoLe, CoLeaf-DB): we may train on them and share results, with attribution and a note of changes. This card is the attribution.
- **PlantDoc:** the repo licence is CC BY 4.0, but the images were collected from the web. Third-party rights in the images are unclear. We train on it for a non-commercial prototype. We do not copy the images into our repo.
- **MMS-TTS Kikuyu and NLLB-200 are CC BY-NC 4.0 (non-commercial).** This is our reading, not legal advice:
  - Use in a non-commercial hackathon prototype is allowed with attribution.
  - The model weights are not in our repo, so they do not sit under our MIT licence.
  - Kikuyu audio clips (`app/public/audio/kik/*.mp3`) and Kikuyu text drafted with NLLB-200 are labelled "generated with Meta MMS-TTS / NLLB-200, CC BY-NC 4.0, non-commercial use". They are excluded from the MIT licence of the code. Whether model output is covered by the model licence is unsettled; we treat it as covered.
  - A commercial deployment would need a commercially licensed voice and translation, or native-speaker recordings and human translation. See `LANGUAGES.md`.
- **Common Voice:** CC0, but Mozilla's download terms ask us not to re-share files. We do not use or re-host it.
- **Code:** MIT. The MIT licence covers our code only, not third-party data or the Kikuyu machine output.

## 4. What the data does not cover

This section is specific on purpose. Each gap is a case where the tool may be wrong.

### Per dataset

| Dataset | Does not cover |
|---|---|
| JMuBEN | Healthy leaves and leaf miner (these are in JMuBEN2). Whole leaves with background: images are cropped to the lesion and filtered. Phone cameras. More than one farm. Named varieties: SL28, Ruiru 11 and Batian are not recorded. Coffee berry disease. Original and augmented copies are not marked |
| JMuBEN2 | Any disease. Same farm, camera and preprocessing as JMuBEN. The number of distinct leaves is much lower than 35,964 because of augmentation; the exact number is not published |
| BRACOL | East Africa. The upper leaf surface (photos show the underside). Leaves on the tree or in field light. Low light. Phoma as named in Kenya (naming unconfirmed). Coffee berry disease |
| Uganda | Cercospora and leaf miner. Confirmed Arabica: variety is not stated, and Uganda grows mostly Robusta. Un-augmented originals: augmented copies are mixed in and not marked. Full resolution (256 px only) |
| RoCoLe | Arabica. Africa. Cercospora, Phoma, leaf miner. Coffee berry disease. Rust level 4 has only 30 images |
| PlantDoc | Coffee (by design). East African weeds and shade trees a farmer might photograph by mistake. Non-leaf backgrounds such as soil, hands and sheets |
| Season calendar | Slope, altitude and the Mt Kenya rain shadow (one reanalysis grid point, modelled, not station data). The July to August middle rain reported in some Nyeri zones [moalf_nyeri_crp_2016]. Year-to-year shifts: onset moves by weeks. Other coffee counties |

### What the model cannot see

The model reads one photo of one picked leaf on a plain page. It cannot see:
- **Coffee berry disease.** Berries are not in any training set. The answer bank has an out-of-scope card (`berries_out_of_scope`) that refers to the officer.
- **Nutrient deficiencies.** No training data in use. CoLeaf-DB is a possible future source.
- **Wilt, root and stem problems,** and drought stress.
- **Mixed infections on one leaf.** Every training image has one label. Several problems across different leaves are handled by a rule that refers to the officer (`mixed_problems`), not by the model.
- **Kenyan varieties by name.** SL28, Ruiru 11 and Batian are not labelled in any set, so we cannot report performance per variety.
- **Leaves still on the tree with a cluttered background.** Only RoCoLe has these, and it is a test set.
- **Night or indoor-lamp photos.** Only the Uganda set has low light, and it is a test set.
- **Robusta versus Arabica.** Training data is Arabica. RoCoLe is Robusta and Uganda is unconfirmed.
- **Severity.** The model labels each leaf. It does not measure how much of a leaf is affected.
- **Pests other than leaf miner,** for example red spider mite.

How well the model does on the held-out sets, per class and per dataset: pending ml (see `EVALUATION.md`).

## 5. Leakage control

Planned method (from `kb/research/DATASETS.md`); the ml agent's manifest is not yet committed, so results are pending ml.
- JMuBEN and JMuBEN2 contain rotated and flipped copies with no marker. A plain perceptual hash misses these. Each image is compared with all 8 rotations and flips of the other, and near-duplicates are grouped. Whole groups go to one split.
- Uganda: drop the 102 empty files, then de-duplicate before testing. Results are reported on the de-duplicated count.
- BRACOL: keep its own train, validation and test split.
- RoCoLe: test only. If anyone fine-tunes on it later, split by plant (4 images per plant).
- Class imbalance: JMuBEN2 healthy (18,985 images) dwarfs BRACOL Cercospora (147). Weight or cap per class.

Duplicate counts removed per dataset: pending ml.
Final split sizes per class: pending ml.

A high JMuBEN test score mostly measures recognition of one farm, one camera and one preprocessing pipeline. The Uganda and RoCoLe results are the honest ones.

## 6. Synthetic data

Synthetic data is allowed only where it is labelled. We use it in three places, none of which trains the leaf model.

| What | Where | How it is tagged | Status |
|---|---|---|---|
| Officer dashboard seed referrals | Supabase `referrals` table (ui agent) | `synthetic: true` on every row, and a visible "synthetic" tag in the UI. Real referrals sent from the app carry `synthetic: false` (set in `app/src/engine/sync.ts` on branch `cursor/engine-offline-core-d90f`) | Not built yet |
| SMS reminder line (1 = done, 2 = not yet, 3 = need help) | Officer side, web | Labelled "simulated" on screen | Not built yet |
| Cooperative registry for the officer map: 80 plots, 66 members, plot polygons, tree counts and deliveries, seed 20261004 | `app/geo/` and `app/public/geo/` on branch `cursor/geo-outlier-map-d222` | `synthetic: true` at the top of `plots.geojson` and on every plot; `outliers.json` lists which parts are synthetic (plots, deliveries, members) and which are real (NDVI, rainfall). The UI must show a "synthetic" tag | Data built, map UI not built yet |

About the geo registry:
- Real: Sentinel-2 L2A dry-season NDVI over Mathira West, Nyeri, and NASA POWER rainfall.
- Cited inputs: 3.0 kg cherry per tree, Nyeri county average for 2013/14 [mugendi-2015], and 1,300 trees per ha for traditional varieties [afa-yearbook-2022-23]. Ruiru 11 is planted at 2,500 to 3,300 trees per ha [afa-yearbook-2022-23], so the baseline does not fit those plots.
- Assumption: the year-to-year cooperative factors and the 15% delivery noise.
- Its hit rates (for example 79 of 80 planted cases) are measured on data we built to test the rules. They say nothing about a real cooperative.
- We do not know that coffee grows inside any synthetic polygon.

Test fixtures in the engine (a tiny colour-rule ONNX model, synthetic leaf images for the quality gate) are test data only. No accuracy claim follows from them.
