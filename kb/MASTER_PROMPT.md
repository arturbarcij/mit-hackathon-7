# MASTER PROMPT: Small AI for Development Hackathon, Annex B (Agriculture)

Working name: **Jani** (Swahili for "leaf"). Rename freely.
Hard deadline: **Sunday 4 October 2026, 15:00 CEST**. Internal freeze: **13:30 CEST**.

This prompt is the single source of truth for every human and AI agent on this project (Cursor, Lovable, Claude, scripts). Read it top to bottom before writing code. If any instruction elsewhere conflicts with this file, this file wins. If this file conflicts with the official challenge brief, the brief wins and this file must be corrected.

---

## 0. Decisions the human must confirm before build starts

These are recommended defaults. Build assumes them unless changed here.

| # | Decision | Default | Why |
|---|----------|---------|-----|
| D1 | The one decision we support | "Do I need to act on a leaf problem in my coffee, when, and does the extension officer need to come?" | Brief asks for ONE better agricultural decision. This one covers "identify a crop problem", "time a farming activity" and "connect evidence to an extension next step" in a single flow. |
| D2 | Reference geography | Kenya central highlands (Arabica, maize and beans below, cooperative members) | Matches Noor's farm layout and language pattern. Best open data (JMuBEN is Kenyan Arabica). Ondera stays fictional; Kenya is the evidence anchor. |
| D3 | Languages | Swahili (national language, full voice + text). Gĩkũyũ / Kikuyu (home language, low-resource, demonstrated on a subset of answers). | Brief: "at home she speaks her local language, and the national one when she needs it." A Swahili-only tool does not speak her home language. Kikuyu is our live answer to "how would it fare in a less-supported language". |
| D4 | Price reference | Out of core scope. Tier 3 stretch only, and explicitly non-AI. | A price lookup is a spreadsheet job. Saying so earns credibility on the "would a simpler tool do the same job" criterion. |

---

## 1. Mission

Build a working Small AI tool that helps Noor make, communicate and act on one better agricultural decision about her coffee, inside her real constraints, and prove it works with honest evidence. Ship: live URL, code repo, three 60-second videos, all by the deadline.

We are one of roughly 8,000 participants. Most agriculture entries will be a cloud chatbot or a PlantVillage classifier with a 99% accuracy claim. We win by being the entry that clearly understood Noor, respected every constraint, and was honest about limits.

---

## 2. The challenge, condensed (from the official brief)

### 2.1 Noor
- 38, farms 2 ha in the Ondera highlands. Coffee on the upper slope, maize and beans below. Ondera Coffee Cooperative member for 11 years.
- Speaks her local language at home, the national language when needed.
- **Two phones.** Her own basic phone: calls, SMS, mobile money. Her daughter's smartphone: only when the daughter is home from boarding school **at weekends**.
- No Wi-Fi. Buys 3G bundles when needed.
- **For most of the day she is on the slope and the phone is at the house.**

### 2.2 Annex B scenario
- Coffee yields dropped this season; she cannot say why.
- Extension officer visits the sub-county twice a year at best.
- At harvest she sells parchment to whichever middleman drives up the valley, at whatever price he names.
- Binding constraint is often the **absence of a working farmer registry**, not the absence of an algorithm.
- Where AI adds value: computer vision on photos (Wadhwani AI pest-trap model, offline on a basic smartphone); voice advisory in local languages where literacy is a constraint.
- Preconditions: AI stacked on absent registries, phones or trust will be hard to implement.

### 2.3 Hackathon task (Annex B)
Help Noor make, communicate or act on one better agricultural decision; for example identifying a crop or post-harvest problem, timing a farming activity, accessing localised advisory, documenting a field observation, improving quality or value addition, or connecting evidence to a pricing, market or extension-service next step.

### 2.4 Rules (Section 06). All are hard requirements.
1. Runs on a device the user already has.
2. Its core feature works offline.
3. Model files are small enough to side-load or send over a weak connection.
4. At least one interaction is in a local language, by voice or text. Name the language. Expect to be asked how it fares in a less-supported one.

### 2.5 AI guardrails
- Human in the loop: a person makes the final call. The tool informs a decision and flags uncertainty. It does not act on the user's behalf. Agentic steps must check in with the user.
- Avoid hallucinations.

### 2.6 Pass/fail gate (Responsible AI, data and safety)
Fail-safe required: when the data is not enough for a definitive answer, the AI signposts to a decision-maker ("not sure, ask a person") instead of guessing. Limits respected. Credible account of privacy, consent, bias and human oversight. **Failing this gate eliminates the entry regardless of other scores.**

