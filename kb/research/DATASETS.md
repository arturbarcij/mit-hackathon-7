# Datasets (research Task 3)

Accessed 2026-10-03. Figures come from the Mendeley Data public API (`https://data.mendeley.com/public-api/datasets/<id>`), the Hugging Face and GitHub APIs, and the papers listed in `_sources_datasets.json`. File sizes are the byte counts the APIs report, not measured downloads. Nothing was downloaded except RoCoLe's 39 KB label sheet (`RoCoLe-classes.xlsx`), used to count classes.

"No login" means an HTTP GET or HEAD on the link returned 200 or 206 with no cookie or token, tested on 2026-10-03.

Mendeley "download all" pattern (tested on k36wnd6knb and c5yvn32dzg, 1-byte ranged GET returned 206): `https://data.mendeley.com/public-api/zip/<id>/download/<version>`. It redirects to a short-lived signed S3 URL, so HEAD returns 403; use GET (`curl -L -o x.zip <url>`).

## Contradictions with the master prompt (Section 6.1)

1. **JMuBEN is not 5 classes.** The 22,591 images are 3 disease classes only (Cercospora, rust, Phoma). Healthy and leaf miner are in a separate dataset, **JMuBEN2** (35,964 images). Combined: 58,555 images, 5 classes. To get a healthy class from Kenya, ml must download JMuBEN2 as well.
2. **The Uganda set is augmented**, which the master prompt does not say. Mendeley lists 3,322 files, not 3,312; the rust folder has 1,033 files, not 1,023; and 102 files are 0 bytes. About half the files share an exact byte size with another file, which suggests exact duplicates. It is a weaker held-out test than the master prompt implies.
3. **BRACOL** is 1,747 photos, of which 1,685 are labelled in the leaf dataset. Its "brown leaf spot" class is a separate class from "cercospora leaf spot"; see the naming warning under BRACOL.
4. RoCoLe figures match (1,560 images, CC BY 4.0, Robusta, Ecuador).
5. PlantVillage is named in the master prompt next to PlantDoc. I did not check PlantVillage (not in my brief). NOT CHECKED.

## Licence flags

| Item | Licence | Blocks training? | Blocks redistribution? |
|---|---|---|---|
| JMuBEN, JMuBEN2, BRACOL, Uganda, RoCoLe, CoLeaf-DB | CC BY 4.0 | No | No, with attribution and a note of changes |
| PlantDoc | CC BY 4.0 on the repo, but images were scraped from the internet | No for a non-commercial prototype | Do not re-host the images; third-party copyright in the images is unclear |
| `facebook/mms-tts-kik` | **CC BY-NC 4.0** | Not applicable (we only run it) | **Yes for commercial use.** See below |
| NLLB-200 (`facebook/nllb-200-distilled-600M`) | **CC BY-NC 4.0** | Not applicable | **Yes for commercial use.** See below |
| Common Voice Swahili | CC0 1.0, plus Mozilla Data Collective download terms | No | Mozilla asks downloaders not to re-share files and not to identify speakers |

**What CC BY-NC 4.0 means for us (MMS-TTS and NLLB-200).** I am not a lawyer; this is my reading. The licence allows use, copying and adaptation for non-commercial purposes with attribution. A hackathon prototype for a World Bank challenge is non-commercial, so pre-rendering Kikuyu clips with MMS-TTS and drafting Kikuyu text with NLLB-200 at build time is acceptable now. Three consequences:
- Do not put the model weights in the repo (they would sit under our MIT licence). We do not need them in the repo anyway.
- The generated Kikuyu clips (`app/public/audio/kik/*.mp3`) and NLLB-drafted Kikuyu text should be labelled "generated with Meta MMS-TTS / NLLB-200, CC BY-NC 4.0, non-commercial use" and excluded from the MIT licence claim in `README`/`LANGUAGES.md`. Whether model outputs are covered by the model licence is legally unsettled; treating them as covered is the safe choice.
- Any commercial deployment (a paid service, a company running Jani) needs either a commercial-licence TTS and translation, or native-speaker recordings and human translation. This fits the plan already in the master prompt (native review, 30-clip recording path in `LANGUAGES.md`).

