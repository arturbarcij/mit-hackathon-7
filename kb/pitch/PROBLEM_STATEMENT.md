# Problem statement (item a)

Owner: pitch. Status: draft v1, Sat 3 Oct. Format required by the brief (Section 08): "Because of this tool, [user] will [action] by [when] that they would otherwise [not do / do late / do worse]; we know because [evidence]."

## Written version (on screen in Video 1, and in the submission form)

> Because of Jani, Noor will check ten leaves from her worst coffee rows and decide whether to act, wait or ask the extension officer, on the weekend before the short rains, when she would otherwise find out about leaf rust late: after her yield has dropped, or when the officer next visits. We know because Kenya has one extension agent for every 1,380 farmers, against a national target of 1:600 and an FAO recommendation of 1:400 (Ministry of Agriculture and Livestock Development, Kenya, 2025). A review of coffee leaf rust in Kenya states that the disease "can cause yield losses in excess of 75% where outbreaks are severe", and that the peak comes soon after the rainy seasons (Agronomy, 2021).

## Spoken version (Video 1, about 24 seconds, read by a team member)

> Because of Jani, Noor will check ten leaves at the weekend and decide whether to act, wait or ask the officer, before the short rains. Otherwise she finds out about leaf rust late. Kenya has one extension agent for every 1,380 farmers. A 2021 review reports yield losses in excess of 75 percent when rust outbreaks are severe.

The spoken version drops the 1:600 and 1:400 comparators for time. They stay on screen in the source tag.

## Slot check against the brief

| Slot | Our text |
|---|---|
| user | Noor, 2 ha coffee farmer, Ondera Coffee Cooperative member (persona from the brief) |
| action | check ten leaves, then choose act, wait or ask the officer |
| when | the weekend, before the short rains (sprays start mid-October, repeat three weeks later) |
| otherwise | finds out late: after the yield drops, or at the officer's next visit (twice a year at best, per Annex B) |
| evidence | extension ratio (MoALD 2025), rust loss and timing (Agronomy 2021) |

## Evidence behind each number (from kb/research/EVIDENCE.md; sources.json IDs)

| Figure | Exact wording to keep | Source | Country, year |
|---|---|---|---|
| 1:1,380 | "Currently, the extension agent-to-farmer ratio is 1:1,380." Target 1:600 (ASTGS 2019 to 2029), FAO recommendation 1:400. | S02, Agriculture Extension Manual v1, Ministry of Agriculture and Livestock Development, PDF page 12 | Kenya, Feb 2025 |
| 75% | "The disease can cause yield losses in excess of 75% where outbreaks are severe" | S03, Agronomy 11(12):2590, review. The review cites an earlier work for this figure. | Kenya (review), 2021 |
| Peak after rains | "the peak of the disease coming soon after the rainy seasons" | S03 | Kenya (review), 2021 |
| Spray timing | sprays "start in mid-October, just before the start of short rains", second spray "three weeks after the first" | S03 | Kenya (review), 2021 |

## Rules for anyone editing this sentence

1. The 75% figure comes from a review, which cites an earlier work. It is not a Kenyan field measurement. Say "a review" every time, in speech and on screen. Keep "in excess of 75%" and "where outbreaks are severe".
2. Use 1:1,380 (MoALD 2025). Do not use "fewer than 5,000 officers for 8 million farmers" (unverified secondary, EVIDENCE.md E1).
3. Do not claim a national yield decline. FAOSTAT shows 308.3 kg/ha in 2020 and 435.7 in 2024 (EVIDENCE.md E3). Noor's drop is a farm-level story from the brief.
4. "Twice a year at best" is Annex B's wording about the officer's visits. It is not a statistic. Attribute it to the brief if shown on screen.
5. The ratio is national. No county-level figure was found (EVIDENCE.md E1, E6).

## Change from MASTER_PROMPT section 11 (for the lead to approve)

MASTER_PROMPT says Noor "will know which coffee rows have leaf rust". The app reads ten sampled leaves and gives a plot-level summary, not a per-row map. This version says she will "check ten leaves from her worst coffee rows and decide". It also adds the FAO and national comparators and drops "rust peaks after the rains" from the loss clause into its own sentence, so the loss figure is not read as the review's finding on timing. If Arthur prefers the MASTER wording, change it there first and tell pitch.