### 2.7 Data rules (Section 07)
- Cite every data source.
- **Problem data:** source, year, country. Flag where figures come from synthetic or modelled data.
- **Build data:** name every dataset, its source, licence and size.
- **State what the data does not cover. This is scored.**
- Synthetic data allowed only if labelled as synthetic.

### 2.8 What must exist by the end (Section 05)
- A working prototype (app, chatbot, SMS service, voice line).
- A clear answer to which AI technique is in use and why it beats a simpler tool (SMS, spreadsheet, search).
- Proof it works on real examples.

### 2.9 Judging
| Criterion | Weight | Question |
|---|---|---|
| Built solution (Small AI fidelity) | 25% | Works end to end within sector constraints? |
| Development relevance and impact | 20% | Real problem from the brief; does the outcome matter to Noor? |
| Data grounding | 15% | Addresses a data gap; data modelling sound? |
| Evidence it works | 15% | Fits the sector challenges; adds other constraints? |
| Clarity, design, inclusivity / Value proposition for AI | 15% | What the AI does, and would a simpler tool do the same job? |
| Scalability, replicability, what next | 10% | Could another setting reuse it? |
| Responsible AI, data and safety | Pass/fail | See 2.6 |

### 2.10 Submission (platform requirements override the PDF where they differ)
- Prototype: working tool plus code, or a link to it.
- **Live project URL.**
- **GitHub repo**, made public right after submission and before judging (5 to 6 October). No secrets in history.
- **Three videos**, each MP4 or MOV, **max 60 seconds**, max 1 GB: (1) Team introduction, (2) Product demo, (3) Technical walkthrough.
- The PDF asks for one 2 to 5 minute video covering five content items (see Section 11). Our three videos must cover all five items between them. The three videos concatenated (about 3 minutes) also satisfy the PDF format; produce that cut as a backup.
- Entrants aged 18 to 35.

---

## 3. Strategic thesis (why this design, top-down)

### 3.1 What most entries will get wrong
1. **They assume Noor holds a smartphone in the field.** She does not. The smartphone is home at weekends, and her own phone stays at the house while she works.
2. **They run a cloud LLM at runtime.** That breaks "core feature offline", "small model", and "avoid hallucinations" at once.
3. **They train and test on PlantVillage** (studio images, no coffee) and report 95 to 99% accuracy. The brief warns about exactly this.
4. **They ship an open chatbot.** The glossary says it plainly: if it can say anything, it cannot be checked for safety.
5. **They speak only the national language** and never address the home language.
6. **They ignore the registry and the institution.** A tool that does not route through the cooperative and the extension officer is a pilot forever.
7. **They let the AI decide.** The rules require the person to decide.

### 3.2 Our answer, one line per insight
- **Fit her week, not a demo.** The smartphone check happens at the weekend, at the house, with her daughter. The follow-through happens on her own basic phone during the week.
- **Several leaves, not one.** PlantVillage Nuru's field study in Kenya and Tanzania found single-leaf accuracy as low as 21 to 59%, rising to 74 to 88% when six leaves were assessed (Mrisho et al., Frontiers in Plant Science, 2020). Our 10-leaf plot check follows that evidence. See kb/research/PRIOR_ART.md.
- **The protocol is the model's friend.** Noor picks 10 leaves from the rows she is worried about and brings them to the house. They are photographed on a plain sheet (exercise book page) in daylight. This mirrors standard rust-incidence sampling, fits "the phone is at the house", and narrows the gap between training images and real use, so a tiny model stays reliable.
- **Split perception from decision.** AI does one thing: read leaf photos. The advice is a transparent rule table (incidence plus season timing) written from published Kenyan guidance and signed off by an extension officer. Every possible answer is in a fixed list. Nothing is generated at runtime.
- **Generative AI at build time, not runtime.** ElevenLabs renders the fixed answer list into Swahili audio once. Clips ship with the app and play offline. Every clip is reviewed by a human before release.
- **Abstain loudly.** Low confidence, disagreement across leaves, unreadable photo, or a non-leaf image all produce "not sure, ask the officer", with a ready referral.
- **Ride the existing registry.** Kenya has one: KIAMIS, over 6.5 million farmers registered by mid-2025, handed from FAO to the Government in November 2025. Jani's referral carries the cooperative member number now and can carry a KIAMIS ID later. The cooperative also holds a member list. Referrals carry the member number, so the officer's two visits a year go to the plots that actually need them. Officer corrections become locally labelled training data.
- **Localising AI, concretely:** the model gets better on Ondera's own leaves, labelled by Ondera's own officer, spoken in Ondera's own languages. Adding a new language means recording about 30 short clips, not training a model.

