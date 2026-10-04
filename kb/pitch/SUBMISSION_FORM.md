# Submission form text (skeleton)

Owner: pitch. Status: skeleton, Sat 3 Oct. Everything here is copied from MASTER_PROMPT or kb/research and must be re-checked against app/README.md and app/docs/* before paste. No new claims. Remove every `[PENDING]` by Sun 13:00 (done condition).
The platform field names are not known to pitch yet. [PENDING: Arthur, paste the exact field list from the platform if it differs from the headings below.]

## Eligibility
- All team members aged 18 to 35: [PENDING: Arthur, confirm each member]. Arthur is 27 (Oct 2026).
- Sector: Annex B, Agriculture.
- Team name / members / country: [PENDING: Arthur]

## Project title
Jani

## One-line summary (under 160 characters)
An offline leaf check for coffee farmers: ten photos, a plot summary in Swahili, and a pre-filled SMS to the cooperative when the tool is not sure.

## Short description (about 150 words)
Jani helps Noor, a coffee farmer in the Kenyan highlands, make one decision: act on a leaf problem, wait, or ask the extension officer. On the weekend, at the house, she photographs ten leaves from her worst rows on a plain page, on her daughter's smartphone, with no data connection. A small on-device model labels each leaf (healthy, rust, cercospora, phoma, leaf miner, or not sure). A fixed rule table and a season calendar turn the counts into a spoken answer in Swahili, with one Kikuyu subset. When the tool is unsure, it says so and opens a pre-filled SMS to the cooperative. Noor presses send. The officer sees referrals in a dashboard and confirms or corrects them. There is no runtime chatbot and no generated advice. The cooperative outlier map and the SMS reminder line [PENDING: keep only what is built and demoable]. Delivery records and plots are synthetic and labelled.

## The problem (problem statement, item a)
Copy the written version from kb/pitch/PROBLEM_STATEMENT.md. Keep the "review, not field measurement" wording for the 75% figure.

## AI technique and why a simpler tool would not do (item b)
Computer vision: a small on-device convolutional network (MobileNetV3-Small or EfficientNet-Lite0, int8 ONNX) reads leaf photos and estimates which problem is present and how many sampled leaves are affected. [PENDING: ml, confirm architecture and size.]
- SMS or a hotline needs Noor to name the disease. She cannot.
- A spreadsheet or rule table needs a symptom as input. The model turns a photo into that input.
- A web search needs data, literacy, English and a name to search for.
- An extension officer can, but visits twice a year at best (Annex B).
Where we do not use AI: the advice (rule table an officer can audit), the timing (a calendar), the price (a lookup, if built).

## Guardrails and Responsible AI
Human decides (act, wait, ask). Officer confirms. Nothing is sent without a tap. Fixed answer bank, each answer reviewed by a person. Abstains on low confidence, disagreement between leaves, bad photo, non-leaf image. Data stays on the phone unless a second consent is given. Referral SMS carries a member number, not a name. Full text: app/docs/RESPONSIBLE_AI.md. [PENDING: docs]

## Links
- Live project URL: [PENDING: U3]
- Code repositories: github.com/arturbarcij/mit-hackathon-7 (kb, ml, geo, qa, docs, backend) and jani-web (UI and engine, Lovable). Private until submission is confirmed, then public. [PENDING: S1/S2, final URLs]
- Video 1 (team): [PENDING: V1]
- Video 2 (demo): [PENDING: V1]
- Video 3 (technical): [PENDING: V1]
- Backup 3-minute cut, if the platform asks for one 2 to 5 minute video: [PENDING: V1]

## Data sources (copy from app/docs/DATA_CARD.md once docs has written it)
Build data, all CC BY 4.0 unless stated (sizes counted by research, kb/research/DATASETS.md):
- JMuBEN, Mendeley Data, Kenya: rust, cercospora, phoma, 22,588 images counted (22,591 stated), about 549 MB.
- JMuBEN2, Mendeley Data, Kenya: healthy and leaf miner, 35,962 images counted, about 1.29 GB.
- BRACOL, Mendeley Data, Brazil: 1,747 whole-leaf and 2,147 symptom images, about 165 MB. No phoma.
- Uganda coffee leaf dataset, Mendeley Data: healthy, rust, phoma, 3,322 files counted (3,312 stated). Test only. Contains augmented copies.
- RoCoLe, Ecuador (Robusta): 1,560 images. Test only.
- Non-coffee negatives: [PENDING: ml, name and licence].
Problem data, each with source, year, country: extension ratio (MoALD, Kenya, 2025), rust (Agronomy, Kenya review, 2021), yield (FAOSTAT and KNBS, Kenya, 2015 to 2024), phones (World Bank Findex 2024 and GSMA 2025, Kenya), data bundle price (Safaricom, 2026). Full list: kb/research/sources.json.
Synthetic: cooperative delivery records, plot shapes, officer-dashboard referrals, SMS reminders. All tagged `synthetic: true` and labelled on screen. Real: Sentinel-2 greenness, NASA POWER rainfall, [PENDING: geo, confirm].

## What the data does not cover (scored)
Coffee berry disease, nutrient deficiency, roots, wilt, drought stress, mixed infections, night photos, varieties such as SL28, Ruiru 11 and Batian, leaves on the tree with cluttered backgrounds. JMuBEN images are cropped to the lesion and partly augmented, so near-duplicates can leak across splits unless hashed first [PENDING: ml, state what was done]. Brazilian and Ecuadorian sets differ in conditions and crop type. No Kenyan incidence threshold exists in the sources we found, so every rule cut-off is an assumption pending officer confirmation. County-level extension coverage was not found.

## Evidence it works [PENDING: ml, from app/docs/EVALUATION.md]
In-domain: [PENDING: ml]. Cross-domain (Uganda, RoCoLe): [PENDING: ml]. Accuracy on accepted cases against coverage at our threshold: [PENDING: ml]. Rejection rate on non-coffee images: [PENDING: ml]. Model size, bundle size, latency, airplane-mode test: [PENDING: ml]. Every figure names its test set.

## Languages
Swahili: voice and text for every answer. Reviewer: [PENDING: L3]. Kikuyu: subset of answers, machine voice (Meta MMS-TTS, CC BY-NC 4.0), pending native-speaker review. English: text. Adding a language: record about 30 short clips, no retraining (LANGUAGES.md) [PENDING: docs].

## Limits (plain)
- Kikuyu voice is machine-generated and not yet reviewed by a native speaker.
- Rule thresholds are assumptions pending officer confirmation.
- Trained on Kenyan Arabica; tested on Uganda and Ecuador; not validated in Noor's own fields or on a low-end Android device [PENDING: ml, adjust if a device test was run].
- The 75% yield-loss figure is from a review, not a Kenyan field measurement.
- The SMS to dashboard step, reminder line and delivery records are simulated or synthetic.
- Tool informs, does not decide. It does not diagnose berries or give doses.

## What next / scalability
Swap model, rule table and answer bank per crop and language (REPLICATION.md, example: cocoa in Cote d'Ivoire) [PENDING: docs]. Referral can carry a KIAMIS ID (Kenya's farmer registry, over 6.5 million farmers registered by mid-2025, FAO 2026). List the tool in the World Bank AI Repository. Officer corrections as local training data [PENDING: engine, say "planned" if the export is not built].
