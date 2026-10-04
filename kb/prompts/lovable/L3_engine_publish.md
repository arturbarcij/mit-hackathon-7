The real engine has been pushed to src/engine via GitHub (same function signatures as the mock). Do not modify src/engine, vite.config.ts, public/model, public/audio, public/ort, public/geo or src/content/*.json.
1. Check every screen still works with the real engine; fix only UI code if something breaks.
2. Use src/content/i18n/*.json for all strings (the translator has filled sw and kik). Show "machine translation, pending review" under Kikuyu text.
3. Remove the MOCK MODEL badge logic only if loadModel() reports mock: false (keep the logic).
4. Publish the app and give me the URL.
