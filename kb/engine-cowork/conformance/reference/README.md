# reference/ (test oracle)

This folder is a small oracle for the conformance suite. It is not a competing engine and must not ship.
The product engine lives in `app/src/engine/` and is owned by the engine agent (Cursor).

It covers the pure modules only: `types`, `summarisePlot`, `seasonWindow`, `decide`, `buildReferral`, `parseReferral`, `smsLink`.
There is no model, storage, audio, sync or hooks here.

Each file follows `kb/CONTRACTS.md` line by line. Where CONTRACTS leaves a choice open, the oracle picks one and says so in a comment at the top of the file:
- `U` in the SMS is `summary.uncertain` (unsure plus not_leaf), so `N = healthy + R + C + H + L + U`.
- `Q` is the mean confidence of all leaves in whole percent, 0 when there are none. The Lovable UI uses the mean of accepted leaves only. The suite accepts any whole number from 0 to 100.
- A missing member, plot or decision is sent as `-`.
- `D` is the local calendar day of `createdAt`.
- `decide` returns `ask_officer` for any summary it cannot trust (null, NaN, negative, invalid date).

If the oracle and the QA harness ever disagree, the QA harness wins: fix the oracle and regenerate fixtures.
