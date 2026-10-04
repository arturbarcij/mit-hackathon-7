# Data card

Status: draft by the docs agent, 3 Oct 2026. Numbers come from `kb/research/EVIDENCE.md` and `DATASETS.md` (accessed 3 Oct 2026). Source IDs (S01 and so on) match `src/content/sources.json` and the in-app Sources page. Open items are marked `TODO(owner)` or `[PENDING: ml]`.

Rule used throughout: every figure has a source, or it is labelled "assumption" or "synthetic". Every accuracy figure names its test set.

## 1. Problem data

Why this matters, with source, year and country. "Primary" means government, World Bank, FAO, peer-reviewed or the dataset owner. "Modelled" means model or reanalysis output.

| # | Figure | Country | Year | Source | Type |
|---|---|---|---|---|---|
| E1 | 1 extension agent per 1,380 farmers. Target 1:600 (ASTGS 2019 to 2029). FAO recommendation 1:400. | Kenya | 2025 | Agriculture Extension Manual v1, Ministry of Agriculture and Livestock Development (S02); target also in KASEP (S01) | Primary |
| E1b | About 6.4 million farming households | Kenya | 2019 census | KASEP (S01) | Primary |
| E2 | Coffee leaf rust: yield losses "in excess of 75%" where outbreaks are severe. Sprays start in mid-October, repeat three weeks later. | Kenya | 2021 | Agronomy 11(12):2590 (S03). The 75% is the review citing earlier work, not a Kenyan field measurement. | Primary |
| E3 | Coffee yield 2024: 435.7 kg/ha, production 49,500 t. Lowest yield 2020: 308.3 kg/ha. Cooperatives 414.7 kg/ha, estates 578.1 kg/ha (2023/24, provisional). | Kenya | 2015 to 2024 | FAOSTAT QCL (S04), official flag; KNBS (S05) | Primary |
| E4 | 91.8% of women own a mobile phone. 42% of women and 50% of men own a smartphone. | Kenya | 2024 | Global Findex (S07); GSMA Mobile Gender Gap Report 2025 (S06). The GSMA figures are national adult figures, not Nyeri farmers. | Primary |
| E5 | Mobile money account: 83.5% of women, 91.7% of men | Kenya | 2024 | Global Findex (S07) | Primary |
| E6 | 4G covers 97.3% of the population (30 June 2025, S52); 3G or better over 96% (2023, S08). No county-level figure found. | Kenya | 2025 | Communications Authority of Kenya Q4 FY2024/25 (S52); World Bank Kenya CCDR digital note (S08) | Primary |
| E7 | Kikuyu ethnic group: 8,148,668 people (17.13% of 47,564,296; our calculation). This counts people of the group, not speakers. Kiswahili is the national language. | Kenya | 2019 | KNBS census (S09); Constitution Art. 7 (S10) | Primary |
| E8 | Safaricom daily bundles: KSh 20 for 250 MB, KSh 99 for 1.5 GB (24 hours). Re-check on the day of the video. | Kenya | 2026 | Safaricom terms (S11), tariffs (S12) | Primary |
| E9 | About 70% of Kenyan coffee comes from smallholders in cooperatives. About 800,000 smallholders (2022). Nyeri: 88.4% of 10,016 ha is cooperative land (our calculation). | Kenya | 2022 to 2024 | AFA (S13); Coffee Strategy 2024 to 2029 (S14); KNBS (S05) | Primary |
| P1 | A national farmer registry exists: KIAMIS, "over 6.5 million farmers" by mid-2025, handed to the Government in November 2025. | Kenya | 2025 | FAO news, 12 Jan 2026 (PA01) | Primary |
| P2 | Single-leaf accuracy as low as 21% (CBSD) and 52 to 59% (CMD) in the field; 74 to 88% with six leaves. Cassava, not coffee. We cite it as design precedent only. | Kenya, Tanzania | 2020 | Mrisho et al., Frontiers in Plant Science (source: PA02) | Primary |

Reading notes for judges:

- The national yield series is **not a steady decline**. It dipped in 2020 and 2021 and recovered in 2022. Noor's drop is a farm-level story. We make no national decline claim.
- "Extension officer visits twice a year at best" comes from the challenge brief. We found no published Kenyan statistic for visit frequency.
- We did not use the "fewer than 5,000 officers for over 8 million farmers" figure. It is a secondary social media post (S36) that we could not verify.
- Three sources give different cooperative shares (AFA about 70%, strategy two-thirds of acreage in 2021/22, KNBS about 75% in 2023/24). They differ by definition and year. We quote AFA for a headline and KNBS for precise or Nyeri figures. We do not average them.

