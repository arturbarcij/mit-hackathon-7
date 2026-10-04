# Jani: how we win (edge plan)

Lead review, Sun 4 Oct 2026, 00:25 CEST. Freeze 13:30, deadline 15:00.
Read with `kb/MASTER_PROMPT.md`. This file changes priorities. It does not reopen decisions 1 to 21.

## 1. Bottom line

1. **The concept will not win on its own.** At least five public repos are agriculture entries for this challenge. One of them, `cropwalk` ("Ondera Leaf Walk"), is close to a twin of Jani: the same six labels, abstention in Swahili, 10 leaves, a quality gate and a confirm-before-send SMS to the cooperative. Our edge has to come from **evidence and a build that judges can test themselves**.
2. **The biggest risk is the model, not the UI.** The 97% holds on JMuBEN-style 128 px crops. On whole leaves on a plain background (BRACOL test) v1 accepts 54% and has never accepted a healthy leaf. On field photos it is confidently wrong 61% of the time. At the plot level it is **safe but nearly useless**. It never advised spraying a healthy plot and never gave a rusty plot the all-clear. But a healthy plot on a plain page gets "ask the officer" 100% of the time.
3. **The edge:** turn that finding into the strongest evidence story in the track. That means four things:
   - an image-validity gate (CottonAce uses a separate classifier "to reject outliers")
   - a model tuned to the protocol overnight
   - false-alarm and missed-alarm rates per 10-leaf plot
   - a live URL a judge can run in 60 seconds with no coffee leaves
4. **Before 01:00:** paste `kb/prompts/12_ml_overnight_amendment.md` into the ml chat. The current sweep rule requires int8 parity, which MobileNetV3 fails, so it will very likely select nothing and the GPU runs all night for no gain.

## 2. How we will be judged

- Hack-Nation screens all entries and hands a shortlist to the World Bank panel, which picks one winner per sector on 5 to 6 Oct. In past editions the Hack-Nation jury picked finalists within hours of the deadline. **So the three videos and the live URL are the pitch.**
- The World Bank's event page: "Entries are not just judged on technical merit, but also on development relevance as well as design and inclusivity." Teams must "build a solution that demonstrates a clear value add in a constrained environment."
- The brief itself warns: "a model trained only on [studio images] performs poorly on real field photos". It also scores "what your data does not cover". The judges wrote that warning, and we can answer it with numbers.

## 3. Who we are up against (public repos, checked Sat night)

| Repo | What it is | Where Jani is stronger |
|---|---|---|
| `nikhil-s1nha/cropwalk` | iOS Core ML leaf scouting. Same six labels, Swahili abstention, 10 stops x 10 leaves, incidence with a 95% CI, SMS to the cooperative, price reference | Android is 95.16% of Kenyan mobile web traffic, iOS 4.54% (StatCounter, Sep 2026). Our PWA runs on the phone Noor's household has and on a judge's laptop. Their repo shows no evaluation numbers or live URL yet. |
| `JackSantospago/Espresso-Hackers` | Flutter app. On-device LLM with RAG plus a ~4 MB MobileNetV3 | Open generation is harder to check for safety (brief glossary: "If it can say anything, it cannot be checked for safety"). Our fixed answer bank can be audited (QA decision matrix). |
| `univerdread/irrigation-coach` | Kenya. PWA plus USSD/SMS, FAO-56 irrigation | A different decision. The AI value is weaker (a calculator does FAO-56). |
| `ag-algolab/sakia` | Tunisia. Voice/SMS irrigation | Not Annex B coffee. |
| `farahnaqwi/AgriFarm` | Swahili voice evidence for loans, satellite cross-checks | Finance angle. |

The baseline of "offline + SMS + Swahili + leaf classifier" is crowded. What nobody shows is measured field behaviour, a gate that refuses the photos the model cannot read, and plot-level error rates.

## 4. What I measured tonight (shipped v1, T=3.5, threshold 0.583)

