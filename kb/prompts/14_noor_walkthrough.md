# Prompt 14: Noor walkthrough script (pitch agent, Claude)

Use at Sun 10:00, with the real build running. Paste into the pitch chat with `kb/agents/pitch.md` loaded.

Task: write `kb/pitch/NOOR_WALKTHROUGH.md`, the exact sequence to record for Video 2 and to rehearse live. One row per beat:

| Beat | Time | What is on the phone | What the person says or does (no AI voice) | Audio the app plays | Label on screen | Proof it is real or simulated |

Base it on MASTER_PROMPT section 4 and `kb/pitch/VIDEO2_demo.md`. Cover: airplane mode shown, language pick, spoken consent, a plain sheet with leaves, at least four photos with one retake, plot summary, action card with its stated uncertainty, one abstention, the act / wait / ask tap, the pre-filled referral SMS (not sent automatically), the officer dashboard with a seeded record, and the Noor-week timeline caption.

Rules: total 55 s at 2.5 words a second for the spoken lines, checked with `python3 kb/pitch/make_srt.py --check`. Anything not built by 09:30 is cut and the walkthrough says so, not faked. Anything simulated is labelled "simulated" on screen. Noor is role-played and labelled. No gradients, no emoji, no marketing words. Plain British English, no em dashes.
Reply in five lines when done: done, not done, blocked on, unsure about, next.
