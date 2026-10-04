# Video 1: Team introduction (covers PDF items a and e)

Target 55 s, hard cap 60 s. 1080p, MP4. Real faces, real voices, no AI narration. Burned-in English captions (CAPTIONS/video1.srt, generated from the SAY lines below by kb/pitch/make_srt.py).
Word budget: about 2.5 words per second, so at most 137 words. Bracketed placeholders count as two words.
Checked by `python3 kb/pitch/make_srt.py --check`.

## People needed (Arthur to fill)
- Speaker 1: [PENDING: Arthur, name and who speaks]
- Speaker 2: [PENDING: name, only if there is a second team member]
- All team members must be aged 18 to 35 (platform rule). Arthur is within range.

## Beats

### 0:00-0:08 Intro (8 s)
- SHOT: Both (or one) team members facing camera, laptop closed, plain background. Name captions bottom left.
- SAY [Speaker 1]: "We are [PENDING: names], team [PENDING: team name]. This is Jani, for Annex B, agriculture."
- ON SCREEN: names and one-line role each [PENDING: roles]. Title card text "Jani (Swahili for leaf)".
- NOTE: add one true sentence on why this sector only if a team member wants to say it. Do not invent a reason. Arthur: if you want it, take it from the 8 s above, not from the problem statement.

### 0:08-0:33 Problem statement (25 s)
- SHOT: Speaker 2 (or Speaker 1) to camera. Cut to a plain slide with the written sentence at 0:20, held for 6 s while the voice continues.
- SAY [Speaker 2]: "Because of Jani, Noor will check ten leaves at the weekend and decide whether to act, wait or ask the officer, before the short rains. Otherwise she finds out about leaf rust late. Kenya has one extension agent for every 1,380 farmers. A 2021 review reports yield losses in excess of 75 percent when rust outbreaks are severe."
- ON SCREEN (lower third, small): "1 extension agent : 1,380 farmers. Target 1:600, FAO 1:400. Ministry of Agriculture and Livestock Development, Kenya, 2025"
- ON SCREEN (second tag, small): "Losses in excess of 75% where outbreaks are severe: review, Agronomy 11(12):2590, 2021. Not a field measurement."
- NOTE: Noor is a persona from the Annex B brief. Do not present her as a real person.

### 0:33-0:52 Our take on localising AI (19 s)
- SHOT: Speaker 1 to camera. Optional B-roll: Kikuyu and Swahili answer cards on the phone, 3 s each.
- SAY [Speaker 1]: "For us, localising AI means the model learns from Kenyan leaves, the voice speaks Swahili and Kikuyu, and a person makes the decision. A new language is about thirty recorded clips, not a new model. Where AI adds nothing, we use a plain rule table."
- ON SCREEN (small tag): "Trained on Kenyan Arabica leaves (JMuBEN, CC BY 4.0). Kikuyu voice: machine-made, native review pending."
- ON SCREEN (small quote, optional): "AI must be used where it truly adds value." World Bank, 'Harnessing AI for Agricultural Transformation', Nov 2025.
- NOTE: this is the team's take. Edit it to the words the speaker would actually use, keep it under 47 words, keep the Kikuyu limit tag. "About thirty clips" is the plan in MASTER_PROMPT section 3.2; check LANGUAGES.md (docs agent) before recording and cut the sentence if the number is not there.

### 0:52-0:55 Close (3 s)
- SHOT: Both to camera.
- SAY [Both]: "Jani. Thank you."
- ON SCREEN: live URL [PENDING: U3] and repo name.

## Checks before recording
- [ ] Problem statement read exactly as in PROBLEM_STATEMENT.md spoken version.
- [ ] "a review" said aloud before the 75% figure (it is in the line).
- [ ] Every number on screen has its tag.
- [ ] Final length from ffprobe under 60 s.