**Not found** (so not claimed): extension coverage by county; coverage by county for the five coffee counties; a count of Gikuyu speakers; members per cooperative; Kenyan incidence thresholds for spraying.

## 2. Build data

What the model learns from and is tested on. All licences below are CC BY 4.0 unless stated. Sizes are file sizes from the Mendeley API. Image counts are our own counts of zip contents unless marked "stated".

| Dataset | Source | Licence | Size | Images | Classes | Country | Capture conditions | Our use |
|---|---|---|---|---|---|---|---|---|
| JMuBEN | Mendeley, DOI 10.17632/t2r6rszp5c.1 (S22, S24) | CC BY 4.0 | 549 MB | 22,588 (stated 22,591) | rust, cercospora, phoma | Kenya (Arabica; county not confirmed) | Camera, pathologist-assisted, cropped to the lesion, augmented. Variety, phone and light not stated. | Train |
| JMuBEN2 | Mendeley, DOI 10.17632/tgv3zb82nd.1 (S23) | CC BY 4.0 | 1.29 GB | 35,962 (healthy 18,984, miner 16,978) | healthy, leaf miner | Kenya (Arabica) | As JMuBEN. Augmented to increase size. | Train |
| BRACOL | Mendeley, DOI 10.17632/yy2k5y8mxg.1 (S26) | CC BY 4.0 | 165 MB | 1,747 whole-leaf + 2,147 symptom crops (stated) | healthy, miner, rust, brown leaf spot, cercospora leaf spot | Brazil (Arabica) | Five phones, underside of the leaf on a white background, partly controlled | Train. Its white-background protocol is close to ours. |
| Uganda coffee leaf set | Mendeley, DOI 10.17632/k36wnd6knb.1 (S25) | CC BY 4.0 | 25 MB | 3,322 files (stated 3,312) | healthy, rust, phoma | Uganda (Soroti University) | Smartphone, daylight and low light, 256 x 256, augmented | Test only (cross-country) |
| RoCoLe | Mendeley, DOI 10.17632/c5yvn32dzg.2 (S27, S39) | CC BY 4.0 | 2.27 GB (full record) | 1,560 | healthy/unhealthy, red spider mite, rust severity 1 to 4 | Ecuador (Robusta, one farm) | 5 MP smartphone, field, 4 images per plant | Test only (field conditions) |
| PlantDoc | GitHub, pratikkayal/PlantDoc-Dataset (S29) | CC BY 4.0 | about 955 MB (repo with history) | [PENDING: ml] (not counted) | 28 non-coffee classes | Mixed | Web and field photos | Negatives for "not a coffee leaf" |
| Background and non-leaf photos | Own photos and `app/ml/make_negatives.py` output | [PENDING: ml] | [PENDING: ml] | [PENDING: ml] | not_leaf | Denmark and elsewhere (assumption: we took them) | Hands, soil, paper, sky | Negatives |
| Own leaf photos on a plain sheet | Our team | Ours | [PENDING: ml] | [PENDING: ml] | label honestly (not coffee unless coffee) | Not Kenya | Smoke test of the capture protocol only | Smoke test, not an accuracy test |
| CoLeaf-DB | Mendeley, DOI 10.17632/brfgw46wzb.2 (S28) | CC BY 4.0 | 2.06 GB | 1,006 (stated); healthy zip has 6 | 8+ nutrient deficiencies | Peru | Not used by the model | Not used. Listed for the future extension only. |

Combined JMuBEN and JMuBEN2 count: 58,550 images (our count; a related paper snippet says 58,549, unopened). (source: MASTER_PROMPT 5.2)

Class balance warning: healthy (18,984) and miner (16,978) outnumber rust (8,336), cercospora (7,681) and phoma (6,571). Raw counts are not natural prevalence. `TODO(ml)`: state the sampling or weighting used.

Language and voice resources (not training data):

| Resource | Licence | Size | Use |
|---|---|---|---|
| `facebook/mms-tts-kik` (S30) | **CC BY-NC 4.0 (non-commercial)** | 145 MB weights | Kikuyu clips, pre-rendered. Machine voice, no native review yet. |
| `facebook/mms-tts-swh` (S40) | **CC BY-NC 4.0 (non-commercial)** | not checked | Swahili fallback only if ElevenLabs fails |
| `facebook/nllb-200-distilled-600M` (S31) | **CC BY-NC 4.0 (non-commercial)** | 2.46 GB | First-draft translation. Every string needs a native reviewer. |
| ElevenLabs `eleven_v3` (Swahili, English) | Paid plans include a commercial licence; the free plan is non-commercial and needs "elevenlabs.io" in the title when published; Beta services exclude commercial use (S55). Swahili is supported by Eleven v3, not by Multilingual v2 or Flash v2.5 (S54). | n/a | Pre-rendered at build time |

