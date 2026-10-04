# Gemini cross-check (v2, replaces the checklist in 09_gemini_review.md for the text pass)

How to use: open Gemini Pro. Attach `app/src/content/answers.json`, `app/src/content/rules.json`, `app/qa/decision_matrix.md`, `kb/research/GUIDANCE.md`, `kb/research/swahili_glossary.md`. Paste everything below the line. Run it as three separate chats (Part A, Part B, Part C) so each answer stays short. Paste the replies back to Claude; do not edit answers.json by hand.

Never attach `app/backend/.env`.

---

You are an independent reviewer for a hackathon entry called Jani. It is an offline app that helps Noor, a Kenyan smallholder coffee farmer in the Nyeri highlands, decide whether to act on a coffee leaf problem. She photographs 10 leaves; a small on-device model labels them (healthy, rust, cercospora, phoma, leaf miner, not sure); a fixed rule table picks one answer from a fixed list; the answer is shown and spoken in Swahili, Gikuyu or English. Nothing is generated at runtime. A person (Noor, then the extension officer) makes every decision. The attached files are the full answer bank, the rules, and the agronomy notes the answers were written from.

Rules for you:
- Be critical and specific. Praise is not useful.
- Do not invent. If you are not sure a word is correct Kikuyu or Kenyan Swahili, write "unsure" and say why. A confident wrong answer is worse than "unsure".
- Judge Swahili as spoken in rural central Kenya, not Tanzanian or textbook Swahili. Short sentences that sound natural when read aloud by a voice.
- Use plain British English. No em dashes.
- Return a markdown table, one row per answer ID, then a short list of cross-cutting problems. Do not rewrite the whole file.

## Part A: Swahili (every answer ID in answers.json)
Columns: `id` | `verdict` (ok / fix / unsure) | `problem` | `better Swahili` | `severity` (blocker / major / minor).
Check: meaning matches the English; natural for a rural Kenyan farmer; no term she would not know (flag "viwavi wachimbaji wa majani" for leaf miner and the term for copper spray specifically); consistent words for officer, cooperative, rust, copper; sentence length suitable for audio (flag anything over about 25 words); no accidental instruction to spray, mix or dose anything.
End with the five terms most worth asking a native speaker about.

## Part B: Gikuyu (only entries with a `kik` field)
Columns: `id` | `verdict` (plausible / clearly wrong / unsure) | `problem` | `suggested fix or "unsure"` | `severity`.
These lines were drafted by an AI without a Kikuyu tool and are marked pending native review. Say plainly which words look invented or borrowed from Swahili without need, which are not Gikuyu, and whether the meaning has drifted from English. Do not try to polish; flag. Give an overall rating: "usable as a labelled placeholder" or "should be removed from the demo".

## Part C: Agronomy safety and over-claims
1. Read `rules.json` and `decision_matrix.md`. List any plot summary where the app's answer could lead Noor to act wrongly (spray when she should not, wait when she should ask, ignore mixed problems, or treat phoma or leaf miner as sprayable). Quote the row.
2. Read each answer's English text. Flag: any dose, product, brand or percentage stated as fact; any advice that conflicts with `GUIDANCE.md`; timing advice that depends on a season window the app may not know; any claim that sounds like a diagnosis rather than a sampled estimate; missing mention that coffee berry disease, nutrient problems and root problems are not covered.
3. Check the "not sure" lines: does every act or watch card say what the tool does not know?
4. Name the three answers you would most want an extension officer to read before release, and why.
Severity for every finding: blocker / major / minor. Blockers are anything that could harm a farmer or break the rule "when unsure, ask a person".

## Part D: README and video claims (run later, with `app/README.md` and the three MP4s attached)
List every claim in the README or videos that is not supported by the attached files or has no source or "assumption" label. Say whether each video is under 60 seconds, whether numbers on screen are readable and sourced, and what would confuse a World Bank evaluator who has two minutes.
