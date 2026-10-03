# Data card

Accessed 3 Oct 2026. Source ids match the research notes. Confidence is primary (government, World Bank, FAO, peer-reviewed, or the dataset owner), secondary, or modelled.

If a figure is missing from those notes, this card says NOT FOUND. The leaf model is not trained in this checkout. No accuracy figure appears here.

## Corrections

These correct a shorter description that mixed two Kenyan records and treated the Uganda set as clean.

| Point | What the files show |
|---|---|
| JMuBEN classes | JMuBEN is rust, cercospora and phoma only. Healthy and miner are a second record, JMuBEN2 (S22, S23). |
| Uganda as a test set | The Uganda set is augmented (rotation, flipping, brightness). It is not a clean held-out set (S25). |
| BRACOL classes | BRACOL has no Phoma class (S26). |

## Problem data

| Figure | Country | Year | Source | Link | Confidence |
|---|---|---|---|---|---|
| Extension agent to farmer ratio 1:1,380 | Kenya | 2025 (February) | Agriculture Extension Manual, Ministry of Agriculture and Livestock Development (S02) | https://fsrp.go.ke/sites/default/files/2025-08/Agriculture%20Extension%20Manual%20v1%20final.pdf | primary |
| Target ratio 1:600 by 2029 | Kenya | Policy 2023; manual 2025. The target is the ASTGS 2019-2029 | KASEP (S01) and S02 | https://kilimo.go.ke/wp-content/uploads/2024/10/KENYA-AGRICULTURAL-SECTOR-EXTENSION-POLICY-2023.pdf | primary |
| FAO recommendation of 1:400, as quoted by the Kenyan manual | Cited in S02 | 2025 document | S02 | Same PDF as the row above, page 12 | primary |
| About 6.4 million farming households (2019 census, as given in KASEP) | Kenya | 2019 census, quoted in the 2023 policy | S01 | KASEP PDF | primary |
| Yield losses in excess of 75% where coffee leaf rust outbreaks are severe. The review cites an earlier work. Also foliage loss by up to 100% and berry loss by up to 70% in the same sentence | Kenya (review) | 2021 | Agronomy 11(12):2590 (S03) | https://www.mdpi.com/2073-4395/11/12/2590 | primary |
| Sprays for rust start in mid-October, just before the short rains, then again three weeks later. Long-rains sprays start in late February or early March | Kenya | 2021 | S03 | Same article | primary |
| East of the Rift: long rains March through May, short rains October through December, rust peaks May to June and January to March | Kenya | 2021 | S03 | Same article | primary |
| Green coffee production 49,500 t; yield 435.7 kg/ha | Kenya | 2024 | FAOSTAT QCL, flag A, official figure (S04) | https://www.fao.org/faostat/en/data/QCL | primary |
| Lowest production in 2015 to 2024: 34,500 t. Lowest yield: 308.3 kg/ha | Kenya | 2021 production; 2020 yield | S04 | Same | primary |
| Women who own a mobile phone: API value 91.8080408756395%. Men: 93.6989094857674%. Rural: 91.493057124906% | Kenya | 2024 | Global Findex (S07). The publisher rounds these on its pages | https://www.worldbank.org/en/publication/globalfindex | primary |
| Smartphone ownership: women 42%, men 50%, gender gap 16% | Kenya | Survey 2024, report 2025 | GSMA Mobile Gender Gap Report (S06). National adults 18+, not a Nyeri sample | https://www.gsma.com/wp-content/uploads/2025/12/The-Mobile-Gender-Gap-Report-2025.pdf | primary |
| Mobile money account: women 83.5097020779134%, men 91.6719907971862%, all adults 87.4994112747318% | Kenya | 2024 | S07 | Findex, as above | primary |
| 3G or better for over 96 percent of the population. Unique mobile internet 34.2% of the population at the start of 2023. Fixed broadband 1.5% | Kenya | 2023 | World Bank Kenya CCDR, digital sector note (S08) | https://openknowledge.worldbank.org/bitstreams/d3107c46-82ec-41e7-9aef-2ff04abc6c3c/download | primary |
| Kikuyu ethnic group 8,148,668 of a census total 47,564,296. Share 17.13% is my calculation from those two counts | Kenya | 2019 | KNBS census Volume IV, Table 2.31 (S09) | https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-4-Distribution-of-Population-by-Socio-Economic-Characteristics.pdf | primary |
| National language is Kiswahili. Official languages are Kiswahili and English | Kenya | 2010 | Constitution, Article 7 (S10) | https://klrc.go.ke/index.php/constitution-of-kenya/108-chapter-two-the-republic/173-7-national-official-and-other-languages | primary |
| Safaricom daily 250 MB for KSh 20, 24 hours. Daily 1.5 GB for KSh 99, 24 hours | Kenya | Page accessed 3 Oct 2026 | Safaricom terms (S11) | https://www.safaricom.co.ke/media-center-landing/terms-and-conditions/terms-and-conditions-for-safaricom-prepay-and-postpay-data-bundles | primary |
| About 70 percent of coffee is produced by smallholders under cooperatives | Kenya | Page refers to 2022/23 grades; year on the page not shown | AFA (S13) | https://afa.go.ke/updates/charting-the-path-towards-a-sustainable-coffee-sub-sector-in-kenya/ | primary |
| Smallholders estimated at 800,000 in 2022 | Kenya | Strategy dated January 2024, figure for 2022 | Coffee Development and Marketing Strategy (S14) | https://kilimo.go.ke/wp-content/uploads/2024/10/Final-Draft-Coffee-Developemnt-and-Marketing-Strategy-27-Jan-2024-1.pdf | primary |
| Nyeri area 2023/24, provisional: cooperatives 8,856.0 ha, estates 1,160.0 ha, total 10,016.0 ha. Cooperative share 88.4% is my calculation | Kenya, Nyeri | 2023/24 provisional | KNBS National Agriculture Production Report 2025, Table 5.1.1 (S05) | https://www.knbs.or.ke/wp-content/uploads/2025/10/National-Agriculture-Production-Report-2025.pdf | primary |

