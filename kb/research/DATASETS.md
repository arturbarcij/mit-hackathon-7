# DATASETS: licences, sizes, download URLs, what each one does not cover

Owner: research agent. Hand-off to ml (and docs for DATA_CARD). Accessed 3 Oct 2026. Source IDs point to `sources.json`.
Counts below come from the Mendeley public API file lists and from listing the zip contents over HTTP range requests (my own count, labelled "counted"). "Stated" means the record's own text.

## 0. Corrections the lead must make to MASTER_PROMPT section 6.1

| MASTER_PROMPT says | What I found | Consequence |
|---|---|---|
| JMuBEN: "22,591 Arabica leaf images: healthy, rust, cercospora, phoma, miner" | The JMuBEN record itself says: "it shows three sets of unhealthy images. In total, 22591 images". Its three zips hold **rust, cercospora, phoma only**. Counted 7,681 + 8,336 + 6,571 = 22,588 (stated 22,591). **Healthy and miner are in a separate record, JMuBEN2** (Healthy 18,984 images, Miner 16,978 images, counted). | ml must download two Mendeley records. JMuBEN2 has far more images than JMuBEN, so the class balance is driven by it. |
| JMuBEN "Cropped, resized, partly augmented" | Confirmed: "The data has been cropped to emphasize the region of interest... The images that were smaller were augmented". JMuBEN2 also says augmentation was applied to increase size. | Leakage risk is real (see section 1). |
| Uganda: "3,312 smartphone images in Ugandan farms: healthy, rust, phoma; daylight and low light" | Confirmed by the record's method field ("smartphone camera under varying lighting conditions (daylight and low light)"). **But it is also augmented** ("enhancing image diversity through augmentation techniques like rotation, flipping, and brightness adjustments") and the listing holds **3,322** files, not 3,312. | Not a clean held-out set. Rotated or flipped copies of one leaf may sit in the "test" set. Report this limit. |
| RoCoLe: "1,560 Robusta field images: healthy, red spider mite, rust levels 1 to 4" | Confirmed by the data article (S39): 1,560 images, healthy or unhealthy, red spider mite presence, rust severity at four levels (OIRSA method). One farm in Ecuador. | OK. Split by plant, not by image (4 images per plant). |
| BRACOL "Arabica leaf images with disease and pest labels" | Classes in the record: leaf miner, leaf rust, "brown leaf spot", "cercospora leaf spot", plus healthy. **No Phoma.** | ml must map "brown leaf spot" and "cercospora leaf spot" to our classes from the label files; I could not open the zip to check. |

---

## 1. Training sources

