# Jani

A small, offline leaf-check tool for coffee farmers in Kenya. It reads photos of 10 leaves on a phone, says what it sees or says it is not sure, and sends a short SMS to the cooperative if Noor asks for help.

Live URL: https://jani-farm-assist.lovable.app
Repo: https://github.com/arturbarcij/mit-hackathon-7
Videos: three clips, each under 60 seconds, submitted with the entry.

Entry to the World Bank Youth Summit x Hack-Nation Small AI for Development Hackathon, Annex B (agriculture). Items marked `TODO(owner)` or `[PENDING: owner]` are not done or not measured yet.

## What works in this copy

- Language choice: Kiswahili, Gĩkũyũ, English. Kiswahili is a draft. Gĩkũyũ is a machine draft on eight lines, pending a native speaker.
- Spoken consent. Nothing is sent unless she taps.
- Photo check for blur, darkness and size, then a label. Unclear leaves stay "not sure".
- Plot summary, action card, and her own decision.
- Referral text of at most 160 characters. The SMS app opens only when she taps. This copy also keeps the message on the phone, because there is no live SMS gateway. That queue is labelled simulated.
- Officer list, pasted-message box, label correction, and a CSV export. Seed rows are labelled synthetic.
- Installable page with an offline cache.

## What this copy does not do yet

- The app does not load the trained model yet. `public/model/leaf.onnx` (v2, 1.64 MB) is in the repo, but labels on screen still come from a mock: the sample name, the file name, or a rough colour guess. The screen says **Mock model**. The results in section 8 are offline evaluation numbers for the model file, not what this screen shows.
- Voice clips are not recorded yet. The play button says so, and the text stays on screen.
- The officer list is on this phone. It is not a shared cooperative server.

## 1. Problem statement

> Because of Jani, Noor will know which coffee rows have leaf rust and can protect them before the short rains, on the weekend she checks, when she would otherwise find out only after the yield has dropped or when the extension officer next visits; we know because Kenya has one extension agent per 1,380 farmers against a 1:400 FAO recommendation (Ministry of Agriculture and Livestock Development, Kenya, 2025) and rust peaks after the rains with losses above 75% in severe outbreaks (Agronomy, Kenya review, 2021). [S02] [S03]

Evidence table with source, year and country: [docs/DATA_CARD.md](docs/DATA_CARD.md), section 1.

Noor is the person in the challenge brief: 38, 2 ha, coffee on the upper slope, two phones, no Wi-Fi, phone at the house while she is on the slope. Our reference area is the Kenyan central highlands. Ondera is fictional. (source: challenge brief)

## 2. Noor's week

| When | Where | Device | What happens |
|---|---|---|---|
| Weekday | Basic phone | SMS | The cooperative can send a nudge: "a leaf check this weekend can help find why". The officer taps send. (Simulated in the demo.) |
| Saturday morning | On the slope | None | Noor and her daughter pick 10 leaves from the rows that look worst. A voice prompt explains how. |
| Saturday | At the house | Daughter's smartphone, offline | Photograph the leaves on a plain sheet. The app checks each photo. The model labels each leaf. The app shows "6 of 10 leaves show rust", spoken in Swahili. |
| Same visit | At the house | Same phone | An action card from a rule table. Noor chooses: act, wait, or ask the officer. |
| Same visit | At the house | Same phone, then SMS | If she asks, or the tool is unsure, a referral under 160 characters opens in her SMS app. She presses send. |
| Following week | Basic phone | SMS | A reminder from the cooperative (simulated). Reply 1 done, 2 not yet, 3 need help. |
| When connected | Officer dashboard | Web | The officer sees referrals, confirms or corrects labels, and plans visits. |

Why the weekend: the smartphone is the daughter's and is home at weekends (brief). Why the house: Noor's phone stays there during the day.

## 3. What the AI does, and why a simpler tool would not

**What it does.** Computer vision. A small convolutional network runs on the phone. It reads a leaf photo and says healthy, rust, cercospora (brown eye spot), phoma, leaf miner, or not sure. The app counts leaves across the 10-leaf sample.

**Why 10 leaves.** PlantVillage Nuru, a smartphone tool tested in Kenya and Tanzania, scored 21 to 59% on single cassava leaves and 74 to 88% when six leaves were assessed (Mrisho et al., Frontiers in Plant Science, 2020; different crop, so design precedent only, not our accuracy). (source: MASTER_PROMPT 5.2)