### 3.3 Why now (the timing hook)
In Kenya, coffee leaf rust peaks soon after the rainy seasons; copper sprays start in mid October, just before the short rains, with a repeat about three weeks later (Coffee Leaf Rust in Kenya, Agronomy 2021, MDPI). Judging happens in October. The demo scenario is literally this week's decision.

### 3.4 The system layer: "is it me, or is it everyone?"
Annex B opens with "her coffee yields have slipped and she is not sure why". The first useful answer is not a diagnosis, it is a comparison. Kenyan cooperatives already record every member's delivery (the registry the brief calls the binding constraint). Comparing Noor's deliveries to similar farms nearby, plus free satellite greenness (Sentinel-2) and rainfall (NASA POWER / CHIRPS), separates three cases:
- **everyone dropped and rain was low**: weather, nothing to diagnose on her farm;
- **only she dropped and her canopy thinned**: a leaf problem is likely, so the cooperative nudges her (one SMS) to do a leaf check at the weekend;
- **only she dropped but the canopy looks normal**: not a leaf problem as far as we can see, so the officer visits.
Three layers, each doing only what it can do: **the map decides where to look, the phone decides what it is, the officer decides what to do.** The map lives on the cooperative/officer side (online); Noor's core feature stays offline on her phone. Delivery records and plot shapes are synthetic in the demo and labelled as such; satellite and rainfall are real. Owner: geo agent (`kb/agents/geo.md`). Priority: Tier 1b, it must never block the farmer app.

### 3.5 The closed loop
1. Cooperative map flags plot P07 as `canopy_loss_check_leaves`.
2. Officer reviews and taps "send nudge" (the officer decides; nothing is sent automatically): SMS to Noor's basic phone, "Farms near you delivered about the same as last year; yours less. A leaf check this weekend can help find why."
3. Saturday: Noor and her daughter run the 10-leaf check offline. Result plus her decision go back as a referral SMS.
4. The referral appears on the same map, on her plot. The officer plans the visit. Corrections become local training data.

---

## 4. The user journey (this is what the product demo shows)

