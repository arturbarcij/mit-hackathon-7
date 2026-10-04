Build the front end for "Jani", an offline coffee-leaf check app for smallholder farmers in Kenya (hackathon prototype for a World Bank "Small AI" challenge). The user is Noor, a 38-year-old coffee farmer with low screen literacy who uses her daughter's cheap Android smartphone at weekends, at home, often offline. Design for that phone first: 360 px width, Chrome on Android.

IMPORTANT ARCHITECTURE RULES
- Do NOT implement any AI, ML, model loading, service worker or real storage. Another developer builds that in Cursor and syncs via GitHub.
- Create ONE placeholder module `src/engine/index.ts` (plus `src/engine/types.ts`) that exports MOCK implementations with exactly these signatures, and import everything from it. After this first build, never modify files in `src/engine/`.
  Types: Lang = 'sw' | 'kik' | 'en'; Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf'.
  QualityResult { ok: boolean; reason?: 'blurry' | 'dark' | 'too_small'; blur: number; brightness: number }
  LeafResult { label: Label | 'unsure'; probs: Record<Label, number>; confidence: number; quality: QualityResult; abstained: boolean; modelVersion: string }
  PlotSummary { n: number; counts: Record<Label, number>; uncertain: number; dominant: Label | 'none'; affected: number; distinctProblems: number }
  AnswerCard { id: string; severity: 'ok' | 'watch' | 'act' | 'ask'; text: Partial<Record<Lang,string>>; notSure?: Partial<Record<Lang,string>>; audio: Partial<Record<Lang,string>>; sources: string[]; assumption: boolean }
  Decision = 'act' | 'wait' | 'ask'
  Functions: loadModel(): Promise<{version: string; mock: boolean}>; checkQuality(img: ImageBitmap): QualityResult; classifyLeaf(img: ImageBitmap): Promise<LeafResult>; summarisePlot(leaves: LeafResult[]): PlotSummary; decide(summary: PlotSummary, date: Date): AnswerCard; buildReferral(check): string; smsLink(number: string, body: string): string; play(answerId: string, lang: Lang): Promise<void>.
  Mock behaviour: classifyLeaf returns a deterministic pseudo-random label (mostly rust or healthy, about 1 in 8 'unsure'), loadModel returns mock: true, play() just resolves.
- Every visible string comes from translation files `src/content/i18n/en.json`, `sw.json`, `kik.json` keyed by language (start sw and kik as copies of English; a translator fills them later). No hard-coded English in components.

FARMER FLOW (route "/"), one action per screen, big buttons
1. Language: three large buttons "Kiswahili", "Gĩkũyũ", "English", each with a speaker icon.
2. Consent: short plain explanation (data stays on this phone; nothing is sent unless you press send), audio button, Yes / No.
3. How to pick leaves: simple illustration (SVG or icons) of picking 10 leaves from the worst rows and laying them on a plain sheet of paper. Audio button. "Start" button.
4. Capture loop: "Leaf 3 of 10" progress, one big camera button using <input type="file" accept="image/*" capture="environment">. After each photo: thumbnail, quality result (retake if not ok), then the label as icon plus word. 'unsure' leaves show a "?" icon, never a guess. Allow finishing early after 5 leaves.
5. Plot summary: grid of thumbnails with state icons, one sentence such as "6 of 10 leaves show rust, 1 not sure", replay-audio button.
6. Action card: from decide(): icon by severity, short text, "What we are not sure about" line, small "Source" link, audio button.
7. Decision: three large buttons "I will act", "I will wait", "Ask the officer". The app never decides for her.
8. Referral: preview of the SMS text from buildReferral, cooperative phone number field (remembered), "Send SMS" button that opens smsLink(). A toggle "also share photos when online" (off by default, second consent).
9. History: list of past checks (in-memory for now).
10. Sources and limits page: what the model learned from and what it cannot see (berries, nutrient problems, other varieties). Placeholder text from i18n.
Persistent header: offline/online indicator, language switch, and a visible amber "MOCK MODEL" badge whenever loadModel() reports mock: true.

OFFICER ROUTE ("/officer"): just a placeholder page for now ("Officer dashboard, coming next"). No backend yet.

DESIGN RULES (strict)
- Low literacy: icon + one short line + audio button on every screen. No paragraphs.
- Touch targets at least 56 px, base font 18 px, high contrast, readable in sunlight.
- Calm, practical look: off-white background (#FAF8F3), near-black text, one deep green accent (#2F5D3A), amber for warnings (#B7791F), red for "ask officer" (#B42318). No gradients, no glassmorphism, no emoji, no stock hero images, no marketing copy, no landing page. The app opens straight into the flow.
- Leaf state icons must be distinguishable without colour (shape plus label).
- lucide icons. Respect prefers-reduced-motion.