Do not average the smallholder shares. AFA says about 70 percent of production (S13). The strategy says two-thirds of acreage in 2021/22 (S14). KNBS 2023/24 provisional figures give cooperatives 85.0 thousand ha of 113.6 thousand ha and 37.2 thousand tonnes of 49.5 thousand tonnes. My calculation from those KNBS cells is 74.8% of area and 75.2% of production (S05). The headline we use is the AFA sentence.

On a 15 MB bundle target only (not a measurement of this app): 120 seconds at 1 Mbit/s, and 6.0% of a 250 MB bundle. Both are my calculation (research note E8). Prices and the bundle size target are above.

### Not found in the problem sources

- How often an extension officer visits a sub-county: NOT FOUND. "Twice a year" is the challenge brief.
- 3G coverage for Nyeri, Kiambu, Murang'a, Kirinyaga and Embu: NOT FOUND. The national population figure is not signal on a farm.
- A count of Gikuyu speakers: NOT FOUND. The census figure is ethnicity, not language.
- A published Kenyan threshold for the percent of leaves that should trigger a spray: NOT FOUND. Any incidence band in the rule table is an assumption for an officer to confirm.

## Build data

Counts marked "counted" were counted from the public file lists. Counts marked "stated" are the record's own text. Bytes are from the Mendeley public API unless noted.