**Why not a simpler tool.**

| Option | Why it does not do this job |
|---|---|
| SMS or hotline | Noor must name the disease. She cannot. That is the problem. |
| Spreadsheet or rule table | It needs a symptom as input. The AI turns a photo into that symptom. |
| Web search | Needs data, literacy, English and a name to search for. |
| Extension officer | Can do it, but there is 1 agent per 1,380 farmers (S02, Kenya, 2025). |

**Where we chose not to use AI.** The advice is a rule table an officer can audit. The timing is a calendar. A price lookup is a spreadsheet job and is out of scope.

## 4. Guardrails

- Fixed answers. 30 answer IDs on 4 Oct 2026 (`src/content/answers.json`). Nothing is generated at runtime. No chatbot.
- Abstention. Low confidence, leaves that disagree, an unreadable photo or a non-leaf image all give "not sure, ask the officer". Threshold: 0.985 on the calibrated top-class probability (temperature 0.971), set in `public/model/model.json`.
- Quality gate. Blur, darkness and "is this a coffee leaf" are checked before the model runs.
- Human decides. Noor picks act, wait or ask. The tool never acts for her.
- Nothing sent automatically. The SMS opens pre-filled. She presses send.
- Officer confirms or corrects every referral.
- No pesticide names or doses from us. The card says to ask the cooperative.

Full account: [docs/RESPONSIBLE_AI.md](docs/RESPONSIBLE_AI.md).

## 5. Small AI facts

| Item | Value | Status |
|---|---|---|
| Model file | 1.64 MB (1,642,557 bytes), MobileNetV3-Small, int8 weights. Target 3 MB or less, cap 5 MB | Measured, `public/model/model.json` |
| Offline bundle (app, model, audio) | target 15 MB or less | `[PENDING: engine]` measured size (source: MASTER_PROMPT 5.2) |
| Download time at 1 Mbit/s | 120 s at the 15 MB target (our calculation, ignores overhead) | Re-calculate on the measured size |
| Cost in a Kenyan data bundle | 15 MB is 6.0% of Safaricom's KSh 20 / 250 MB daily bundle (our calculation; Safaricom terms 2026, S11; re-check price on the day) | Re-calculate on the measured size |
| Works offline | After first load, in airplane mode | `[PENDING: qa]` test |
| Inference per leaf | target under 1 s. 4.3 ms median on a cloud CPU in Python, not a phone | `[PENDING: engine]` browser and phone timing with this model (source: MASTER_PROMPT 5.2; docs/EVALUATION.md section 7) |
| Device | Household Android smartphone, Chrome, installable PWA | |
| Needs data for | First install; optional photo sync with consent | |
| Needs GSM for | Sending the referral SMS | |

## 6. Languages

| Language | Coverage | Status |
|---|---|---|
| Swahili | Voice and text for all answers | Review pending (`TODO(Arthur)`) |
| Gikuyu (Kikuyu) | Voice and text for a subset | Machine voice (Meta MMS-TTS) and machine draft, **pending native speaker review**. Non-commercial licence (CC BY-NC 4.0). |
| English | Text and audio for reviewers | Checked by team |

Adding a language: translate and record the fixed answer list (about 30 short clips), no model training. See [docs/LANGUAGES.md](docs/LANGUAGES.md).

## 7. Data

| Dataset | Country | Licence | Size | Use |
|---|---|---|---|---|
| JMuBEN | Kenya | CC BY 4.0 | 549 MB, 22,588 images | Train |
| JMuBEN2 | Kenya | CC BY 4.0 | 1.29 GB, 35,962 images | Train (source: MASTER_PROMPT 5.2) |
| BRACOL | Brazil | CC BY 4.0 | 165 MB | Train |
| Uganda coffee leaf set | Uganda | CC BY 4.0 | 25 MB, 3,322 files | v2: 50% train, 15% threshold choice, 35% test, split by duplicate group (source: MASTER_PROMPT 5.2) |
| RoCoLe | Ecuador | CC BY 4.0 | 2.27 GB, 1,560 images | Test only |
| PlantDoc and background photos | Mixed | CC BY 4.0 (PlantDoc) | about 955 MB | Negatives (source: MASTER_PROMPT 5.2) |

