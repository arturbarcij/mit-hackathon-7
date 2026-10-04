# Replication

How another crop, country or language could reuse Jani, and what has to change.

Status: first draft. The worked example (cocoa in Côte d'Ivoire) is a design sketch. We have not researched cocoa datasets, guidance or languages yet, so this file gives no figures for it. Every cocoa item below is marked "to research".

## What is fixed and what is swappable

The engine (quality gate, model runner, plot summary, rules engine, referral, local storage, offline caching) does not know about coffee. Coffee lives in five swappable parts.

| Part | File | What it holds | Who changes it |
|---|---|---|---|
| Leaf model | `public/model/leaf.onnx`, `model.json` | Labels, input size, calibration temperature, abstention threshold, checksum | ml, retrained on the new crop |
| Rule table | `src/content/rules.json` | Plot summary and season window to answer ID. First match wins; last rule is "ask the officer" | Agronomist and extension officer |
| Answer bank | `src/content/answers.json` | Every sentence the farmer can see, per language, with sources | Content writer, reviewed by the officer and native speakers |
| Audio | `public/audio/<lang>/<answer id>.mp3` | One clip per answer per language | Local speakers (see `LANGUAGES.md`) |
| Season calendar | `src/content/season.json` | Named windows (for example before the rains, rains, dry) per area | From rainfall climatology, checked against local guidance |

Two parts are not swappable without engine work:
- The label list is typed in the engine (`healthy`, `rust`, `cercospora`, `phoma`, `miner`, `not_leaf` in `app/src/engine/types.ts`). A new crop needs new label names there and in the referral SMS fields.
- Season window names are a fixed set of five in the engine. A crop with a different calendar, or one rainy season, needs that list changed.

## Worked example: cocoa in Côte d'Ivoire

| Part | Coffee in Kenya (now) | Cocoa in Côte d'Ivoire (sketch) |
|---|---|---|
| Decision | Act, wait or ask the officer about a coffee leaf problem, before the rains | Act, wait or ask about a cocoa pod or leaf problem. Same three choices |
| What the model reads | One picked coffee leaf on a plain page | Pods for black pod disease; leaves and shoots for cocoa swollen shoot virus. Capture protocol to design with officers. To research |
| Model | Retrained small CNN, int8 ONNX | Same architecture, retrained. Open cocoa image datasets, their licences and sizes: to research |
| Rule table | Rust incidence and season window, from KALRO guidance [S1], [S2], [S3] | From Ivorian national cocoa guidance. Until that guidance is sourced, every cocoa rule routes to the officer. To research |
| Answer bank | Swahili, Kikuyu subset, English | French (official language) plus a local language chosen with the cooperative. Which one, and whether open speech tools cover it: to research |
| Audio | ElevenLabs for Swahili, MMS-TTS for Kikuyu | French by a licensed voice; the local language recorded by a local speaker (about 30 clips) |
| Season calendar | NASA POWER climatology at one Nyeri point | Same method at the new location. Cocoa areas have their own wet and dry seasons. To research |
| Referral | SMS with the coffee cooperative member number | SMS with the cocoa cooperative member number, if members have one. To research |
| Officer side | Extension officer, twice a year | National cocoa extension service or cooperative agronomist. To research |

What stays the same: offline PWA, quality gate, abstention, multi-leaf summary, fixed answers, human decides, SMS referral the farmer sends herself, consent, local storage, officer confirms.

## Preconditions from the brief

The brief warns that AI stacked on absent registries, phones or trust is hard to implement. Before a new rollout, check:
- **A registry.** A cooperative or agency with a member list and member numbers. Jani routes referrals through it. In Kenya, smallholders in practice join a cooperative to market coffee and receive a membership number [efi-eudr-kenya-coffee]. Without such a list, referrals have nowhere to land.
- **Phones.** At least a shared smartphone in the household for the weekend check, and a basic phone for SMS. In Kenya, 93% of women own a mobile phone and 42% a smartphone [gsma-mggr-2025]. The figures for the new country must be found.
- **Coverage.** GSM signal at the house for the SMS. Kenya reports 98.7% 2G population coverage nationally [ca-annual-2024-25], with no county breakdown.
- **Trust in advisory.** An officer or agronomist who will sign off the rule table and review referrals. Without that person, the "ask the officer" fail-safe has no one behind it.

## How it would scale

Through cooperatives, not app stores. One cooperative adopts it, its officer signs off the rules, members install the PWA once on a household phone, and referrals reach that officer. Each new cooperative needs its member numbers and its SMS number in the app. The model and rules can be shared across cooperatives in the same area.

World Bank AgriConnect was suggested as a scale path. We have not reviewed it yet, so we make no claim about fit. To research.

## Cost of a new setting

Without figures, in terms of work:
- Model: a labelled image set for the new crop, a retrain on one GPU, export and checks. The heaviest part.
- Rules and answers: an agronomist's time, plus officer sign-off.
- Language: about 30 recorded clips per language, by a local speaker.
- Season: one climatology pull and a check against local guidance.
- Engine: label names and, if needed, season window names.
