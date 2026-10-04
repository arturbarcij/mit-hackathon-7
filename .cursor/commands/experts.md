# Experts: reviewer passes

Read `kb/WORKFLOW.md` first. Launch in ONE message as parallel `Task` calls with `run_in_background: true`. Use the pass time in each brief's Schedule table.

1. [mathematician] Next pass per `kb/agents/mathematician.md`. Report to `kb/math/YYYYMMDD_HHMM.md`.
2. [agronomist] Next pass per `kb/agents/agronomist.md`. Report to `kb/agronomy/YYYYMMDD_HHMM.md`.
3. [ux-designer] Next pass per `kb/agents/ux-designer.md` against the live URL at 360 px. Report to `kb/ux/`.
4. [user-simulator] Next pass per `kb/agents/user-simulator.md`, all personas. Report to `kb/usersim/`.
5. [security-privacy] Next pass per `kb/agents/security-privacy.md`. Report to `kb/security/`. Never print secrets.

Each prompt ends with "When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."
When they report, list blockers by owner and stop. The release-manager is launched separately from Sun 08:00 (see `/wave-d`).