Method: shipped `leaf.onnx` on CPU, preprocessing from `model.json`. Code in `kb/edge/field_check.py` and `kb/edge/sheet_gate.py`. Uganda is a random 150 per class (some files unreadable, so 143/141/136 scored), never trained on. BRACOL rows were in training. These val and test rows were not.

| Set (never in training unless stated) | n | Gate passes | Confidently wrong | Wrong after gate | Notes |
|---|---:|---:|---:|---:|---|
| BRACOL val, whole leaf on plain background | 173 | 172 | 4 | 4 | |
| BRACOL test, same | 175 | 174 | 9 | 9 | Coverage 54%, selective accuracy 90%. Healthy 0/12 accepted. Rust 35/69, all correct. Phoma 50/55, all correct. Cercospora and miner: 9 of 9 accepted were wrong |
| Field: Uganda healthy, rust and phoma (phone) plus iNaturalist rust | 468 | 3 | 284 (61%) | 3 (0.6%) | 77 of 143 healthy flagged as a disease. Rust found 0 of 189. 109 of 189 rust photos labelled "not a leaf" |

Plot level (4,000 simulated 10-leaf plots each, through `rules.json`, pre-short-rains window):

| Plot | Photos | Spray advice | All clear | Ask the officer |
|---|---|---:|---:|---:|
| 10 healthy | BRACOL val | 0% | 0% | 100% (too many unsure) |
| 6 rust + 4 healthy | BRACOL val | 0% | 0% | 100% |
| 10 rust | BRACOL val | 12% | 0% | 88% |
| Any of the above | field | 0% | 0% | 100% |

How to read this:
- **The fail-safe works.** Neither harmful error occurred on any set: no spray advice for a healthy plot, no all-clear for a rusty one. The rule table's "3 unsure goes to a person" carries it. Say this in Video 3. It is our pass/fail answer.
- **Value is near zero until the model reads a healthy leaf on paper.** That is tonight's ML job.
- **The gate removes almost all field errors.** It turns them into "lay the leaf on a plain page and take it again". Caveat: I set its thresholds tonight while looking at these same images. Validate it on fresh photos (move 2).
- **Do not show Noor labels the model cannot tell apart.** Cercospora, phoma and miner already all route to "ask the officer", so merging them changes no advice and removes confident wrong names.

The contact sheet `app/ml/_peek/contact_sheet_domain_gap.jpg` shows the gap in one picture for Video 3. It may include CC BY-NC iNaturalist images, so check `wild_set.csv`, keep the credit on screen and do not ship it in the app.

## 5. Edge moves, ranked