### 1.1 JMuBEN (Kenya, Arabica): rust, cercospora, phoma
- Record: https://data.mendeley.com/datasets/t2r6rszp5c/1 (DOI 10.17632/t2r6rszp5c.1). Published 26 Mar 2021. Authors: Jepkoech, Kenduiywo, Mugo, Chebet. S22.
- Licence: **CC BY 4.0** (record's `data_licence`). Credit and link needed.
- Method (stated): "Datasets were taken from Arabica coffee plantation using a camera and with the help of a plant pathologist. The images were then cropped to focus on the region of interest. Image augmentation was done with the aim of increasing the dataset size and preventing over-fitting". Country is Kenya per the authors' affiliations; exact county **not confirmed** (a PubMed snippet names a plantation, truncated, not opened).
- Files and sizes (Mendeley API), and counted contents:

| File | Bytes | Counted images | Download (no login; redirects to S3) |
|---|---|---|---|
| Cercospora zip | 252,204,134 | 7,681 `.jpg`, folder `Cerscospora` (sic) | https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/8657d2a2-c9a1-4733-9dbc-00c83aa3575a/file_downloaded |
| Leaf rust zip | 69,450,673 | 8,336 (8,192 `.jpg` + 144 `.jpeg`), folder `Leaf rust` | https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/8c7c2915-f979-43f6-b3fd-b3bc7407da87/file_downloaded |
| Phoma zip | 227,452,725 | 6,571 `.jpg`, folder `Phoma` | https://data.mendeley.com/public-files/datasets/t2r6rszp5c/files/82625dd3-e908-4224-93b5-06a3b74f0c8a/file_downloaded |

  Total 549,107,532 bytes (about 549 MB). Download with `curl -L -o x.zip <url>`; I checked that a range request works.
- Observation from file names (mine): rust holds original phone names such as `IMG_20210126_091314.jpg` (so some real field photos, taken 26 Jan 2021) mixed with 144 hashed `.jpeg` names. Cercospora and Phoma use numbered series like `9 (987).jpg` and `6 (970).jpg`, which suggests generated sets. I cannot tell which files are augmented copies.
- **Does not cover:** healthy leaves; leaf miner (both are in JMuBEN2); berries; nutrient deficiency; whole-plant or whole-leaf context (images are cropped to the lesion); variety (not stated); lighting and phone model (not stated); any split file (none supplied).
- Risk for ml: augmented copies of one source image may land in train and test. No source-image ID is supplied. Mitigation is near-duplicate hashing before splitting (ml's call).

### 1.2 JMuBEN2 (Kenya, Arabica): healthy and miner
- Record: https://data.mendeley.com/datasets/tgv3zb82nd/1 (DOI 10.17632/tgv3zb82nd.1). Authors: Jepkoech, Mugo, Kenduiywo, Chebet. S23.
- Licence: **CC BY 4.0**.
- Files:

| File | Bytes | Counted images | Download |
|---|---|---|---|
| Healthy zip | 566,927,674 | 18,984 `.jpg`, folder `Healthy`, names like `2 (990).jpg` | https://data.mendeley.com/public-files/datasets/tgv3zb82nd/files/d126777d-c495-4b7a-846a-c0228540ea10/file_downloaded |
| Miner zip | 724,766,477 | 16,978 `.jpg`, folder `Miner`, names like `1 (9999).jpg` | https://data.mendeley.com/public-files/datasets/tgv3zb82nd/files/f6d37632-6349-4be9-9af0-c3177dbfaa8a/file_downloaded |

  Total 1,291,694,151 bytes (about 1.29 GB).
- Record text says augmentation was used "with the aim of increasing the dataset size". Same leakage warning as 1.1.
- JMuBEN + JMuBEN2 together: counted 58,550 images. (A search snippet of a related paper says 58,549; I did not open it. Use my count.)
- **Does not cover:** rust, cercospora, phoma (in JMuBEN); berries; nutrients; variety.
- Class balance warning: healthy 18,984 and miner 16,978 against rust 8,336, cercospora 7,681, phoma 6,571. Raw counts are not natural prevalence.

### 1.3 BRACOL (Brazil, Arabica)
- Record: https://data.mendeley.com/datasets/yy2k5y8mxg/1 (DOI 10.17632/yy2k5y8mxg.1). Published 6 Nov 2019. Authors: Krohling, Esgario, Ventura. S26.
- Licence: **CC BY 4.0**.
- One file, `BRACOL_coffee_leaf_ images_datasets.zip` (the name contains a space), **164,516,964 bytes**. Download: https://data.mendeley.com/public-files/datasets/yy2k5y8mxg/files/c16b08ee-3ca6-4bf0-8f4e-4285a53a4a24/file_downloaded (first bytes are a zip header, `PK`). My `remotezip` listing of it failed, so I did not count inside it.
- Stated: 1,747 whole-leaf images ("healthy leaves and diseased leaves, affected by one or more types of biotic stresses") plus 2,147 cropped symptom images. Severity labels for the leaf set: "healthy (< 0:1%), very low (0.1% - 5%), low (5% - 10%), high (10% - 15%) and very high (> 15%)". Each set is divided into train, validation and test. Five phones listed (ASUS Zenfone 2, Xiaomi Redmi 5A, Xiaomi S2, Galaxy S8, iPhone 6S). Collected in Santa Maria of Marechal Floreano, Espirito Santo, Brazil. "The photos were taken from the abaxial (lower) side of the leaves under partially controlled conditions and placed on a white background."
- Useful point: the lower side on a white background is close to the sheet-of-paper protocol Jani asks of Noor.
- **Does not cover:** Phoma; Kenyan conditions; field backgrounds; berries; variety.
- Unresolved: the exact mapping of its "brown leaf spot" and "cercospora leaf spot" labels to ours. ml to read the labels inside the zip.

## 2. Held-out test sources

### 2.1 Uganda coffee leaf dataset (Soroti University)
- Record: https://data.mendeley.com/datasets/k36wnd6knb/1 (DOI 10.17632/k36wnd6knb.1). Published 7 Feb 2025. Authors: Chelangat, Anirwoth, Mayanja, Sserwadda. S25.
- Licence: **CC BY 4.0**.
- Stated: 3,312 images; healthy 1,179, CLR 1,023, Phoma 1,110; JPEG, 256 x 256. "Leaves were sampled at early, medium, and advanced growth stages."
- Listing: **3,322 files, 25,409,168 bytes in total (about 25 MB)**, so about 7.6 KB per image on average: very small and heavily compressed. Counted by file-name prefix: `1_*` 1,179; `1200_*` 1,033; `2300_*` 1,110. The 10 extra files sit in the `1200` group (1,033 against the stated 1,023). I assume this group is rust, but the prefix-to-class mapping is **not stated in the record**; ml should confirm by looking at images.
- Download: files are individual, 3,322 URLs. Get the list from the API: `https://data.mendeley.com/public-api/datasets/k36wnd6knb` with header `Accept: application/vnd.mendeley-public-dataset.1+json`; each file has `content_details.download_url`. Or download the dataset zip from the record page.
- **Does not cover:** cercospora and miner (so those classes cannot be tested cross-country); variety (not stated); original resolution (256 x 256 only); a clean un-augmented subset (none flagged).

### 2.2 RoCoLe (Ecuador, Robusta)
- Record: https://data.mendeley.com/datasets/c5yvn32dzg/2 (DOI 10.17632/c5yvn32dzg.2, version 2). Published 17 May 2019. Authors: Parraga-Alava, Cusme, Loor, Santander. S27. Data article: https://pmc.ncbi.nlm.nih.gov/articles/PMC6727496/ (S39).
- Licence: **CC BY 4.0**.
- Stated (S39): "The dataset contains 1560 leaf images with visible red mites and spots (denoting coffee leaf rust presence) for infection cases and images without such structures for healthy cases." "A total of 4 images are included per each one of the 390 coffee plants". Upper and back sides. "Images were acquired using a 5MP, f/2.2 autofocus smartphone camera." Severity: OIRSA method, "four diseases level". Location: CIIDEA, Calceta, Manabi, Ecuador (one farm). Working distance 200-300 mm; cloudy, sunny and windy days.
- Files (API): 1,565 entries. 1,560 `.jpg` (about 0.44 to 1.3 MB each; names like `C10P10E1.jpg`; counted 780 ending `E<n>`, 779 ending `H<n>`, one odd name `C11P11HE.jpg`), plus `RoCoLe-classes.xlsx` (39,437 B), `RoCoLE-coco.json` (1,813,080 B), `RoCoLE-csv.csv` (2,220,101 B), `RoCoLE-json.json` (2,488,394 B), `RoCoLe-voc.tar.gz` (697,591,506 B). **Total 2,270,913,636 bytes (about 2.27 GB)**. The meaning of the `E` and `H` suffixes is not stated in the places I read; the `.xlsx` has the labels.
- Download: per file; get URLs from the API as above (`https://data.mendeley.com/public-api/datasets/c5yvn32dzg`). For a quick test, the `.xlsx` plus a few hundred images is enough; avoid the 697 MB VOC archive.
- **Does not cover:** Arabica; Kenya; phoma, cercospora or miner; berries; any other lighting than the one farm. Naming: file names carry plant and position codes (C#P#), so split by plant to avoid leakage.

## 3. Negatives and extensions

### 3.1 PlantDoc (non-coffee leaves)
- Repo: https://github.com/pratikkayal/PlantDoc-Dataset (S29). Licence **CC BY 4.0** (GitHub API licence field). Repo size reported by the GitHub API: 955,318 KB (about 955 MB, includes git history). Clone with `git clone --depth 1`.
- The `train` folder lists 28 class folders and `test` 27 (checked via the GitHub contents API): apple, bell pepper, blueberry, cherry, corn, peach, potato, raspberry, soybean, squash, strawberry, tomato, grape. **No coffee class.** Good as negatives.
- Image counts per class NOT checked.
- **Does not cover:** coffee; background-only scenes (hands, soil, paper, sky). The "not a coffee leaf" class also needs those. Use PlantVillage or own photos for them; I did not research PlantVillage licensing (CC0 per its Kaggle/TFDS listings from memory, **unverified**).

### 3.2 CoLeaf-DB (Peru): nutrient deficiency, future extension
- Record: https://data.mendeley.com/datasets/brfgw46wzb/2 (DOI 10.17632/brfgw46wzb.2). Published 30 May 2023. Authors: Tuesta-Monteza, Mejia-Cabrera, Arcila-Diaz. Paper: https://doi.org/10.1016/j.dib.2023.109226. S28.
- Licence: **CC BY 4.0**.
- Stated: "1006 leaf images grouped according to their nutritional deficiencies (Boron, Iron, Potasium, Calcium, Magnesium, Manganese, Nitrogen and others)". 10 zips, 2,061,021,043 bytes in total (about 2.06 GB). **The healthy zip has only 6 images** (counted), 11,178,182 bytes.
- Per-zip bytes: boron 186,714,966; calcium 321,785,132; healthy 11,178,182; iron 137,875,321; magnesium 184,900,756; manganese 206,554,169; more-deficiencies 252,725,783; nitrogen 155,553,075; phosphorus 388,135,476; potassium 215,598,183.
- Download pattern: `https://data.mendeley.com/public-files/datasets/brfgw46wzb/files/<uuid>/file_downloaded`; UUIDs from the API. Healthy: https://data.mendeley.com/public-files/datasets/brfgw46wzb/files/b220d2f4-8c02-429a-96c1-059923c1fd90/file_downloaded
- **Does not cover:** diseases and pests; Kenya; useful only for the "cannot see" list, not for the model.

## 4. Language and voice resources

| Resource | Licence | Size | Notes |
|---|---|---|---|
| `facebook/mms-tts-kik` (Kikuyu TTS) S30 | **CC-BY-NC-4.0** (model card metadata) | `model.safetensors` 145,226,744 bytes; repo used storage 290,614,698 | Last modified 2023-09-01. Non-commercial. Fine for the hackathon and pre-rendered clips; flag for any commercial roll-out and in RESPONSIBLE_AI. Machine voice, unreviewed by a native speaker. |
| `facebook/mms-tts-swh` (Swahili TTS, fallback if ElevenLabs fails) | **CC-BY-NC-4.0** | not checked | Last modified 2023-09-01. |
| `facebook/nllb-200-distilled-600M` S31 | **CC-BY-NC-4.0** | `pytorch_model.bin` 2,460,457,927 bytes | Language tokens `eng_Latn`, `kik_Latn` and `swh_Latn` all appear in the repo's `special_tokens_map.json` (checked). Machine translation only; every string still needs a native reviewer. Non-commercial. |
| Mozilla Common Voice 17.0 S32 | Mozilla states CC0 in general; **not re-confirmed on the page I read** | n/a | The Hugging Face copy is now empty and data moved to the Mozilla Data Collective. **Swahili hours: NOT FOUND.** Not needed for Jani (we do not train ASR). |

Both Meta models carry a **non-commercial** licence. Decision for docs: say so plainly in DATA_CARD and LANGUAGES, and name ElevenLabs as the commercial-safe path for Swahili (its own licence terms were not researched).

## 5. Summary table for ml

| Dataset | Use | Licence | Size | Images (counted unless stated) | Classes |
|---|---|---|---|---|---|
| JMuBEN | train | CC BY 4.0 | 549 MB | 22,588 | rust, cercospora, phoma |
| JMuBEN2 | train | CC BY 4.0 | 1.29 GB | 35,962 | healthy, miner |
| BRACOL | train | CC BY 4.0 | 165 MB | 1,747 leaf + 2,147 symptom (stated) | healthy, miner, rust, brown leaf spot, cercospora leaf spot |
| Uganda | held-out test | CC BY 4.0 | 25 MB | 3,322 (stated 3,312) | healthy, rust, phoma |
| RoCoLe | held-out test | CC BY 4.0 | 2.27 GB | 1,560 | healthy/unhealthy, mites, rust severity 1 to 4 |
| PlantDoc | negatives | CC BY 4.0 | about 955 MB repo | not checked | 28 non-coffee folders |
| CoLeaf-DB | future | CC BY 4.0 | 2.06 GB | 1,006 (stated) | 8+ nutrient classes, 6 healthy |

## 6. Wild field test set (research pass 2, for ml)

- Manifest: `kb/research/wild_set.csv` (254 rows). Images: `data_raw/wild/inat/` and `data_raw/wild/commons/` (never commit).
- Sources: iNaturalist research-grade, 188 photos (taxon *Hemileia vastatrix* and *Coffea arabica*, CC BY / CC BY-NC / CC0); Wikimedia Commons, 66 photos. **Flickr: NOT FOUND.** Bright Data returned "Residential Failed (bad_endpoint)" / KYC block on `flickr.com` search. Openverse search pages were JavaScript shells with no image list.
- Licences recorded per row. ND licences were skipped. About 151 of 254 are **CC BY-NC 4.0** (fine for the hackathon; flag for any commercial roll-out).
- Labels are **hints only**, not agronomist labels. Counted by hint prefix: rust 58; `coffee_plant_unverified` 140; `coffee_leaf_unverified` 56. Many *Coffea arabica* shots are whole plants, flowers or berries. ml must look at each file before using it as a leaf test.
- Almost none are Kenyan (about 8 place strings look Kenya-related). This is a field-background / lighting set, not a Kenya-local set.
- Collect script: `kb/research/wild_collect.py`.

## 7. NOT FOUND or unverified

- Exact JMuBEN collection county and capture dates: NOT FOUND (a snippet names a plantation; truncated; not opened).
- Which JMuBEN and JMuBEN2 files are augmented copies and of which originals: NOT FOUND; no manifest is supplied.
- BRACOL inner file list and label files: not opened (remotezip failed).
- Uganda prefix to class mapping: inferred, not stated.
- PlantDoc image counts; PlantVillage licence: not checked.
- Swahili hours in Common Voice: NOT FOUND.
- ElevenLabs licence terms for the pre-rendered clips: not researched.
