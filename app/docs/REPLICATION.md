# Replication

Status: draft by the docs agent, 3 Oct 2026. Criterion: scalability, replicability, what next (10%). The cocoa example is a design exercise. We have not built or tested it, and we say so. (source: MASTER_PROMPT 5.2)

## 1. What is swappable

Jani is four swappable parts around a fixed engine. Changing crop, place or language does not change the code that runs the check.

| Part | File or folder | Swap for | Who does it |
|---|---|---|---|
| Model (crop and problems) | `public/model/leaf.onnx`, `model.json`; training in `ml/` | A model trained on the new crop's labelled photos | ML person, with an agronomist for the labels |
| Rule table (agronomy) | `src/content/rules.json` | New rules from local guidance | Extension officer signs off |
| Answer bank and audio (language) | `src/content/answers.json`, `public/audio/<code>/` | New text and recordings | Local speaker |
| Season file (location) | `src/content/season.json` | Rain-onset and spray windows for the new area | Agronomist; data from NASA POWER or CHIRPS |
| Referral target | cooperative SMS number and member-number format | The new cooperative or registry ID | Cooperative |

Not swappable without work: the capture protocol (plain sheet, several leaves) assumes a leaf-based problem. Fruit or root problems need a different protocol.

## 2. Preconditions (from the brief)

AI "stacked on absent registries, phones or trust will be hard to implement". Check all three before copying Jani.

| Precondition | Kenya coffee (now) | Check in a new setting |
|---|---|---|
| A cooperative or registry to route through | Cooperative member list; KIAMIS with over 6.5 million farmers by mid-2025 (PA01) | Is there a member list an officer can use? |
| Phones | 91.8% of women own a phone, 42% a smartphone (2024, S07, S06) | What share own a basic phone? A smartphone? Who holds it, and when? |
| Trust in the advice | Officer confirms every referral | Will the farmer act on a card the officer has signed off? |
| A person to receive referrals | Extension officer, 1 per 1,380 farmers (S02) | Who reads the SMS, and how fast? |

## 3. Worked example: cocoa in Côte d'Ivoire

This is a plan, not a result. Facts that need a source are marked `TODO(research)`. We give no numbers for Côte d'Ivoire because we have not researched them.

**Decision supported.** "Do I need to act on a pod or leaf problem in my cocoa, and does the extension officer need to come?"

**Problems to cover first.** Black pod disease (a pod problem) and cocoa swollen shoot virus (a leaf and shoot problem). These two are named in the project brief as the example. `TODO(research)`: confirm with a published source that both are priority problems, and find the main extension body.

**What changes.**

| Part | Change | Open question |
|---|---|---|
| Model | New classes: healthy, black pod, swollen shoot symptoms, not sure, not cocoa | `TODO(research)`: find open labelled cocoa image sets and their licences. Do not assume any exist. |
| Capture protocol | Black pod is on the pod, not the leaf. The "10 leaves on a sheet" protocol must become "10 pods or leaves" and be tested. | `TODO(ml)`: does the plain-sheet protocol work for pods? |
| Rule table | New incidence bands and season timing for cocoa | `TODO(research)`: published thresholds. If none, mark "assumption, officer to confirm" as we did for coffee. |
| Swollen shoot | A virus. Visual symptoms overlap with other problems. Remedies involve removal and officer action. | The card should always say "ask the officer" and never advise cutting trees. |
| Language | French is the official language. Add one local language, chosen with the cooperative. | `TODO(research)`: confirm the official language and name candidate local languages. We will not guess. |
| Audio | French clips from a commercial voice service; local-language clips by a local speaker (about 30 clips, assumption) | Check the licence for commercial use. Meta MMS-TTS and NLLB are CC BY-NC (non-commercial). |
| Season file | Rain and harvest windows for the cocoa belt | `TODO(research)`: NASA POWER query for the chosen location, as done for Nyeri (modelled data) |
| Referral | Cooperative member number and SMS number in Côte d'Ivoire | Check the SMS length limit and the mobile network |

**Steps and rough effort (assumptions, not measured).**

1. Agree the decision and the officer partner (days).
2. Collect or find labelled photos; train and evaluate on a held-out set from a different farm (days to weeks, depends on data).
3. Write rules and answers with the officer; translate and record (days).
4. Evaluate honestly, including cross-domain results. Publish gaps as we do in `DATA_CARD.md`.
5. Pilot with one cooperative before anything else.

## 4. Scale path

- Kenya first: more coffee cooperatives use the same model. Officer corrections add local labelled photos. Referrals can carry a KIAMIS ID later (PA01).
- Other crops and countries: follow section 3.
- World Bank AgriConnect is the scale path named in the project brief. `TODO(research)`: add a verified link and one sentence on how Jani would plug into it. We have not read its documents.
- Cost of adding a farmer: the offline bundle is at most 15 MB, which is 6.0% of a KSh 20 daily 250 MB bundle (our calculation, S11, to re-check). Cost of the officer's time is not measured.

## 5. Limits of this document

- We tested nothing outside Kenyan coffee.
- Cocoa data availability is unknown.
- The effort figures are guesses and labelled so.
