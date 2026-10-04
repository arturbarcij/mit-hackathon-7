# Wave D: gate and finish (Sun 09:30 to 13:30)

Read `kb/WORKFLOW.md` section 4, Wave D. Launch in ONE message as parallel `Task` calls with `run_in_background: true`, using the time column in the workflow as the order:

1. [qa] `--llm` cut-line run now; later `--strict --llm` at 12:30. A FAIL blocks submission.
2. [judge] Pass 2 now, pass 3 at 12:00.
3. [redteam] Pass 2 now, pass 3 at 12:00. Zero open blockers or a lead waiver in `kb/DECISIONS.md`.
4. [mathematician] Pass 2 now (check routed fixes landed, EVALUATION numbers honest), pass 3 at 12:00.
5. [agronomist] Pass 2 now (cards, protocol, safety lines), pass 3 at 12:00.
6. [ux-designer, user-simulator, security-privacy] Pass 2 now (09:45 to 10:00), final passes at 11:00, 12:15 and 12:30.
7. [release-manager] Pass 1 now; checklist, consistency sweep, `FALLBACK.md`; final passes at 12:00, 13:00, 13:25.
8. [docs] D3 final README; fix doc requests.
9. [pitch] After humans record: `ffprobe` each video, fill `video/COVERAGE.md` (a) to (e), build the 3-minute backup cut instructions, write `SUBMISSION_FORM.md`.
10. Builders (engine, ui, content-voice, ml): launch only for lines routed to them in `kb/STATUS.md`, one fix per task.

Each prompt ends with "When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."
At 13:30 do not launch anything new. Remind Arthur to submit, save the confirmation, then make the repo public.
