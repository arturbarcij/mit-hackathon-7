Build the front end for "Jani", an offline coffee-leaf check app for smallholder farmers in Kenya, plus an officer dashboard for the coffee cooperative (hackathon prototype, World Bank "Small AI" challenge). The farmer is Noor, a 38-year-old coffee farmer with low screen literacy who uses her daughter's cheap Android smartphone at weekends, at home, often offline. Design the farmer side for that phone first: 360 px width, Chrome on Android.

ARCHITECTURE RULES
- Do NOT implement any AI, ML, model loading, service worker or real storage. Another developer replaces the engine via GitHub.
- Create ONE placeholder module `src/engine/index.ts` (plus `src/engine/types.ts`) with MOCK implementations of exactly these signatures, and import everything from it. Never modify `src/engine/` after this first build.
  Types: Lang = 'sw' | 'kik' | 'en'; Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf'.
  QualityResult { ok: boolean; reason?: 'blurry' | 'dark' | 'too_small'; blur: number; brightness: number }
  LeafResult { label: Label | 'unsure'; probs: Record<Label, number>; confidence: number; quality: QualityResult; abstained: boolean; modelVersion: string }
  PlotSummary { n: number; counts: Record<Label, number>; uncertain: number; dominant: Label | 'none'; affected: number; distinctProblems: number }
  AnswerCard { id: string; severity: 'ok' | 'watch' | 'act' | 'ask'; text: Partial<Record<Lang,string>>; notSure?: Partial<Record<Lang,string>>; audio: Partial<Record<Lang,string>>; sources: string[]; assumption: boolean }
  Decision = 'act' | 'wait' | 'ask'
  Functions: loadModel(): Promise<{version: string; mock: boolean}>; checkQuality(img: ImageBitmap): QualityResult; classifyLeaf(img: ImageBitmap): Promise<LeafResult>; summarisePlot(leaves: LeafResult[]): PlotSummary; decide(summary: PlotSummary, date: Date): AnswerCard; buildReferral(check): string; smsLink(number: string, body: string): string; play(answerId: string, lang: Lang): Promise<void>.
  Mock: classifyLeaf returns a deterministic pseudo-random label (mostly rust or healthy, about 1 in 8 'unsure'); loadModel returns mock: true; play() resolves.
- Every visible string comes from `src/content/i18n/en.json`, `sw.json`, `kik.json` (start sw and kik as copies of English). No hard-coded English in components.

FARMER FLOW (route "/"), one action per screen, big buttons
1. Language: "Kiswahili", "Gĩkũyũ", "English", each with a speaker icon.
2. Consent: data stays on this phone; nothing is sent unless you press send. Audio button, Yes / No.
3. How to pick leaves: simple SVG illustration of picking 10 leaves from the worst rows and laying them on a plain sheet of paper, underside up. Audio button. "Start".
4. Capture loop: "Leaf 3 of 10", one big camera button using <input type="file" accept="image/*" capture="environment">. After each photo: thumbnail, quality result (retake if not ok), then the label as icon plus word. 'unsure' shows a "?" icon, never a guess. Allow finishing after 5 leaves.
5. Plot summary: thumbnails with state icons, one sentence like "6 of 10 leaves show rust, 1 not sure", replay-audio button.
6. Action card from decide(): icon by severity, short text, "What we are not sure about" line, small "Source" link, audio button.
7. Decision: "I will act", "I will wait", "Ask the officer". The app never decides for her.
8. Referral: SMS preview from buildReferral, cooperative number field (remembered), "Send SMS" opens smsLink(). Toggle "also share photos when online", off by default.
9. History: past checks (in memory for now).
10. Sources and limits: what the model learned from and what it cannot see (berries, nutrient problems, other varieties).
Header on every screen: offline/online indicator, language switch, amber "MOCK MODEL" badge when loadModel() reports mock.

OFFICER ROUTE ("/officer"): placeholder page "Cooperative dashboard: next step". No backend yet.

DESIGN RULES (strict)
- Low literacy: icon + one short line + audio button on every screen. No paragraphs.
- Touch targets at least 56 px, base font 18 px, high contrast, readable in sunlight.
- Off-white background #FAF8F3, near-black text, deep green accent #2F5D3A, amber #B7791F for warnings, red #B42318 for "ask the officer". No gradients, glassmorphism, emoji, stock images, marketing copy or landing page. Open straight into the flow.
- Leaf states distinguishable without colour (shape plus label). lucide icons. Respect prefers-reduced-motion.