**Saturday morning, on the slope.** Noor and her daughter pick 10 leaves from the rows that look worst (the app's voice prompt explains how, in Swahili or Kikuyu, with pictures).

**Saturday, at the house, phone offline.**
1. Open Jani (installed PWA; no data needed). Choose language by tapping a speaker icon that plays each language's name.
2. Consent screen read aloud: what is stored, where, who can see it. Noor says yes or no; nothing is sent without a separate yes later.
3. Photograph the leaves one by one on the plain sheet. The app checks each photo (blur, darkness, "is this a coffee leaf") and asks for a retake if needed.
4. On-device model labels each leaf: healthy, rust, cercospora (brown eye spot), phoma, leaf miner, or "not sure".
5. Plot summary: e.g. "6 of 10 leaves show rust." Shown as icons and spoken aloud. Uncertain leaves are counted separately and never forced into a class.
6. Action card from the rule table, spoken aloud. Example: "Rust is on many leaves. The short rains are close. Spraying copper before the rains protects the new leaves. Ask the cooperative which product and dose. Repeat after three weeks." Each card says what the tool is and is not sure about.
7. Noor decides: "I will act", "I will wait", or "Ask the officer". The tool never decides for her.
8. If "Ask the officer" or the tool abstained: the app builds a referral of under 160 characters (member number, plot, date, counts, confidence) and opens the SMS composer pre-filled to the cooperative number. Noor presses send herself. SMS needs a GSM signal only, no data bundle.

**During the week, on her own basic phone.** The cooperative SMS line sends a reminder on the chosen date ("Spray day is Tuesday if it is dry"). Noor can reply 1 = done, 2 = not yet, 3 = need help. (Simulated in the demo; label it as simulated.)

**Officer side, when connected.** The officer dashboard lists referrals by urgency and location. The officer opens the photos (synced later, only with consent), confirms or corrects the label, and plans the visit. Corrections are stored as new labelled examples.

---

## 5. Solution architecture (Small AI)

### 5.1 Components
| Component | What | Where it runs | Online needed? |
|---|---|---|---|
| Farmer app | React PWA, installable, service-worker cached | Household smartphone (Android, Chrome) | First install only |
| Leaf model | MobileNetV3-Small or EfficientNet-Lite0, fine-tuned, int8-quantised ONNX | In the browser via onnxruntime-web (WASM) | No |
| Quality gate | Blur (Laplacian variance), brightness, plus "not a coffee leaf" class / OOD score | In the browser | No |
| Rule table | JSON: (incidence band, dominant class, season window) to answer ID | In the browser | No |
| Answer bank | Fixed list of answer IDs with Swahili and English text, Swahili audio (ElevenLabs, pre-rendered), Kikuyu audio for a subset (Meta MMS-TTS `facebook/mms-tts-kik`, pre-rendered, flagged as machine voice pending native review) | Bundled with the app | No |
| Season calendar | Rain-onset windows per area from CHIRPS / NASA POWER climatology, cached at install | Bundled JSON | No |
| Local store | IndexedDB: checks, photos, decisions | Phone | No |
| Referral | Compact SMS string, opened via `sms:` link; user sends | Phone + GSM | GSM only |
| Officer dashboard | Referral queue, map, label confirm/correct, export of corrected labels | Web (live URL) | Yes |
| SMS reminder line | Simulated SMS panel (clearly labelled) | Web | Yes |

### 5.2 Budgets (measure and report every one)
- Model file: target 3 MB or less, hard cap 5 MB.
- Download cost line for docs: the 15 MB bundle is 6% of Safaricom's KSh 20 daily 250 MB bundle (tariff page, Oct 2026; re-check on the day), about 2 minutes at 1 Mbit/s.
- Whole offline bundle (app + model + audio): target 15 MB or less. Report download time at 1 Mbit/s 3G and cost in a typical Kenyan data bundle (verify the price and cite it).
- Inference: under 1 second per leaf on a low-end Android, or in Chrome DevTools with 4x CPU throttling if no device is available. State which.
- Works in airplane mode after first load. Show this on camera.

### 5.3 Non-goals (do not build)
- No runtime LLM, no free-text chatbot, no generated advice.
- No diagnosis of berries (coffee berry disease), roots, or nutrient deficiency. The tool says so and refers.
- No pesticide product names or doses invented by us. Doses come from the cooperative / officer only.
- No user accounts or passwords on the farmer side.
- No automatic sending of anything. The user presses send.

### 5.4 Stack
- Frontend: Vite + React + TypeScript + Tailwind (Lovable default). `vite-plugin-pwa` for the service worker. `onnxruntime-web` for inference. IndexedDB via `idb`.
- Training: Python, PyTorch + `timm`, export to ONNX, quantise with `onnxruntime.quantization`. Notebook or script in `/ml`.
- Officer dashboard: same app, `/officer` route. Lovable Cloud / Supabase for referral storage. Seeded with clearly labelled synthetic referrals plus any real ones from testing.
- Hosting: Lovable publish (fallback: Vercel or Netlify from the GitHub repo).

---

## 6. Data plan

### 6.1 Build data (what the model learns from and is tested on)
Verify licence and size for each before use and record it in `DATA_CARD.md`.

| Dataset | Content | Role | Known gap |
|---|---|---|---|
| JMuBEN + JMuBEN2 (Mendeley, Kenya, CC BY 4.0) | JMuBEN: 22,588 images, rust, cercospora, phoma (549 MB). JMuBEN2: 35,962 images, healthy and miner (1.29 GB). Cropped, augmented, no source manifest. | Main training set. Kenyan Arabica, our crop and country. | Augmented copies will leak across splits unless near-duplicates are hashed first. Cropped to the lesion, so little background variety. Variety and county not stated. |
| BRACOL (Mendeley, Brazil, CC BY 4.0) | 1,747 whole-leaf + 2,147 symptom images; healthy, miner, rust, cercospora. No phoma. Lower side on a white background, five phones. | Second training source; its white-background protocol matches ours | Brazilian conditions; no phoma; label mapping of 'brown leaf spot' to confirm. |
| Uganda coffee leaf dataset (Mendeley k36wnd6knb, CC BY 4.0) | 3,322 files (stated 3,312), 256x256, smartphone, daylight and low light: healthy, rust, phoma. Augmented. | **Held-out cross-country test set** (East Africa, phone camera) | Only 3 classes; augmented copies may sit in the test set; variety not stated. |
| RoCoLe (Ecuador, CC BY) | 1,560 Robusta field images: healthy, red spider mite, rust levels 1 to 4 | **Held-out field-condition test set**, rust severity sanity check | Robusta, not Arabica; Latin America. |
| PlantDoc / PlantVillage (non-coffee leaves) + background photos | Negatives | Train the "not a coffee leaf" class | Not coffee by design. |
| Our own photos | Any leaves we can photograph this weekend on a plain sheet | Smoke test of the capture protocol | Not coffee unless we find coffee; label honestly. |

Report what the model **cannot see**: coffee berry disease (berries), nutrient deficiencies (see CoLeaf-DB for a future extension), wilt and root problems, drought stress, mixed infections, night photos, other varieties (e.g. SL28, Ruiru 11, Batian are not labelled in any set), leaves still on the tree with cluttered background.

### 6.2 Problem data (why this matters, with source, year, country)
Collect and cite primary sources. Candidates to verify:
- Extension coverage in Kenya: **1 extension agent per 1,380 farmers** (Agriculture Extension Manual v1, Ministry of Agriculture and Livestock Development, Feb 2025) against a national target of 1:600 (ASTGS 2019 to 2029, cited in KASEP Dec 2023) and the FAO recommendation of 1:400. 6.4 million farming households (2019 census via KASEP). Do not use the 'fewer than 5,000 officers for 8 million farmers' figure: unverified secondary.
- Rust impact: losses above 75% in severe outbreaks; peaks after rainy seasons; spray timing mid October (Agronomy 11(12):2590, 2021, review of CLR in Kenya).
- Coffee yield for Kenya: FAOSTAT 2015 to 2024 (official flag). 2024: 49,500 t, 435.7 kg/ha; low point 2020 at 308.3 kg/ha. **The national series is not a steady decline; never claim one.** Noor's drop is a farm-level story. Cooperatives yield 414.7 kg/ha vs estates 578.1 (KNBS 2023/24).
- Phones: 91.8% of Kenyan women own a mobile phone (Findex 2024); 42% of women vs 50% of men own a smartphone (GSMA Mobile Gender Gap Report 2025, 2024 survey). Supports the two-phone design.
- Mobile money: 83.5% of women, 91.7% of men have a mobile money account (Findex 2024).
- Network coverage in coffee areas: OpenCelliD.
- Rainfall: CHIRPS and NASA POWER for the reference location.
- Smallholder context: LSMS-ISA where relevant.

Every number shown in the app, README or videos must have a source next to it, or be labelled "assumption" or "synthetic".

### 6.3 Synthetic data
Allowed for officer-dashboard seed referrals and SMS simulation only. Every synthetic record has `synthetic: true` and is visibly tagged in the UI.

---

## 7. AI value proposition (answer this the same way everywhere)

**What the AI does:** computer vision. A small on-device convolutional network reads leaf photos and estimates which leaf problem is present and how many sampled leaves are affected, and knows when it does not know.

**Why a simpler tool cannot do this job:**
- SMS or a hotline needs Noor to name the disease. She cannot, which is the problem.
- A spreadsheet or rule table needs a symptom as input. The AI turns a photo into that input.
- A web search needs data, literacy, English and a name to search for.
- An extension officer can, but comes twice a year.

**Where we deliberately do NOT use AI:** the advice itself (a rule table an officer can audit), the timing (a calendar), the price (a lookup, if built). Saying this is part of our answer.

**Guardrails:** fixed answer list, abstention thresholds, quality gate, out-of-distribution rejection, multi-leaf agreement, human decides, officer confirms, nothing sent without a tap.

---

## 8. Responsible AI (pass/fail; write `RESPONSIBLE_AI.md`)
- **Human oversight:** Noor chooses act / wait / ask. Officer confirms or corrects every referral. No automatic actions.
- **Fail-safe:** abstain when top-class probability is below a calibrated threshold, when leaves disagree, when photo quality fails, or when the OOD score fires. Abstention always leads to "ask the officer" with a pre-filled referral.
- **Calibration:** temperature scaling on a validation split; report coverage versus accuracy at the chosen threshold.
- **Privacy:** all data stays on the phone by default. Photos leave only with a second explicit consent. Referral SMS carries member number, not name. No location finer than plot ID unless consented.
- **Shared phone:** the smartphone belongs to the daughter. Records sit under a household profile; a 4-digit PIN option hides history. Lost phone: data is local and minimal; the cooperative holds the registry, not us.
- **Consent:** spoken consent in the chosen language before first use and before any sync.
- **Bias:** report per-class and per-dataset performance (Kenya vs Uganda vs Ecuador). State the variety and lighting gaps. Plan to collect local photos through officer corrections.
- **Content safety:** every answer in the bank is reviewed by a person; pesticide guidance points to the cooperative or officer for product and dose; no invented doses.
- **Language risk:** Kikuyu audio is machine-generated (MMS-TTS) and marked "pending native speaker review"; Swahili audio is reviewed before release.

---

## 9. Evidence plan (what we will show judges)
Produce `EVALUATION.md` with:
1. In-domain test accuracy and per-class F1 (JMuBEN + BRACOL held-out split).
2. **Cross-domain results on the Uganda set and RoCoLe**, reported even if worse. This honesty is the point.
3. Selective prediction: accuracy on accepted cases versus coverage, at our threshold.
4. OOD rejection rate on non-coffee leaves and random photos.
5. Model size, bundle size, inference latency, airplane-mode test result.
6. A confusion matrix image.
7. Five worked examples (photo, prediction, confidence, answer card) including at least two abstentions.
8. A plain-language paragraph on what these numbers do and do not prove.

Never present an accuracy number without naming the test set.

---

## 10. Tool usage policy (use a tool only when it serves a requirement)

| Tool | Use for | Do not use for |
|---|---|---|
| **Cursor** | Main IDE for the repo: ML training scripts, ONNX integration, PWA/offline work, tests, docs. Multiple agents on separate branches per workstream. | Rewriting Lovable-generated UI wholesale. |
| **Lovable** | Fast UI for the farmer app shell and the officer dashboard, Supabase backend for referrals, hosting the live URL. Synced to GitHub. | ML training. Runtime LLM features. |
| **ElevenLabs** | Pre-render the fixed Swahili answer bank (and English) to audio at build time. Optionally Scribe for video captions. | Runtime TTS, AI narration of our videos (keep human voices on camera). |
| **BrightData** | Tier 3 only: scrape public coffee price references (e.g. Nairobi Coffee Exchange results, ICE Arabica reference, FX) for an offline price card; collect public Kenyan extension leaflets to ground the answer bank text. Record source URL and date for each item. | Anything that breaks site terms; scraping personal data. |
| **Claude** | Planning, reviews, requirement checks, docs, evaluation write-ups. | Unreviewed agronomic advice. |

Never commit API keys. Pre-rendered audio means no ElevenLabs key ships in the client.

---

## 11. Videos (3 x max 60 s, MP4/MOV, max 1 GB). Must jointly cover all five PDF items.

PDF content items: (a) problem statement sentence, (b) AI capabilities and why not a simpler tool, with guardrails, (c) end-to-end demo, (d) where the tool sits in the user's day plus tech stack, (e) your take on localising AI.

**Video 1: Team introduction (covers a, e).** Real faces, real voices. Who we are, why this sector. Read the problem statement sentence. Close with what localising AI means to us.

Problem statement (fill in verified evidence):
> Because of Jani, Noor will know which coffee rows have leaf rust and can protect them before the short rains, on the weekend she checks, when she would otherwise find out only after the yield has dropped or when the extension officer next visits; we know because Kenya has one extension agent per 1,380 farmers against a 1:400 FAO recommendation (Ministry of Agriculture, 2025) and rust peaks after the rains with losses above 75% in severe outbreaks (Agronomy, 2021).

**Video 2: Product demo (covers c, d).** Screen recording plus phone on camera. Airplane mode visible. Leaves on a sheet, 10 photos, plot summary, Swahili audio plays, one Kikuyu clip plays, one abstention ("not sure, ask the officer"), referral SMS pre-filled, Noor taps the decision, officer dashboard receives and confirms. Caption the timeline of Noor's week.

**Video 3: Technical walkthrough (covers b, d).** Architecture diagram, model and bundle size, datasets and their gaps, cross-domain results, abstention curve, why not SMS/spreadsheet/search, guardrails, stack.

Rules for all videos: under 60 s (aim for 55 s), 1080p, burned-in English captions, no stock music clichés, no AI voice narration, every number on screen has its source in small text. Export a 3-minute concatenated backup cut.

---

## 12. Requirements traceability matrix (build and test against every row)

Keep this as `REQUIREMENTS.md` with a Status column (todo / pass / fail) and an Evidence link. Nothing is "done" until its test passes and the evidence is linked.

| ID | Requirement (source) | How we meet it | Acceptance test | Evidence |
|---|---|---|---|---|
| R1 | Runs on a device the user already has (§06) | PWA on the household Android smartphone; SMS on her basic phone | Install and run on a real Android phone (or throttled Chrome mobile emulation, stated) | Screen recording |
| R2 | Core feature works offline (§06) | Service worker caches app, model, audio, rules | Airplane mode: full leaf check end to end | Video 2 clip |
| R3 | Model small enough to side-load or send over weak link (§06) | int8 ONNX, at most 5 MB; bundle at most 15 MB | File sizes printed in build log; download time at 1 Mbit/s computed | EVALUATION.md |
| R4 | At least one interaction in a named local language, voice or text (§06) | Swahili voice + text for all answers | Every answer ID has Swahili text and audio | Answer bank table |
| R5 | Ready for "less-supported language" question (§06) | Kikuyu subset via MMS-TTS (CC BY-NC 4.0, flagged in docs); process to add a language documented | Kikuyu clips play for at least 5 core answers; doc describes 30-clip recording path | LANGUAGES.md |
| G1 | Human makes the final call (§06) | Act / wait / ask buttons; officer confirms | No code path performs an action without a user tap | Code review + demo |
| G2 | Agentic steps check in with user (§06) | SMS opened pre-filled, user sends | Referral never auto-sends | Demo |
| G3 | Avoid hallucinations (§06) | Fixed answer list; no generative runtime | Grep: no LLM calls in client; every rendered answer exists in the bank | Test |
| P1 | Fail-safe: "not sure, ask a person" (§09) | Calibrated threshold, quality gate, OOD, disagreement rule | Blurry, dark, non-leaf and mixed inputs all abstain | Test images + video |
| P2 | Credible privacy, consent, bias, oversight (§09) | RESPONSIBLE_AI.md, consent screens, on-device storage | Reviewer checklist passes | RESPONSIBLE_AI.md |
| D1 | Cite all data sources (§07) | DATA_CARD.md and in-app "Sources" page | Every dataset and statistic has a citation | DATA_CARD.md |
| D2 | Problem data with source, year, country (§7.2) | Problem evidence table | Each figure has all three fields | README |
| D3 | Build data: name, source, licence, size (§7.2) | Data card | All four fields filled for every set | DATA_CARD.md |
| D4 | State what data does not cover (§7.2, scored) | "Gaps" section per dataset and for the model | Section exists, specific, not generic | DATA_CARD.md |
| D5 | Synthetic data labelled (§7.2) | `synthetic: true` flag and UI tag | Every synthetic record tagged | DB query |
| W1 | Working prototype (§05) | Live URL | URL loads on a fresh phone; full flow works | Live URL |
| W2 | Clear AI technique and why not simpler (§05) | Section 7 text in README and Video 3 | Present in both | README, Video 3 |
| W3 | Proof it works on real examples (§05) | Cross-domain evaluation, worked examples | EVALUATION.md complete | EVALUATION.md |
| B1 | One better agricultural decision (Annex B) | Act / wait / ask on leaf problem, with timing and referral | Demo shows the decision being made | Video 2 |
| B2 | Addresses extension gap and registry precondition (Annex B) | Referral keyed to coop member number; officer queue | Officer dashboard receives referral | Video 2 |
| S1 | Live project URL (platform) | Lovable publish or Vercel | Opens in incognito on mobile | URL |
| S2 | Code link; repo public after submission (platform) | GitHub repo, MIT licence, no secrets | `git log -p` secret scan clean; repo set public right after submit | Repo |
| S3 | 3 videos, each MP4/MOV, max 60 s, max 1 GB (platform) | Section 11 | `ffprobe` duration under 60 s, size under 1 GB, container MP4/MOV | Files |
| S4 | Videos jointly cover PDF items a to e (§08) | Section 11 mapping | Checklist ticked per video | Checklist |
| S5 | Submitted before 4 Oct 2026 15:00 CEST | Freeze 13:30 | Submission confirmation screenshot | Screenshot |
| J1 | Scalability and reuse (§09) | Model + rule table + answer bank are swappable per crop/language; cooperative-based rollout | REPLICATION.md describes cocoa in Côte d'Ivoire as an example swap | Doc |

---

## 13. Repository layout

The git repo is `MIT_Hackathon_7/app/` (Lovable-synced). Full layout and path owners: `kb/OWNERSHIP.md`.
```
app/src/pages, src/components   UI screens (Lovable): farmer "/" and officer "/officer"
app/src/engine                  offline logic: inference, quality, rules, storage, referral
app/src/content                 answers.json, rules.json, season.json, i18n, sources.json
app/public/model                leaf.onnx, model.json
app/public/audio                sw/*.mp3, kik/*.mp3, en/*.mp3
app/ml                          training, export, quantisation, evaluation scripts
app/backend                     build-time scripts using API keys; .env (git-ignored)
app/docs                        REQUIREMENTS, EVALUATION, DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION, ARCHITECTURE
app/README.md                   problem, user journey, AI value, stack, data, limits, how to run
```

---

## 14. Agents (briefs in `kb/agents/`; humans review merges)

Builders (active now): **research**, **ml**, **engine**, **ui** (Lovable), **content-voice**, **docs**. One brief each in `kb/agents/<name>.md`.
Added later: **qa** (runs the Section 12 matrix, has veto on "done"), **redteam** (attacks the pass/fail safety gate), **judge** (scores us against the weighted criteria), **pitch** (videos, problem statement, submission form).
Expert reviewers (added Sat 3 Oct, late): **mathematician** (statistics, sampling, decision rule, calibration, evaluation validity; reports in `kb/math/`) and **agronomist** (practising Kenyan coffee farmer and agronomist: protocol, advice cards, safety, cooperative realism; reports in `kb/agronomy/`). They review and route fixes; they never edit other agents' files.
Second expert wave (Sun 3 Oct night): **ux-designer** (low-literacy and accessibility audit; `kb/ux/`), **user-simulator** (persona walkthroughs of the live app; `kb/usersim/`), **security-privacy** (secrets, access control, consent, licences; `kb/security/`), **release-manager** (submission checklist, consistency sweep, fallback, go / no-go from 09:30; `kb/release/`).
Coordination: `kb/STATUS.md`, `kb/DECISIONS.md`, `kb/OWNERSHIP.md`, `kb/CONTRACTS.md`.

---

## 15. Timeline (CEST). Cut lines are not optional.

| Time | Milestone |
|---|---|
| Sat 20:00 to 21:00 | Confirm Section 0. Repo, Lovable project, GitHub sync, data downloads started. |
| Sat 21:00 to 01:00 | Model v1 trained and exported. PWA shell offline with a dummy model. Answer bank v1 and Swahili audio rendered. |
| Sun 01:00 to 06:30 | Sleep. Long training or evaluation runs overnight only. |
| Sun 06:30 to 09:30 | Real model in the app. Abstention and quality gate. Officer dashboard. Kikuyu clips. |
| **Sun 09:30 cut line** | If the model is not in the app, ship the best working version and stop adding features. Drop Tier 2 and Tier 3. |
| Sun 09:30 to 11:00 | Run Section 12 matrix. Fix fails. Evaluation and docs. |
| Sun 11:00 to 12:45 | Record and edit three videos. |
| Sun 12:45 to 13:30 | Final QA, secret scan, live URL check on a phone. |
| **Sun 13:30** | Freeze. Submit. |
| Sun 13:30 to 15:00 | Buffer only. Make repo public once submission is confirmed. |

Scope tiers:
- **Tier 1 (must ship):** offline PWA, on-device model with abstention, 10-leaf plot summary, rule-based action card with season timing, Swahili voice and text, consent, local storage, referral SMS, officer dashboard receiving referrals, EVALUATION, DATA_CARD, RESPONSIBLE_AI, live URL, three videos.
- **Tier 2:** Kikuyu clips, officer label correction loop and export, measured device latency, bundle cost in local currency.
- **Tier 3:** offline price reference card (non-AI, BrightData-sourced, dated), simulated SMS reminder line with 1/2/3 replies.

---

## 16. Anti-slop rules (every agent follows these)
- No marketing language: no "revolutionise", "empower", "seamless", "cutting-edge", no gradient hero sections, no emoji in the UI.
- No number without a named source or a visible "assumption" / "synthetic" label.
- No accuracy figure without the test set named. Show the bad cross-domain numbers too.
- No feature that is not in the user journey (Section 4).
- No mock that pretends to be real. Simulated parts are labelled "simulated" on screen.
- UI for Noor: large touch targets, icons plus audio for every instruction, one action per screen, works at 360 px width, readable in sunlight (high contrast), no text-only instructions.
- Prose in docs: short sentences, plain British English, concrete nouns, no em dashes.
- When unsure about agronomy, write "ask the officer", not a guess. That applies to us as builders, not only to the app.

---

## 17. Definition of done
- Every row in Section 12 is "pass" with linked evidence.
- A person who has never seen the project can open the live URL on an Android phone, go offline, and complete a leaf check in Swahili in under 3 minutes.
- Three videos pass `ffprobe` checks and cover items a to e.
- Repo has README, DATA_CARD, EVALUATION, RESPONSIBLE_AI, LANGUAGES, REPLICATION, MIT licence, no secrets.
- Submitted before 13:30 CEST, confirmation saved.

---

## Sources used to shape this prompt
- Official brief: "Small AI for Development Hackathon, Concept Note", World Bank Youth Summit x Hack-Nation, 2026 (project file `world_bank_Challenge.pdf`).
- JMuBEN dataset, Mendeley Data: https://data.mendeley.com/datasets/t2r6rszp5c/1
- Uganda coffee leaf dataset, Mendeley Data: https://data.mendeley.com/datasets/k36wnd6knb/1
- RoCoLe dataset paper (CC BY): https://pmc.ncbi.nlm.nih.gov/articles/PMC6727496/
- Coffee Leaf Rust in Kenya, a review, Agronomy 2021: https://www.mdpi.com/2073-4395/11/12/2590
- Kenya Agricultural Sector Extension Policy 2023: https://kilimo.go.ke/wp-content/uploads/2024/10/KENYA-AGRICULTURAL-SECTOR-EXTENSION-POLICY-2023.pdf
- Kilimo Trust on extension coverage: https://x.com/kilimoEAC/status/1922614393646284879
- Meta MMS-TTS Kikuyu: https://huggingface.co/facebook/mms-tts-kik
- ElevenLabs model language support: https://elevenlabs.io/docs/overview/models
