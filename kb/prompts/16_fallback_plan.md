# Prompt 16: Fallback plan (release-manager, Claude)

Use at Sun 08:00 (pass 0), refresh at 12:00. Paste into a fresh chat with `kb/agents/release-manager.md` loaded.

Task: write `kb/release/FALLBACK.md`, a decision table for what we do if something fails after the 09:30 cut line. Columns: failure | how we detect it | fallback | who acts | latest time to switch | what we say in the submission.

Cover at least:
1. Real model not working in the browser (parity or size): ship the mock-free build with the model off? No. Decide with the lead: ship the abstain-everything build with the honest message, or the last model that passed parity. State which.
2. Live URL down or stale: redeploy from the GitHub repo to a second host; keep the Lovable URL and the backup URL in the form.
3. Offline mode fails on a fresh phone: what we claim, what we show, which video clip proves it.
4. Audio not rendered (ElevenLabs credits or key): text-only Swahili with a clear note; what the videos show instead.
5. Kikuyu clips not reviewed or not rendered: cut the Kikuyu beat, say so.
6. Officer dashboard or Supabase not working: seeded static data, labelled synthetic.
7. Swahili reviewer (L3) not found: ship with the "pending native review" label and the Gemini cross-check.
8. Videos over 60 s or failing `ffprobe`: trim rules and the 3-minute backup cut.
9. Submission form fails or the platform is slow: save text offline, screenshot, email contact in the brief.
10. Repo flip fails or secrets found: do not make public until clean; rotate keys.

Rules: every row has a time. Nothing is hidden: the fallback text says what is not working. Plain British English, no em dashes, no marketing language.
Reply in five lines when done: done, not done, blocked on, unsure about, next.