---

## JMuBEN

- **Exact name:** JMuBEN. Mendeley Data, version 1, published 26 March 2021, DOI 10.17632/t2r6rszp5c.1. Authors: Jennifer Jepkoech, Benson Kenduiywo, David Mugo, Edna Chebet (Chuka University, University of Embu, JKUAT). Paper: Jepkoech et al., "Arabica coffee leaf images dataset for coffee leaf disease detection and classification", Data in Brief 36 (2021) 107142.
- **URL:** https://data.mendeley.com/datasets/t2r6rszp5c/1
- **Licence:** CC BY 4.0
- **Images:** 22,591
- **Classes:** Cercospora 7,682; Rust 8,337; Phoma 6,572 (paper text and abstract). The paper's Table 1 has typos (lists "Rust" twice and swaps Phoma's count); the text and the Mendeley total (22,591 = 7,682 + 8,337 + 6,572) agree with the figures given here. **No healthy and no miner class in this dataset.**
- **Country:** Kenya. Mutira coffee plantation, Kirinyaga county (neighbours Nyeri).
- **Capture conditions:** Fujifilm X-T4 (26.1 MP, APS-C) digital camera, "real-world conditions", with a plant pathologist. Then noise filtering and contrast stretching, cropped to a centre square on the region of interest, resized to a uniform size, and augmented (rotation and flipping) for the smaller sets. Final pixel size: NOT FOUND (check after download).
- **File size:** 549,107,532 bytes in 3 zips: `Cerscospora-...zip` 252,204,134; `Leaf rust-...zip` 69,450,673; `Phoma-...zip` 227,452,725.
- **No-login download:** Yes. Direct links:
  - Cercospora: https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/8657d2a2-c9a1-4733-9dbc-00c83aa3575a/file_downloaded
  - Rust: https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/8c7c2915-f979-43f6-b3fd-b3bc7407da87/file_downloaded (HEAD 200)
  - Phoma: https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/82625dd3-e908-4224-93b5-06a3b74f0c8a/file_downloaded
- **Does not cover:** healthy leaves, leaf miner, whole leaves with background (images are cropped to the lesion area and filtered), phone-camera images, more than one farm, named varieties (SL28, Ruiru 11, Batian not recorded), coffee berry disease. Original versus augmented copies are not marked.

## JMuBEN2 (relevant: it is where the Kenyan healthy class lives)

- **Exact name:** JMuBEN2. Mendeley Data, version 1, published 26 March 2021, DOI 10.17632/tgv3zb82nd.1. Same authors and paper as JMuBEN.
- **URL:** https://data.mendeley.com/datasets/tgv3zb82nd/1
- **Licence:** CC BY 4.0
- **Images:** 35,964
- **Classes:** Healthy 18,985; Miner 16,979.
- **Country:** Kenya, Mutira, Kirinyaga county.
- **Capture conditions:** as JMuBEN (same camera, cropping, filtering, augmentation by rotation and flipping).
- **File size:** 1,291,694,151 bytes: `Healthy-...zip` 566,927,674; `Miner-...zip` 724,766,477.
- **No-login download:** Yes. Direct links:
  - Healthy: https://data.mendeley.com/public-files/datasets/tgv3zb82nd/files/d126777d-c495-4b7a-846a-c0228540ea10/file_downloaded (HEAD 200)
  - Miner: https://data.mendeley.com/public-files/datasets/tgv3zb82nd/files/f6d37632-6349-4be9-9af0-c3177dbfaa8a/file_downloaded