| # | Move | Lane, time | Acceptance test | Criteria hit |
|---|---|---|---|---|
| 1 | **Protocol-tuned model overnight.** Un-cap BRACOL, oversample it, add sheet augmentation, select and calibrate on BRACOL val. Prompt ready | ml, now to 06:30 | Beats v1 by 5+ points of BRACOL val coverage; accepts healthy leaves; in-domain F1 within 2 points | Built 25, Evidence 15 |
| 2 | **Image-validity gate in the engine.** Port `sheet_gate.py` (about 40 lines on a 256 px canvas). New card `retake_on_page`: "Lay the leaf flat on a plain page and take it again." | engine, 07:00 to 08:00 | Same pass/fail as Python on 20 reference images. Fresh test with phone photos: 10/10 leaves on an exercise-book page pass; 10/10 on a hand, table or tree fail | Pass/fail gate, Evidence 15 |
| 3 | **Real model, offline, in the live URL.** onnxruntime-web WASM, fp16 2.93 MB, service worker | engine + ui, 07:00 to 09:30 | Airplane mode, full 10-leaf check, under 1 s per leaf at 4x throttle. **08:30 decision:** if PWA on TanStack Start is not working, ship the farmer flow as a static Vite PWA (`app/` already is one) on Netlify or GitHub Pages, and keep Lovable for the officer side | Built 25 |
| 4 | **"Try a sample plot" for judges.** Bundle 10 BRACOL test leaves (CC BY 4.0, credited) and an "upload your own photo" path that works without a camera | ui, 30 min | A judge on a laptop finishes a check in 60 s. A random selfie gets the retake card | Built 25, Clarity 15 |
| 5 | **Name only what the model can tell apart.** Farmer cards: "rust", "no problem seen", "other spots: ask the officer". The officer view keeps the fine label, marked "model guess, please confirm" | content + ui, 20 min | No farmer screen shows phoma, cercospora or miner as a finding | Pass/fail, Clarity 15 |
| 6 | **Plot-level evidence table** in EVALUATION.md, v1 and v2 side by side: spray advice on healthy plots, all-clear on rusty plots, ask rate. Set against CottonAce's published goal of under 5% missed-alarm and false-alarm rates, "as both false positives and false negatives are harmful to the farmer" | ml/docs, 30 min, script ready | Table per data domain, test set named in every row | Evidence 15, Data 15 |
| 7 | **Fresh real-world test (optional).** A Coffea arabica houseplant (IKEA lists "COFFEA ARABICA", and garden centres sell them). Photograph 20 leaves on an exercise-book page, report whatever the app says, and film Video 2 with them | Arthur, 60 min, only if a shop opens by 09:00 | Results written up as they came, including abstentions | Evidence 15 |
| 8 | **Human language review.** Post now in the Hack-Nation Discord and to Kenyan contacts. Ask for a Swahili reviewer (10 min), and a Kikuyu speaker to record 8 core clips as WhatsApp voice notes. Native clips beat MMS-TTS and avoid its CC BY-NC licence in the product | Arthur, 5 min tonight | `REVIEW_LOG.md` names the reviewer (first name, county); clips in `public/audio/kik/` | Clarity 15, localising AI |
| 9 | **Data the system lacks.** Every referral is a dated, plot-level incidence count keyed to the cooperative member number. Every officer correction is a locally labelled image. This answers Annex B's "manual data collection, and delayed alerts" | docs/pitch, 20 min | One paragraph in README and one line in Video 3 | Data 15, Scale 10 |
| 10 | **Scale story with names.** KIAMIS has registered over 6.5 million farmers. KPCU is recruiting 1,000 ward-level Coffee Extension Champions (reported Sep 2026), who are natural users of the officer queue. Next step: one Nyeri cooperative pilot, then an AI Repository listing | docs/pitch, 20 min | README "What next" with sources | Scale 10, Relevance 20 |

## 6. Before you sleep (now to 01:00)

1. Paste `kb/prompts/12_ml_overnight_amendment.md` into the ml chat. Confirm the sweep restarts with job D next.
2. Post the reviewer and voice request (move 8).
3. Tell the engine-cowork lane that move 2 (gate) and move 4 (sample plot) are now part of E1/E3, and point it to `kb/edge/sheet_gate.py`.
4. Check that no agent turn edits code after 01:00 (your own overnight rule).

## 7. Sunday, revised (CEST)

| Time | What |
|---|---|
| 06:30 | Read sweep SUMMARY. Run `field_check.py` on v1 and the winner. Pick by rule |
| 07:00 to 09:30 | Critical path: real model in the browser, gate, offline. 08:30 hosting decision. Sample plot. Merged labels |
| 09:30 | Cut line. Nothing new after this |
| 09:30 to 11:00 | EVALUATION plot table, README top block (problem, what it does, numbers with set names, limits), QA `--strict` |
| 11:00 to 12:45 | Videos. Video 3 leads with the contact sheet and the plot table |
| 12:45 to 13:30 | Phone check in airplane mode, secret scan, submit |

## 8. Lines to use (exact quotes, sourced)

- "What we call 'small AI' is not about smaller ambition. It is AI purpose-built for the task at hand, efficient enough to run with limited energy, flexible enough to work with intermittent internet, and grounded in local languages and local realities." (World Bank blog, Kim and Nagao, Jul 2026)
- "AI must be used where it truly adds value." (World Bank, Harnessing AI for Agricultural Transformation, Nov 2025). Pair it with our deliberate non-AI parts: the rule table, the calendar, the price lookup.
- **Why now:** KMSA forecasts above-average October to December rains. For Nyeri, Kirinyaga, Murang'a, Kiambu, Embu and Meru, "the rains are expected to begin in the second to third week of October and continue into January". Rust sprays start "mid-October, just before the start of short rains" (Gichuru et al. 2021). Judging is this week, and so is Noor's decision.
- **Field gap is known:** a PlantVillage model scored 99.35% on its own test set but 31.40% on images from other sources (Mohanty et al. 2016). Say it, then show our own field numbers.
- **Multi-leaf design has precedent:** PlantVillage Nuru went from 65% to 74 to 88% when six leaves were assessed (Mrisho et al. 2020, Kenya and Tanzania).

