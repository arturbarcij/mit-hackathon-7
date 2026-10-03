# Replication

Jani is one crop, one rule table, one answer bank and one season file. Another place reuses the shell by swapping those four parts. The leaf model in this checkout is not trained. The cocoa sketch below is an illustration, not a built product.

## What swaps

| Part | What it encodes | Swap it for |
|---|---|---|
| Model | The crop and the visible problem | A small on-device model for that crop's photos, with its own data card and its own abstention test |
| Rule table | The agronomy an officer can audit | Local guidance for that crop and that season. Incidence cut-offs stay marked as assumptions until a local officer confirms them |
| Answer bank and audio | The language | A fixed list in the national language and a home language. About 30 short recordings (assumption) by a local speaker. No new language model at runtime |
| Season file | The location | Rain-onset windows for that area, cached on the phone, with the climate source named |

The phone flow stays the same. Photos at the house, a fixed answer, the farmer taps act, wait or ask, SMS to the organisation that already holds the member list, an officer confirms.

What does not swap cleanly is the institution. The model does not create a registry.

## Illustration: cocoa in Côte d'Ivoire

This is a sketch of the same shape. It is not a product, not a dataset we hold, and not a model we trained.

A cooperative in Côte d'Ivoire wants the same decision for cocoa: is there a pod or tree problem I should act on, and does the officer need to come? The two problems a local team would encode first are black pod and swollen shoot. The languages would be French and one local language chosen with speakers there.

The swaps would be:

- A cocoa photo model, trained and tested on images from that region, with a written list of what those images do not cover.
- A rule table from Ivorian extension guidance, signed by a local officer. No doses invented in the app.
- French audio for the full answer list, and a smaller set in the local language, recorded by a speaker, pending that speaker's review.
- A season file for the rainfall pattern of that area.

The farmer still uses a phone the household already has. The core check still runs offline. The referral still goes to the cooperative by SMS, and the farmer still presses send.

## Preconditions

The challenge brief states three preconditions. AI stacked on a missing registry, missing phones or missing trust is hard to implement. We treat that as a condition, not as a statistic.

- A cooperative or another farmer registry that already exists, so a referral can carry a member number.
- Phones people already have. In the Kenyan story that is a basic phone all week and a smartphone at the weekend.
- Trust in the advisory. Fixed answers, a named officer, and no invented doses are how this design earns that trust. They do not replace it.

## Scale path

The scale path is institutional. [AgriConnect](https://www.worldbank.org/ext/en/agriconnect) is the World Bank Group initiative that works through farmer organisations and digital tools for smallholders. Jani is a pattern a cooperative programme could host: on-device photos, a rule table the officer can read, and referrals into the registry the cooperative already keeps.

No AgriConnect target numbers are repeated here. They are not in our research notes.