Counts are our own, from `kb/research/DATASETS.md`. Full tables, gaps and synthetic data: [docs/DATA_CARD.md](docs/DATA_CARD.md). Synthetic data (seed referrals, simulated SMS, delivery records) is tagged and labelled on screen.

## 8. Results

Model `v2-2026-10-04`. Numbers come from `ml/metrics.json`. Each names its test set and n. "Answers" means the leaf is above the threshold. The rest show "not sure".

| Measure | Value | Test set |
|---|---|---|
| In-domain accuracy | 0.969 (n = 9,359). Inflated by augmented near-copies in the sources | JMuBEN, JMuBEN2, BRACOL, PlantDoc held-out split |
| Uganda phone photos | Answers 45% (476 of 1,051). Right on 98.7% of those | Uganda test split. Same farms as the Uganda training split, so not a cross-country result |
| Field photos, Ecuador | Answers 2% (31 of 1,393). Rust recall 0.030 | RoCoLe, the only fully independent set |
| Non-coffee rejection | 60 of 61 non-coffee leaves and 298 of 300 blank pages rejected | PlantDoc non-coffee leaves; synthetic blank pages (same generator as the training negatives, so optimistic) |

On photos like its training data the model is accurate when it answers. On field photos from a new country it mostly says "not sure". That is safe, but not yet useful there.

Detail, including weak results: [docs/EVALUATION.md](docs/EVALUATION.md).

## 9. Limits

- The app does not load the trained model yet. Labels on screen are a mock.
- On field photos from a new country (RoCoLe, Ecuador) the model says "not sure" for 98% of leaves.
- Reads leaves only. No berries, nutrient deficiency, roots, wilt or drought stress. It says so and refers.
- Not tested on Noor's farm. Public photos only, mostly cropped or augmented.
- No labelled Kenyan varieties (SL28, Ruiru 11, Batian).
- Phoma and brown eye spot: no Kenyan extension source found, so the answer is "ask the officer".
- Spray cut-offs in `rules.json` are assumptions. No Kenyan incidence threshold found. Officer to confirm.
- Kikuyu audio is a machine voice.
- Simulated: SMS reminder line and replies. Synthetic: seed referrals and cooperative delivery records.
- The national yield series is not a steady decline (FAOSTAT 2015 to 2024). We do not claim one.

Full list: [docs/DATA_CARD.md](docs/DATA_CARD.md), section 3.

## 10. Tech stack and how to run

Stack: Vite, React, TypeScript; `vite-plugin-pwa`; `idb`; `react-router-dom`; `onnxruntime-web` on the engine branch, not yet on main; Python, PyTorch, `timm` for training. Diagram and budgets: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```bash
cd app
npm install
npm test
npm run dev        # farmer app at /, officer list at /officer
```

Open the site, then use "Fill 10 synthetic leaves" to walk the October rust case without farm photos. Those pictures are synthetic.

Model training, export and evaluation: [ml/README.md](ml/README.md).
Audio is pre-rendered at build time, so the client does not call a speech service at runtime.

Requirements and test status: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md). Reuse for another crop or country (example: cocoa in Côte d'Ivoire): [docs/REPLICATION.md](docs/REPLICATION.md).

## 11. Our take on localising AI

`TODO(Arthur)`: two to three sentences in Arthur's words. Draft to react to: Localising AI means the model improves on Ondera's own leaves, labelled by Ondera's own officer, and speaks Ondera's own languages. Adding a language should mean recording clips, not training a model. The tool earns trust by saying "not sure" and sending the person to the officer.

## 12. Credits and licences

- Code: MIT, see [LICENSE](LICENSE).
- Datasets: JMuBEN and JMuBEN2 (Jepkoech, Mugo, Kenduiywo, Chebet), BRACOL (Krohling, Esgario, Ventura), Uganda coffee leaf set (Chelangat, Anirwoth, Mayanja, Sserwadda; Soroti University), RoCoLe (Parraga-Alava, Cusme, Loor, Santander), PlantDoc. All CC BY 4.0. Links in [docs/DATA_CARD.md](docs/DATA_CARD.md).
- Meta MMS-TTS and NLLB-200: CC BY-NC 4.0, non-commercial.
- Voices: ElevenLabs (Swahili, English), pre-rendered.
- Guidance: Coffee Leaf Rust in Kenya, Agronomy 2021 (S03); Infonet Biovision (S17).
- Team: `TODO(Arthur)` names and roles.