## 9. What to cut or fix

- **Geo lane (G1 to G4) and the outlier map.** It currently shows 12 placeholder plots, and the nudge texts talk about deliveries and satellite data we do not have. Cut it from the videos, or label it "synthetic illustration" on every screen. Most entries will not have it, so it is not worth risking the pass/fail gate.
- **int8 claims.** We ship fp16 (3,077,051 bytes). Fix MASTER_PROMPT 5.1, README and Video 3.
- **"97% accurate" without its set.** Always say "on the in-domain JMuBEN/BRACOL/PlantDoc split", followed by the field numbers.
- **The bundle budget.** The onnxruntime-web wasm may push precache past 15 MB. Report the measured number. A 250 MB daily Safaricom bundle costs KSh 20 (EVIDENCE E8).
- **Supabase on the public repo.** The publishable key is fine to expose, but check that row-level security blocks public reads of `referrals` before the repo goes public.

## Sources
- World Bank, Global AI and Digital Summit 2026 event page: https://www.worldbank.org/en/events/2026/10/19/global-ai-and-digital-summit-2026
- Hackathon FAQ (World Bank): https://thedocs.worldbank.org/en/doc/a2d80d7a647019e16e7265a3563ce416-0320012026/original/Small-AI-for-Development-Hackathon-FAQs.pdf
- Kim and Nagao, "Small AI, big bets", World Bank blog, Jul 2026: https://blogs.worldbank.org/en/voices/small-ai--big-bets--how-the-world-s-most-impactful-ai-startups-w
- Harnessing AI for Agricultural Transformation, World Bank, Nov 2025: https://www.worldbank.org/en/topic/agriculture/publication/harnessing-artificial-intelligence-for-agricultural-transformation
- StatCounter, mobile OS share Kenya, Sep 2026: https://gs.statcounter.com/os-market-share/mobile/kenya
- KMSA OND 2026 outlook, reported by The Kenya Times, 2 Oct 2026: https://thekenyatimes.com/weather/kenya-met-reveals-when-above-normal-october-december-rains-will-start-and-end-across-counties/ and KMSA statement, 26 Aug 2026: https://meteo.go.ke/documents/4755/NCOF_13_Statement_26th_Aug_2026_Final.pdf
- Gichuru et al., Coffee Leaf Rust in Kenya, Agronomy 2021: https://www.mdpi.com/2073-4395/11/12/2590
- Mohanty, Hughes and Salathé 2016: https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.01419/full
- Mrisho et al. 2020 (Nuru): https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.590889/full
- Wadhwani AI CottonAce (PyTorch blog): https://medium.com/pytorch/how-wadhwani-ai-uses-pytorch-to-empower-cotton-farmers-14397f4c9f2b
- KIAMIS handover (FAO, Jan 2026): https://www.fao.org/agroinformatics/news/news-detail/official-handover-of-kiamis-to-the-government-of-kenya--a-new-era-for-digital-agriculture/en
- KPCU Coffee Extension Champions (Sacco Review, Sep 2026): https://saccoreview.co.ke/new-kpcu-seeks-1000-coffee-extension-champions-nationwide/
- IKEA COFFEA ARABICA listing: https://www.ikea.com/at/en/p/coffea-arabica-potted-plant-coffee-plant-60583434/
- Competitor repos: https://github.com/nikhil-s1nha/cropwalk , https://github.com/JackSantospago/Espresso-Hackers , https://github.com/univerdread/irrigation-coach , https://github.com/ag-algolab/sakia , https://github.com/farahnaqwi/AgriFarm
