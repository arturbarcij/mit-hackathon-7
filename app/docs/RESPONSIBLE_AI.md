# Responsible AI

This note is the pass/fail account: a person decides, the tool abstains when it should, and we can say where data sits. The leaf model is not trained in this checkout. Coverage at the abstention threshold is [PENDING: ml].

## Human oversight

Noor chooses act, wait, or ask. The tool does not choose and does not act for her.

A referral opens in the SMS composer. She presses send. There is no path that sends on its own.

The officer confirms or corrects every referral that arrives. A correction is a new human label. It is not an automatic update of the model on her phone.

## Fail-safe and abstention

The check abstains, and the answer is "not sure, ask the officer", when any of these is true:

- The top-class probability is below the calibrated threshold.
- The sampled leaves disagree.
- The photo fails the quality gate (blur, darkness, or too small).
- The out-of-distribution check treats the image as not a coffee leaf.

Abstention leads to a pre-filled referral. Uncertain leaves are counted on their own and are not forced into a class.

The threshold, the coverage at that threshold, and accuracy on the accepted slice are [PENDING: ml]. No accuracy is claimed. Temperature scaling on a validation split is the planned calibration. It has not been run in this checkout.

## Privacy

Checks, photos and decisions stay in IndexedDB on the phone. That is the default.

Photos leave the phone only after a second, explicit consent. A referral SMS carries the cooperative member number, the plot id, the date, the counts and the answer id. It does not carry her name. Location in that SMS is the plot id, not a finer point, unless she consents to more.

There are no farmer accounts and no passwords. The officer dashboard is a separate, online view for referrals that were sent or synced.

We do not hold the farmer registry. The cooperative already does.

## Shared phone and lost phone

In the challenge story the smartphone belongs to her daughter and is available at the weekend. Records sit under a household profile on that phone. A 4-digit PIN (design choice) can hide history from the next person who opens the phone.

If the phone is lost, the leaf photos on it are local. The cooperative still holds the member list. We do not keep a cloud copy unless she has given the second consent and a sync has run.

## Consent

There are two consents, both spoken in the language she picked, before the matching step:

1. Before first use: what is stored, where it sits, and who can see it. She can refuse. The check does not start without this yes.
2. Before any sync: photos and the check record leave the phone only after a separate yes.

The SMS itself is a third tap. Opening the composer is not consent to sync the photos.

## Bias

Per-dataset and per-class scores are [PENDING: ml]. They will be reported for the Kenyan training images, the Uganda set and RoCoLe, including where the outside sets are worse.

Known gaps before any score exists:

- Variety is not labelled. SL28, Ruiru 11 and Batian are not classes.
- JMuBEN images are cropped to the lesion. BRACOL uses a white background and the underside of the leaf. Night photos are not in the sets.
- The Uganda set is augmented, so a cross-country number from it is not a clean field test.
- RoCoLe is Robusta on one Ecuadorian farm. Training images named as Arabica will not stand in for that.
- Healthy and miner counts in JMuBEN2 are much larger than the disease classes in JMuBEN. That is dataset balance, not prevalence on a farm.
- Phone and smartphone figures we cite are national (S06, S07), not a sample of women coffee farmers in Nyeri.

The planned mitigation is local: the officer's corrections become labelled photos from the same cooperative, under the capture protocol (plain sheet, daylight). That collection has not happened.

## Content safety

The answer bank is a fixed list. The phone does not generate a sentence at runtime.

Every answer is meant to be read by a person before release, and the rule table needs officer sign-off. That review is not done. Swahili in this checkout is a draft. Kikuyu has not been produced.

No answer may invent a pesticide product or a dose. The card points to the cooperative or the officer for the registered product and the rate. General clothing and washing advice, if used, comes from the FAO/WHO pesticide protection guidelines (S20, 2020) and stays general.

Incidence cut-offs in the rules are assumptions until an officer confirms them. A published Kenyan percent-of-leaves threshold was NOT FOUND.

## Language risk

Kikuyu is not translated yet and no Kikuyu audio has been produced. If Kikuyu voice is rendered later with Meta MMS-TTS (`facebook/mms-tts-kik`), that model is CC-BY-NC-4.0 (S30). The voice would be machine speech, marked pending native speaker review. It must not be described as a native recording.

Swahili answer text is a draft from a glossary that is mostly Tanzanian. Kenyan attestations we do have include `kutu ya majani ya kahawa` and `ugonjwa wa matunda ya kahawa`. It is pending a Kenyan Swahili speaker. Swahili audio, if rendered, is ElevenLabs at build time only, and a person reviews the clips before release. ElevenLabs licence terms for those clips were NOT FOUND in the research notes.

NLLB, if used to draft a translation, is CC-BY-NC-4.0 (S31) and is not a substitute for that review.

## Before a real deployment

This hackathon build is not a deployment. Before one, we would need:

- Native speaker review of Swahili, and a real Kikuyu translation if that language is included.
- Officer sign-off on the rule table, including every incidence band marked as an assumption.
- A local photo set from the cooperative's own plots and varieties, labelled by the officer.
- A data agreement with the cooperative for referrals, photo sync and how long records are kept.
- A fresh look at the CC-BY-NC-4.0 voice models before any commercial use.
- A re-check of the Safaricom bundle price on the day it is quoted (S11).