The two Meta models are for non-commercial use. That is fine for a hackathon prototype with pre-rendered clips. It would need a different route for a commercial roll-out.

## 3. What the data does not cover (scored)

### 3.1 Per dataset

| Dataset | What it does not cover |
|---|---|
| JMuBEN | No healthy or miner leaves (they are in JMuBEN2). Cropped to the lesion, so little background variety and no whole-leaf context. No variety, phone model or lighting stated. County and capture dates not confirmed. No manifest of which files are augmented copies. No split file. |
| JMuBEN2 | No rust, cercospora or phoma. Same augmentation and variety gaps. Healthy and miner counts are inflated against the disease classes. |
| BRACOL | No phoma class. Brazilian conditions. White background only. The mapping of "brown leaf spot" and "cercospora leaf spot" to our classes is `[PENDING: ml]`. |
| Uganda set | Only three classes: no cercospora, no miner, so those cannot be tested across countries. Augmented (rotation, flip, brightness), so copies of one leaf may sit in the test set. 256 x 256 only. Prefix-to-class mapping is inferred, not stated. |
| RoCoLe | Robusta, not Arabica. One farm in Ecuador. No phoma, cercospora or miner. Four images per plant, so we split by plant. |
| PlantDoc | No coffee. No background-only scenes, so we add our own. |

### 3.2 For the model as a whole

The model cannot see, and the app says "ask the officer" for:

- coffee berry disease and any problem on berries (the model reads leaves only);
- nutrient deficiency (CoLeaf-DB exists for a future extension, we do not use it);
- root problems and wilt;
- drought or frost stress;
- mixed infections on one leaf;
- night photos and strong shade;
- leaves still on the tree against a cluttered background (our protocol asks for a plain sheet);
- Kenyan varieties such as SL28, Ruiru 11 and Batian, which no dataset labels;
- Robusta, other than as a field-condition test;
- pest traps and insects other than the leaf miner damage on the leaf.

Other gaps that affect trust:

- Phoma and brown eye spot: we found no Kenyan extension source. Advice for those classes is "ask the officer".
- No Kenyan incidence threshold exists in the sources we found. Every cut-off in `rules.json` is labelled "assumption, officer to confirm".
- Season windows come from NASA POWER 1991 to 2020 at one point (modelled), plus spray timing from the Kenyan rust review (S03). CHIRPS was not used.
- Training and test photos are mostly not from Noor's farm. Performance on her leaves is unknown until officers label local photos.
- Real-world accuracy on a phone camera held by a farmer is `[PENDING: ml]` and may be lower than any figure in `EVALUATION.md`.

## 4. Synthetic data

Synthetic data is used for demonstration only, never for training or for any accuracy figure.

| What | Where | How it is tagged |
|---|---|---|
| Seed referrals in the officer dashboard | Lovable Cloud / Supabase table | Field `synthetic: true`; a visible "synthetic" tag in the UI on every row |
| Simulated SMS reminder panel and 1/2/3 replies | Web panel | Labelled "simulated" on screen |
| Cooperative delivery records and plot shapes for the outlier map | `app/geo` outputs | Field `synthetic: true`; map legend says synthetic. `TODO(geo)`: confirm tags. |
| Satellite greenness (Sentinel-2) and rainfall (CHIRPS or NASA POWER) | `app/geo` | **Real** data, not synthetic. Rainfall from NASA POWER is modelled. |

Check for the QA agent: `SELECT count(*) FROM referrals WHERE synthetic IS NOT TRUE` must return only rows created in real tests.

## 5. Leakage control

The datasets are augmented and carry no source-image IDs, so near-copies of one photo can land in both train and test.

- Near-duplicate hashing before splitting: `[PENDING: ml]` (method, threshold, number of images removed).
- Split sizes and the manifest: `app/ml/data_manifest.csv` `[PENDING: ml]`.
- RoCoLe is split by plant, not by image.
- Uganda and RoCoLe are never used for training. They are test sets from another country.
- The Uganda set is itself augmented, so its scores may be optimistic. We say so in `EVALUATION.md`.

## 6. Licence summary

- Our code: MIT (see `LICENSE`).
- Datasets above: CC BY 4.0. Credit is in the app Sources page and in `README.md`.
- Meta MMS-TTS and NLLB: CC BY-NC 4.0, non-commercial.
- Audio clips we render: ElevenLabs output may be published on a paid plan; on the free plan only non-commercial with "elevenlabs.io" credited (S55). We credit ElevenLabs in the README and the app Sources page either way. Kikuyu clips inherit the MMS CC BY-NC 4.0 terms.
