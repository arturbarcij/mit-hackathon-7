# Jani

Jani is a coffee leaf check for Noor's household phone. She picks 10 leaves at the weekend, photographs them on a plain page, and gets one fixed answer: act, wait, or ask the extension officer. The phone can be offline after the first load.

The advice is a rule table, not a generated sentence. Every line the farmer hears is in `src/content/answers.json`.

## What works in this copy

- Language choice: Kiswahili, Gĩkũyũ, English. Kiswahili is a draft. Gĩkũyũ is a machine draft on eight lines, pending a native speaker.
- Spoken consent. Nothing is sent unless she taps.
- Photo check for blur, darkness and size, then a label. Unclear leaves stay "not sure".
- Plot summary, action card, and her own decision.
- Referral text of at most 160 characters. The SMS app opens only when she taps. This copy also keeps the message on the phone, because there is no live SMS gateway. That queue is labelled simulated.
- Officer list, pasted-message box, label correction, and a CSV export. Seed rows are labelled synthetic.
- Installable page with an offline cache.

## What this copy does not do

- There is no trained model file yet. Labels come from a mock: the sample name, the file name, or a rough colour guess. The screen says **Mock model**. There is no accuracy number, because there is no test-set result to report.
- Voice clips are not recorded yet. The play button says so, and the text stays on screen.
- The officer list is on this phone. It is not a shared cooperative server.

## Run

```bash
cd app
npm install
npm test
npm run dev
```

Open the site, then use "Fill 10 synthetic leaves" to walk the October rust case without farm photos. Those pictures are synthetic.

`npm run build` writes the offline bundle to `dist/`.