| Dataset | Source | Licence | Size | Classes | Country and capture | How we use it |
|---|---|---|---|---|---|---|
| JMuBEN | Mendeley `t2r6rszp5c`, DOI 10.17632/t2r6rszp5c.1, published 26 Mar 2021 (S22). https://data.mendeley.com/datasets/t2r6rszp5c/1 | CC BY 4.0 | 549,107,532 bytes (about 549 MB). Counted images 22,588 (stated 22,591): cercospora 7,681, rust 8,336, phoma 6,571 | Rust, cercospora, phoma. Healthy and miner are not in this record | Kenya, Arabica, per the authors. County NOT FOUND. Camera, cropped to the lesion. Augmentation was used to increase size. Some rust files keep phone names from 26 Jan 2021 | Train. Split only after near-duplicate control |
| JMuBEN2 | Mendeley `tgv3zb82nd`, DOI 10.17632/tgv3zb82nd.1 (S23). https://data.mendeley.com/datasets/tgv3zb82nd/1 | CC BY 4.0 | 1,291,694,151 bytes (about 1.29 GB). Counted: healthy 18,984, miner 16,978 (35,962) | Healthy, miner | Kenya, Arabica, same author group. Augmented to increase size. Variety not stated | Train. Same leakage warning |
| JMuBEN + JMuBEN2 | Both records | CC BY 4.0 | See rows above | Five leaf classes | Counted total 58,550 images | Train. Raw counts are not natural prevalence. Healthy and miner outnumber the disease classes |
| BRACOL | Mendeley `yy2k5y8mxg`, DOI 10.17632/yy2k5y8mxg.1, published 6 Nov 2019 (S26). https://data.mendeley.com/datasets/yy2k5y8mxg/1 | CC BY 4.0 | One zip, 164,516,964 bytes. Inner file list was not opened. Stated: 1,747 whole-leaf images and 2,147 cropped symptom images | Healthy, leaf miner, leaf rust, brown leaf spot, cercospora leaf spot. No Phoma | Santa Maria of Marechal Floreano, Espirito Santo, Brazil. Five phone models. Abaxial side, white background, partly controlled | Train, after label mapping. The zip's own train, validation and test split is stated |
| Uganda coffee leaf set | Mendeley `k36wnd6knb`, DOI 10.17632/k36wnd6knb.1, published 7 Feb 2025, Soroti University (S25). https://data.mendeley.com/datasets/k36wnd6knb/1 | CC BY 4.0 | Listing: 3,322 files, 25,409,168 bytes (about 25 MB). Stated 3,312 images, JPEG 256 x 256 | Stated: healthy 1,179, coffee leaf rust 1,023, Phoma 1,110. File-name prefixes were counted as 1,179, 1,033 and 1,110. Prefix-to-class mapping is not stated in the record | Uganda, smartphone, daylight and low light. Also augmented (rotation, flipping, brightness). Variety not stated. Cercospora and miner absent | Held-out test only. Because of augmentation it is not a clean held-out set |
| RoCoLe | Mendeley `c5yvn32dzg` version 2, DOI 10.17632/c5yvn32dzg.2, published 17 May 2019 (S27). Article: https://pmc.ncbi.nlm.nih.gov/articles/PMC6727496/ (S39) | CC BY 4.0 | Record total 2,270,913,636 bytes (about 2.27 GB), including a 697,591,506 byte VOC archive. Leaf images: 1,560 | Healthy or unhealthy, red spider mite, rust severity at four levels (OIRSA). 4 images on each of 390 plants | One farm, CIIDEA, Calceta, Manabi, Ecuador. Robusta. Smartphone, upper and back sides, cloudy, sunny and windy days, working distance 200 to 300 mm | Held-out test only. Split by plant. Red spider mite is not one of our classes |
| PlantDoc | GitHub `pratikkayal/PlantDoc-Dataset` (S29). https://github.com/pratikkayal/PlantDoc-Dataset | CC BY 4.0 | GitHub API repo size 955,318 KB (about 955 MB, includes git history). Image counts per class were not checked | 28 train folders of non-coffee crops. No coffee class | Field-style non-coffee leaves | Negatives for a "not a coffee leaf" class. Hands, soil, paper and sky are not in this set |
| CoLeaf-DB | Mendeley `brfgw46wzb` version 2, DOI 10.17632/brfgw46wzb.2, published 30 May 2023 (S28). https://data.mendeley.com/datasets/brfgw46wzb/2 | CC BY 4.0 | 2,061,021,043 bytes (about 2.06 GB). Stated 1,006 leaf images. Healthy zip counted at 6 images | Nutrient classes (boron, iron, potassium, calcium, magnesium, manganese, nitrogen, and others) plus a tiny healthy set | Peru. Not diseases | Not used to train. It documents the nutrient gap |
| Wild field photos | iNaturalist research grade and Wikimedia Commons. The manifest is a local research file (S51), not a public dataset page | Per row. About 151 of 254 are CC BY-NC 4.0. ND licences were skipped | 254 rows: 188 iNaturalist, 66 Commons. Flickr: NOT FOUND | Hint prefixes only, not agronomist labels: rust 58, `coffee_plant_unverified` 140, `coffee_leaf_unverified` 56 | Almost none are Kenyan (about 8 place strings look Kenya-related). Many shots are whole plants, flowers or berries | Not training data. A later field-background check only after someone looks at each file |

NASA POWER (S33) is modelled daily precipitation for the season file, at a point latitude -0.42, longitude 36.95, 1991 to 2020. It is not a leaf dataset. https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=AG&longitude=36.95&latitude=-0.42&start=19910101&end=20201231&format=JSON

PlantVillage's licence was not checked. It is not listed as a build set.

## What the data does not cover

### By dataset

