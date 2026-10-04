# Video 3: Technical walkthrough (covers PDF items b and d)

Target 55 s, hard cap 60 s. 1080p MP4. A team member appears on camera in a corner window for the whole video and speaks every line. Screen content: architecture diagram, EVALUATION.md charts, code or repo tree. No AI narration.
Word budget 2.5 words a second. Checked by `python3 kb/pitch/make_srt.py --check`. Placeholders count as two words.
Every number below comes from app/docs/EVALUATION.md or the STATUS.md measured budgets table once the ml owner has filled them. Until then they stay `[PENDING: ml]`. Do not estimate.

## Beats

### 0:00-0:10 Three layers (10 s)
- SHOT: Architecture diagram (app/docs/ARCHITECTURE.md): cooperative map, phone, officer.
- SAY [Tech speaker]: "Three layers. The map decides where to look. The phone decides what it is. The officer decides what to do."
- ON SCREEN: diagram labels. Tag: "Map: synthetic deliveries and plots, real Sentinel-2 and rainfall."
- VARIANT IF THE MAP IS NOT BUILT (G4 not done at the 09:30 cut): "Two layers. The phone decides what it is. The officer decides what to do." Remove the map from the diagram. Do not show a map that does not run.

### 0:10-0:20 The model (10 s)
- SHOT: Terminal or table showing file sizes and latency from the build log.
- SAY [Tech speaker]: "A small convolutional network reads each leaf on the phone: [PENDING: ml] megabytes, [PENDING: ml] milliseconds, offline."
- ON SCREEN: "leaf.onnx [PENDING: ml] MB (cap 5 MB). Offline bundle [PENDING: ml] MB (cap 15 MB). Latency [PENDING: ml] ms per leaf on [PENDING: ml, device or 4x CPU throttle]." Add: "[PENDING: ml] seconds to download at 1 Mbit/s (computed)" and, if wanted, "15 MB is 6% of Safaricom's KSh 20, 250 MB daily bundle (Safaricom tariff, re-check on the day, my calculation)".
- RULE: state whether latency is a real Android device or Chrome with 4x CPU throttling.

### 0:20-0:31 Data and gaps (11 s)
- SHOT: Results table and the abstention curve (accuracy against coverage).
- SAY [Tech speaker]: "Trained on Kenyan Arabica leaves, tested on Uganda and Ecuador photos. Cross-country accuracy: [PENDING: ml]. It cannot see berries, nutrient problems or other varieties."
- ON SCREEN: "Train: JMuBEN and JMuBEN2 (Kenya, CC BY 4.0), BRACOL (Brazil, CC BY 4.0). Test: Uganda set (CC BY 4.0, contains augmented copies), RoCoLe (Ecuador, Robusta)." Each accuracy figure carries its test set name. Show the bad numbers too.
- ON SCREEN (gap line): "Not covered: berries, nutrients, roots, other varieties, night photos."
- NOTE: the Uganda set is augmented, so it is not a clean held-out set (DATASETS.md section 0). Keep that tag.

### 0:31-0:41 Why not a simpler tool (10 s)
- SHOT: Four small cards: SMS, spreadsheet, search, officer. Each crossed out with the reason.
- SAY [Tech speaker]: "SMS and spreadsheets need Noor to name the disease. The model turns a photo into that input. The advice is a plain rule table."
- ON SCREEN: "Officer: can, but visits twice a year at best (Annex B)". "AI only reads the photo. Advice, timing and price are not AI."

### 0:41-0:49 Guardrails (8 s)
- SHOT: Screens of the abstention, consent, referral composer.
- SAY [Tech speaker]: "No chatbot, only fixed answers. Doubt means ask the officer. Nothing is sent until Noor presses send."
- ON SCREEN: "Fixed answer bank, reviewed by a person. Abstain: low confidence, disagreement, bad photo, not a leaf. Human decides: act, wait, ask."

### 0:49-0:55 Stack and her day (6 s)
- SHOT: Repo tree and live URL.
- SAY [Tech speaker]: "React app, ONNX Runtime, Supabase. Saturday at the house; follow-up by SMS."
- ON SCREEN: "Vite, React, TypeScript, vite-plugin-pwa, onnxruntime-web, IndexedDB, Supabase. Voice clips rendered once at build time (ElevenLabs Swahili, Meta MMS-TTS Kikuyu, CC BY-NC 4.0). Live URL [PENDING: U3]. Repo [PENDING: S2, public after submission]."
- NOTE: Lovable and Cursor are build tools, not part of the product. Mention only if there is room.

## The cooperative loop in one sentence (only if the map is built)
Add to beat 1 on screen, not in speech: "Map flags a plot. Officer approves a nudge SMS. Noor runs the leaf check. The referral lands on the same map." (MASTER_PROMPT 3.5). All records on that map are synthetic and labelled.

## Checks before recording
- [ ] No `[PENDING: ...]` left in speech or on screen.
- [ ] Each number has its test set or source in small text.
- [ ] Latency device stated.
- [ ] Diagram matches what is built (map shown only if it runs).
- [ ] ffprobe under 60 s.