- **Does not cover:** any disease class (only healthy and miner); same capture limits as JMuBEN. Healthy and miner are heavily augmented, so the number of distinct leaves is much lower than 35,964 (exact number NOT FOUND).

## BRACOL

- **Exact name:** "BRACOL - A Brazilian Arabica Coffee Leaf images dataset to identification and quantification of coffee diseases and pests". Mendeley Data, version 1, published 6 November 2019, DOI 10.17632/yy2k5y8mxg.1. Authors: Renato A. Krohling, Guilherme J. M. Esgario, José A. Ventura. Paper: Esgario, Krohling, Ventura, "Deep learning for classification and severity estimation of coffee leaf biotic stress", Computers and Electronics in Agriculture 169 (2020) 105162; arXiv 1907.11561.
- **URL:** https://data.mendeley.com/datasets/yy2k5y8mxg/1
- **Licence:** CC BY 4.0
- **Images:** 1,747 whole-leaf photos taken; 1,685 in the leaf dataset (62 with two stresses of similar severity were excluded); 2,147 cropped symptom images (the paper's symptom set of 2,722 adds 575 images from Barbedo 2019; the Mendeley description says 2,147).
- **Classes (leaf dataset, paper Table 1):** Healthy 272; Leaf miner 387; Rust 531; Brown leaf spot 348; Cercospora leaf spot 147. Symptom dataset (2,722 incl. external): healthy 256, miner 593, rust 991, brown leaf spot 504, cercospora 378. Severity labels on leaves: healthy 272, very low 924, low 332, high 101, very high 56.
- **Naming warning:** BRACOL has both "brown leaf spot" and "cercospora leaf spot". A Brazilian workshop paper (SBC WSIS) describes BRACOL's classes as including "doença da phoma", so "brown leaf spot" in BRACOL most likely means Phoma, not the Kenyan "brown eye spot" (which is Cercospora). I could not confirm this in the original paper text. ml should map BRACOL `brown leaf spot` to Phoma only after checking the folder names or the authors' code (github.com/esgario/lara2018). Unsure.
- **Country:** Brazil. Santa Maria de Marechal Floreano, mountain region of Espírito Santo state.
- **Capture conditions:** smartphones (ASUS Zenfone 2, Xiaomi Redmi 5A, Xiaomi S2, Galaxy S8, iPhone 6S); leaves picked and photographed on the abaxial (lower) side on a white background, "partially controlled conditions", different times of year. Pre-split into train, validation and test.
- **File size:** 164,516,964 bytes, one zip (`BRACOL_coffee_leaf_ images_datasets.zip`).
- **No-login download:** Yes (HEAD 200). https://data.mendeley.com/public-files/datasets/yy2k5y8mxg/files/c16b08ee-3ca6-4bf0-8f4e-4285a53a4a24/file_downloaded
- **Does not cover:** East Africa, upper leaf surface (photos are of the underside), leaves on the tree or with field background, low light, Phoma as named in Kenya (see naming warning), coffee berry disease.

## Uganda coffee leaf dataset

- **Exact name:** "A Machine Learning Dataset for Classification of Common Coffee Leaf Diseases in Uganda." Mendeley Data, version 1, published 7 February 2025, DOI 10.17632/k36wnd6knb.1. Authors: Specioza Chelangat, Racheal Anirwoth, Kizito Najib Mayanja, Abubakhari Sserwadda (Soroti University). No journal paper found.
- **URL:** https://data.mendeley.com/datasets/k36wnd6knb/1
- **Licence:** CC BY 4.0
- **Images:** 3,312 per the description; 3,322 files listed by the API.
- **Classes (description):** Healthy 1,179; Coffee Leaf Rust 1,023; Phoma 1,110. Files per folder from the API: 1,179; 1,033; 1,110 (folder names are not in the API; I matched them by count, so the 1,033 folder is presumably rust). **102 files are 0 bytes** (100 in the healthy-sized folder, 2 in the rust-sized folder). **About half of the files share an exact byte size with another file** (1,633 distinct sizes for 3,322 files), so exact duplicates are likely.
- **Country:** Uganda (farms; district not stated).
- **Capture conditions:** smartphone camera, "varying lighting conditions (daylight and low light)", leaves at early, medium and advanced growth stages. 256 x 256 JPEG. Duplicates removed, then **augmented** (rotation, flipping, brightness adjustment) to balance classes. Variety (Arabica or Robusta) is not stated; Uganda grows mostly Robusta, so this may not be Arabica. Unsure.
- **File size:** 25,409,168 bytes across 3,322 JPEGs. No zip file in the record; use the "download all" endpoint.
- **No-login download:** Yes. Zip: https://data.mendeley.com/public-api/zip/k36wnd6knb/download/1 (GET 206). Single files also return 200, e.g. https://data.mendeley.com/public-files/datasets/k36wnd6knb/files/8b384bd5-e89c-4e30-9323-10ae8349571b/file_downloaded
- **Does not cover:** Cercospora, leaf miner, coffee berry disease; confirmed Arabica; un-augmented originals (augmented copies are mixed in and not marked); full-resolution images (256 px only).

## RoCoLe

- **Exact name:** "RoCoLe: A robusta coffee leaf images dataset". Mendeley Data, version 2, published 17 May 2019, DOI 10.17632/c5yvn32dzg.2. Authors: Jorge Parraga-Alava, Kevin Cusme, Angélica Loor, Esneider Santander (ESPAM MFL, Manabí; Universidad de Santiago de Chile). Paper: Data in Brief 25 (2019) 104414.
- **URL:** https://data.mendeley.com/datasets/c5yvn32dzg/2
- **Licence:** CC BY 4.0
- **Images:** 1,560 (390 plants, 4 images per plant)
- **Classes (counted from `RoCoLe-classes.xlsx`):** binary healthy 791, unhealthy 769. Multiclass: healthy 791; rust_level_1 344; rust_level_2 166; rust_level_3 62; rust_level_4 30; red_spider_mite 167. Severity scale is the OIRSA/LANREF method, assessed visually by an expert.
- **Country:** Ecuador. CIIDEA, ESPAM MFL, Calceta, Manabí (-0.834206, -80.177159).
- **Capture conditions:** 5 MP f/2.2 autofocus smartphone, 200 to 300 mm from the plant, no zoom, leaves on the plant, cloudy, sunny and windy days, background of other plants and weeds, upper and lower leaf sides. Annotations in JSON, CSV, COCO, VOC and XLSX (segmentation masks included).
- **File size:** 2,270,913,636 bytes total: 1,560 JPEGs 1,566,761,118 bytes; `RoCoLe-voc.tar.gz` 697,591,506; annotation files about 6.5 MB. For classification, skip the VOC tarball.
- **No-login download:** Yes. Zip of everything: https://data.mendeley.com/public-api/zip/c5yvn32dzg/download/2 (GET 206). Label sheet: https://data.mendeley.com/public-files/datasets/c5yvn32dzg/files/04be3a14-906e-426b-8acc-610f719c9d90/file_downloaded
- **Does not cover:** Arabica, Africa, Cercospora, Phoma, leaf miner, coffee berry disease. Rust level 4 has only 30 images.

## PlantDoc (negatives for "not a coffee leaf")

- **Exact name:** PlantDoc (Cropped-PlantDoc classification set). Singh, Jain, Jain, Kayal, Kumawat, Batra, "PlantDoc: A Dataset for Visual Plant Disease Detection", CoDS-COMAD 2020, arXiv 1911.10317. Object-detection version: https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset
- **URL:** https://github.com/pratikkayal/PlantDoc-Dataset
- **Licence:** CC BY 4.0 (repo LICENSE). The images were scraped from the internet and annotated, so the original photographers' rights are not cleared. Fine to train on for a non-commercial prototype; do not re-host the images in our repo.
- **Images:** 2,578 in the repo (train 2,342, test 236). The paper says 2,598 data points.
- **Classes:** 28 folders over 13 species (apple, bell pepper, blueberry, cherry, corn, grape, peach, potato, raspberry, soybean, squash, strawberry, tomato). **No coffee**, which is what we want for negatives. Smallest folder: "Tomato two spotted spider mites leaf", 2 images.
- **Country:** not stated (internet images; paper authors in India).
- **Capture conditions:** mixed internet photos, field and indoor, many with cluttered backgrounds.
- **File size:** GitHub reports the repo at 955,318 KB.
- **No-login download:** Yes. https://github.com/pratikkayal/PlantDoc-Dataset/archive/refs/heads/master.zip (302 to codeload, normal for GitHub).
- **Does not cover:** coffee; East African weeds or shade trees that a farmer might photograph by mistake; non-leaf backgrounds (soil, hands, sheets), which we need to add ourselves.

## CoLeaf-DB (future work only)

- **Exact name:** "CoLeaf DATASET" on Mendeley, version 2, published 30 May 2023, DOI 10.17632/brfgw46wzb.2. Paper: Tuesta-Monteza, Mejia-Cabrera, Arcila-Diaz, "CoLeaf-DB: Peruvian coffee leaf images dataset for coffee leaf nutritional deficiencies detection and classification", Data in Brief 48 (2023) 109226. Universidad Señor de Sipán.
- **URL:** https://data.mendeley.com/datasets/brfgw46wzb/2
- **Licence:** CC BY 4.0
- **Images:** 1,006
- **Classes (paper Table 1):** healthy 6; nitrogen 64; phosphorus 246; potassium 96; magnesium 79; boron 101; manganese 83; calcium 162; iron 65; more than one deficiency 104.
- **Country:** Peru. San Miguel de las Naranjas and La Palma Central, Jaén province, Cajamarca. Varieties Catimor, Caturra, Borbón.
- **Capture conditions:** controlled environment (purpose-built structure), Canon PowerShot SX50 HS, 12.1 MP; deficiencies identified by agronomists.
- **File size:** 2,061,021,043 bytes in 10 zips.
- **No-login download:** Yes, per-file links of the form `https://data.mendeley.com/public-files/datasets/brfgw46wzb/files/<file-id>/file_downloaded` (listed by the public API), e.g. healthy.zip https://data.mendeley.com/public-files/datasets/brfgw46wzb/files/b220d2f4-8c02-429a-96c1-059923c1fd90/file_downloaded. Not HEAD-tested individually.
- **Does not cover:** diseases or pests; Africa; field backgrounds. Only 6 healthy images. Use only for the "future extension: nutrient deficiencies" note.

---

## Speech and language

### Meta MMS-TTS Kikuyu (`facebook/mms-tts-kik`)

- **URL:** https://huggingface.co/facebook/mms-tts-kik
- **Licence:** **CC BY-NC 4.0** (model card and Hugging Face tag). See the licence section above.
- **What it is:** VITS text-to-speech model, `transformers` `VitsModel`, language `kik`. Tokeniser: `is_uroman: false`, so it takes Gĩkũyũ text in Latin script directly (with tilde vowels ĩ, ũ); no romanisation step.
- **File size:** `model.safetensors` 145,226,744 bytes (a `pytorch_model.bin` is also present).
- **No-login download:** Yes, not gated (ranged GET 206). https://huggingface.co/facebook/mms-tts-kik/resolve/main/model.safetensors
- **Does not cover:** commercial use; voice choice (single voice); quality checked by native speakers (none published that I found); Kikuyu dialect variation.

### NLLB-200 (`facebook/nllb-200-distilled-600M`)

- **URL:** https://huggingface.co/facebook/nllb-200-distilled-600M
- **Licence:** **CC BY-NC 4.0**.
- **Languages:** `kik_Latn` and `swh_Latn` are both in the tokeniser's special tokens (checked in `special_tokens_map.json`).
- **File size:** `pytorch_model.bin` 2,460,457,927 bytes.
- **No-login download:** Yes, not gated (HEAD 200). https://huggingface.co/facebook/nllb-200-distilled-600M/resolve/main/pytorch_model.bin
- **Does not cover:** commercial use; agricultural terminology quality for Kikuyu (not evaluated; output must be marked "machine translation, pending native review"); disease names that have no Kikuyu equivalent.

### Mozilla Common Voice Swahili

- **Exact name:** Common Voice Scripted Speech 27.0 - Swahili (`sw`), corpus `cv-corpus-27.0-2026-09-11`, released 17 September 2026 on Mozilla Data Collective.
- **URL:** https://mozilladatacollective.com/datasets/cmu5sgles002zo1071nphgtby
- **Licence:** CC0 1.0, plus download terms: you agree not to try to identify speakers, and Mozilla asks downloaders not to re-share the files. Since October 2025 Common Voice is only distributed through Mozilla Data Collective; the Hugging Face copies (`mozilla-foundation/common_voice_17_0` etc.) now point there.
- **Size:** 730,758 clips, 1,064.9 hours recorded, 392.2 hours validated, 1,525 speakers, 269,140 validated clips. File size for v27: NOT FOUND; v26.0 Swahili is listed at 20.88 GB (MP3).
- **No-login download:** **No.** Needs an account with a validated email and acceptance of terms.
- **Does not cover:** Kikuyu; farming vocabulary specifically; text-to-speech voices (it is read speech for speech recognition). We do not need it for the current build (no speech recognition in scope); keep it as a reference for future voice input.

---

## Summary for ml

**Train on (all CC BY 4.0, all downloadable without login):**
- JMuBEN (rust, Cercospora, Phoma) **plus JMuBEN2 (healthy, miner)**. Without JMuBEN2 there is no Kenyan healthy class.
- BRACOL leaf dataset as the second source (healthy, miner, rust, Cercospora; "brown leaf spot" only after confirming it is Phoma).
- PlantDoc as "not a coffee leaf" negatives, plus our own background photos.

**Hold out (never in train or val):**
- Uganda set: cross-country test for healthy, rust and Phoma only. Before use, drop the 102 zero-byte files and de-duplicate (exact hash, then pHash). Report results on the de-duplicated count. Variety not stated, so say "coffee leaves from Uganda", not "Arabica".
- RoCoLe: field-condition test for healthy versus rust (map red_spider_mite to "other / unsure"). Robusta, Ecuador.

**Leakage risks:**
- JMuBEN and JMuBEN2 contain rotated and flipped copies with no marker for originals. pHash is rotation-sensitive, so a 90-degree rotation or a mirror will not be caught by a plain pHash comparison. Hash each image and its 7 rotations and flips (dihedral group) and keep the minimum distance, or group by that canonical hash, before splitting. Expect very large duplicate groups in healthy and miner.
- JMuBEN is from one farm and one camera, with lesion-cropped and filtered images. A high JMuBEN test score mainly measures recognition of that farm and preprocessing; report the Uganda and RoCoLe numbers as the honest ones.
- Uganda set: augmented copies inside the set (including brightness changes) inflate any accuracy computed on it; de-duplicate first.
- RoCoLe: 4 images per plant (filenames like `C10P10E1`, `C10P10H2`; I read P as plant and E/H as underside/upper side, which is my inference). It is a test set only, so this matters only if anyone fine-tunes on it; then split by plant.
- BRACOL comes with its own train/val/test split; keep it, and keep the symptom crops from the same leaf in the same split as that leaf.
- Class imbalance: JMuBEN2 healthy (18,985) dwarfs BRACOL Cercospora (147). Weight or cap per class.