- JMuBEN: no healthy leaves, no leaf miner, no berries, no nutrient deficiency, no whole-leaf context (cropped to the lesion), variety not stated, lighting and phone model not stated, no split file, county NOT FOUND. Augmented copies are not marked.
- JMuBEN2: no rust, no cercospora, no phoma, no berries, no nutrients, variety not stated. Same unmarked augmentation.
- BRACOL: no Phoma, no Kenyan conditions, no field background. Variety not stated. Leaves can carry one or more biotic stresses, but the record is not a mixed-infection test we have opened.
- Uganda: no cercospora, no miner, variety not stated, only 256 x 256 files, no flagged un-augmented subset. Low light is stated. Night is not.
- RoCoLe: Robusta, not Arabica. One farm in Ecuador. No phoma, cercospora or miner. No berries. Not Kenya.
- PlantDoc: no coffee. No background-only scenes. Image counts not checked.
- CoLeaf-DB: nutrients in Peru, not Kenyan leaf diseases. The healthy folder is 6 images. It is a gap marker, not a training set.

### For the model as a whole

- Coffee berry disease and other berry problems. The tool looks at leaves.
- Nutrient deficiency. CoLeaf-DB is a future set from Peru, not this model.
- Root problems and wilt.
- Kenyan varieties are not labelled. SL28, Ruiru 11 and Batian are not classes in any of these sets. Strategy text discusses those names (S14). The photos do not.
- Leaves still on the tree, with clutter, shade and overlapping foliage. The Kenyan training images are cropped. BRACOL uses a white background.
- Night photos. No set is described as night.
- Mixed infections as their own class. A single label would hide a second problem.
- Robusta versus Arabica. Training sets named here are Arabica. The Ecuador test is Robusta.
- Augmented leakage. JMuBEN, JMuBEN2 and the Uganda set all used augmentation. A rotated copy of one leaf can land in a test folder if splits ignore the source image.
- On-tree Kenyan photos of SL28, Ruiru 11 or Batian under the house protocol (plain sheet, daylight): we do not have that set.
- Agronomy gaps that sit next to the images: no Kenyan primary leaflet was found for cercospora treatment, and none for Phoma. Leaf miner symptoms are in a Kenyan extension page (Infonet / icipe). A percent-of-leaves action threshold for Kenya was NOT FOUND.

## Synthetic data

Two things are synthetic, and only these:

1. Seed referrals on the officer dashboard, so the queue can be shown before any real farmer uses the tool.
2. The weekday SMS reminder and the 1 / 2 / 3 reply demo.

Every synthetic record carries `synthetic: true` and is tagged on screen as synthetic. Farmer leaf photos, if a person takes them, are not synthetic. The wild-photo manifest is real photographs with uncertain labels, not synthetic images.

## Leakage control

The method is specified. Perceptual hashing (pHash) puts near-duplicate images in the same split, so an augmented copy of one source photo does not sit in both train and test. RoCoLe is split by plant, because each plant has 4 images. The Uganda set stays out of training.

The measured duplicate count is [PENDING: ml]. Which JMuBEN and JMuBEN2 files are augmented copies of which originals: NOT FOUND. No source-image manifest is supplied.

## Voice and translation models

These are build-time tools. They are not the leaf model and they do not ship as the on-device network.

| Resource | Licence | Size | Note |
|---|---|---|---|
| Meta MMS-TTS Kikuyu, `facebook/mms-tts-kik` (S30) | CC-BY-NC-4.0 | `model.safetensors` 145,226,744 bytes | Machine voice. Kikuyu clips have not been produced in this checkout |
| Meta MMS-TTS Swahili, `facebook/mms-tts-swh` (S40) | CC-BY-NC-4.0 | not checked | Fallback only. Size NOT FOUND in the notes |
| Meta NLLB, `facebook/nllb-200-distilled-600M` (S31) | CC-BY-NC-4.0 | `pytorch_model.bin` 2,460,457,927 bytes | Machine translation only. Tokens `eng_Latn`, `kik_Latn` and `swh_Latn` appear in the repo file that was checked |
| ElevenLabs, for pre-rendered Swahili clips | NOT FOUND | n/a | Licence terms for the clips were not researched |
| Mozilla Common Voice (S32) | Mozilla states CC0 in general. Not re-confirmed on the page that was read | Swahili hours: NOT FOUND | Not used to train speech recognition |

CC-BY-NC-4.0 is non-commercial. That is acceptable for this hackathon and must be flagged before any commercial roll-out. The MIT licence on the code does not cover these models or the image datasets.
