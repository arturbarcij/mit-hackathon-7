# Video 2: Product demo (covers PDF items c and d)

Target 55 s, hard cap 60 s. 1080p MP4. Screen recording of the phone plus a camera shot of the phone in hand. Humans speak on camera; Noor is role-played by a team member and labelled so. No AI narration. The only machine voices are the app's own Swahili and Kikuyu audio, which are the product being shown.
Word budget 2.5 words a second. Checked by `python3 kb/pitch/make_srt.py --check`.

## Labels that must be on screen
- Top corner, whole video: "Role-played. Noor is a persona from the Annex B brief."
- Officer screens: "Synthetic records" (D5 in MASTER_PROMPT).
- SMS receipt and reminders: "Simulated".

## Demo-ability check (done Sat 3 Oct, from STATUS.md and MASTER_PROMPT)
| Step in the demo | Needs | State on Sat night | Risk |
|---|---|---|---|
| Airplane mode, app opens | E2 PWA offline | todo | Low if E2 lands by 09:30 |
| Consent read aloud, language by speaker icon | UI plus audio (U1, C3) | UI done with mocks, audio todo | Medium |
| Ten photos on a plain sheet, quality gate with retake | E1, E3 | todo | Medium |
| Plot summary and result card | E3 real model | todo | High if the model misses the 09:30 cut |
| Swahili audio plays | C3 ElevenLabs | todo, needs L2 keys | Medium |
| One Kikuyu clip | C3 MMS-TTS | Tier 2 | Medium. If missing, cut beat 5 and say so |
| One abstention | M3 thresholds, quality gate | todo | Low: use a blurry or non-leaf photo |
| Pre-filled referral SMS | E1 referral builder | todo | Low |
| Officer dashboard shows the referral | U2, Supabase | doing | Medium |
| Referral appears on the cooperative map on Noor's plot | G1 to G4, U2 | all todo | **High. Not demoable tonight.** See below |

Important: there is no SMS gateway in the architecture (MASTER_PROMPT 5.1). A real SMS from the phone does not reach the dashboard by itself. In the video the officer's referral is a seeded record that matches the SMS text. Say "simulated" on screen. Do not imply the SMS arrived.

## Beats

### 0:00-0:06 Airplane mode (6 s)
- SHOT: Phone in hand at a table, status bar showing airplane mode. Cut to Jani opening from the home screen.
- SAY [Presenter]: "Saturday, at the house. Phone in airplane mode, so nothing here uses data."
- ON SCREEN: timeline bar starts: "Sat morning: pick leaves | Sat at the house: check, offline | Weekdays: SMS on her basic phone | Officer: visit". Highlight "Sat at the house".
- NOTE: item (d), where the tool sits in her day.

### 0:06-0:12 Language and consent (6 s)
- SHOT: Screen. Tap the speaker icon for Swahili. Consent screen plays aloud.
- SAY [Noor]: "I choose Swahili. It reads the consent screen aloud."
- ON SCREEN: "Swahili text and voice: translation review pending (L3)" until a reviewer has signed off, then remove.

### 0:12-0:21 Ten leaves (9 s)
- SHOT: Ten real leaves on a plain exercise-book page. Time-lapse of ten photos with counter 1/10 to 10/10. One blurry photo triggers "take it again".
- SAY [Noor]: "Ten leaves from my worst rows, on a plain page. One photo each. A blurry one gets a retake."
- ON SCREEN: "Photos of [PENDING: whose leaves, source, label honestly]". If the leaves are not coffee, say so on screen.
- NOTE: cross-check that the app really shows a retake prompt (quality gate, engine). If not, cut the last sentence.

### 0:21-0:30 Plot summary and Swahili answer (9 s)
- SHOT: Screen. Plot summary with icons, then the action card. Swahili audio plays for about 4 s.
- SAY [Presenter]: "The model runs on the phone. [PENDING: result from the take] of ten leaves show rust."
- ON SCREEN: card text in English as captions; "Thresholds are assumptions pending officer confirmation".
- NOTE: the number is whatever the app shows on the recorded take. Never edit it in.

### 0:30-0:38 Kikuyu clip (8 s)
- SHOT: Screen. Tap Kikuyu on one answer. Clip plays about 3 s.
- SAY [Presenter]: "Now Kikuyu. This voice is machine-made and awaiting native speaker review."
- ON SCREEN: "Kikuyu: Meta MMS-TTS, CC BY-NC 4.0, machine voice, native review pending."
- CUT RULE: if no Kikuyu clip exists by 09:30, delete this beat and give its 8 s to beat 3 and beat 6. Then say so in the submission form.

### 0:38-0:45 Abstention (7 s)
- SHOT: Screen. A blurry or non-coffee photo returns "Not sure. Ask the officer."
- SAY [Presenter]: "A blurry or non-coffee photo gets no guess: not sure, ask the officer."
- ON SCREEN: "Abstains on: low confidence, leaves disagree, bad photo, not a leaf."

### 0:45-0:50 The decision and the SMS (5 s)
- SHOT: Noor taps "Ask the officer". The SMS composer opens pre-filled, under 160 characters. Noor's thumb presses send.
- SAY [Noor]: "I tap ask the officer. I press send myself."
- ON SCREEN: "Pre-filled. Nothing is sent until she presses send."
- NOTE: in airplane mode the send will fail or queue. Either record the composer only and stop before send, or switch signal back on first. State which.

### 0:50-0:55 Officer confirms (5 s)
- SHOT: Officer dashboard on a laptop. Referral from Noor's plot at the top, officer taps confirm.
- SAY [Officer role, second team member]: "The officer sees the referral and confirms. Simulated records."
- ON SCREEN: "Synthetic records. SMS receipt simulated."
- VARIANT WITH MAP (use only if G4 passes and the map renders on the live URL): replace the line with "The officer sees it on the cooperative map, on Noor's plot, and confirms." and show plot P07 or Noor's plot highlighted with the "synthetic deliveries, real Sentinel-2 and rainfall" legend. If the map is not on the live URL by 11:00, use the line above and leave the map to Video 3.

## The cooperative outlier map in this video
MASTER_PROMPT 3.4 and 3.5 describe the map ("is it me, or is it everyone?") and a four-step loop: map flags a plot, officer taps send nudge, Noor does the leaf check, the referral lands on the same map. STATUS.md on Sat 23:35 has G1 to G4 all `todo` and U2 `doing`, and the map is Tier 1b that "must never block the farmer app". It is **not demoable tonight**. Rule: show the map only if G4 is `done` and it renders on the live URL. The nudge SMS (step 2) does not fit in 55 s; Video 3 covers the loop in one sentence. All delivery records and plot shapes are synthetic and must carry that label; satellite greenness and rainfall are real.

## Checks before recording
- [ ] Every step above performed on the live URL, not a mock.
- [ ] Airplane mode visible at 0:00 and again at the result.
- [ ] Kikuyu limit and Swahili review status on screen.
- [ ] "Simulated" and "Synthetic" tags visible on the officer screen.
- [ ] ffprobe under 60 s.
