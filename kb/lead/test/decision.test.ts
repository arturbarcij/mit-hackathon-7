import { readFileSync } from "node:fs";
import { answerCard, buildReferral, cardText, decide, decideId, seasonClock, seasonWindow, summarisePlot, meanConfidence } from "../src/engine/decision";
import { parseReferral } from "../src/lib/parseReferral";
import { mockClassify, pixelStats, qualityFrom } from "../src/engine/vision";
import type { PlotSummary, SeasonWindow, Label } from "../src/engine/types";
import answers from "../src/content/answers.json";

const ref = JSON.parse(readFileSync("test/ref.json", "utf8"));
let fails = 0; const fail = (m: string) => { fails++; if (fails < 15) console.log("FAIL", m); };
const ok = (c: boolean, m: string) => { if (!c) fail(m); };

// 1. Rule parity with the Python decision matrix (3,510 summaries)
for (const [d, a, u, di, w, card] of ref.matrix) {
  const counts = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 } as Record<Label, number>;
  const s: PlotSummary = { n: 10, counts, uncertain: u, dominant: d, affected: a, distinctProblems: di };
  const got = decideId(s, w as SeasonWindow);
  ok(got === card, `rule parity ${d} a=${a} u=${u} di=${di} ${w}: ts=${got} py=${card}`);
}
// every id the rules can return exists in answers.json and builds a card
const ids = new Set((answers as { id: string }[]).map((x) => x.id));
for (const row of ref.matrix) ok(ids.has(row[5]), `missing answer ${row[5]}`);
ok(answerCard("no_such_id").id === "ask_officer", "unknown id falls back to ask_officer");

// 2. summarisePlot vs independent Python reference (3,000 random plots)
for (const [labels, exp] of ref.cases) {
  const got = summarisePlot(labels.map((label: string) => ({ label })));
  ok(JSON.stringify(got) === JSON.stringify(exp), `summarise ${labels.join(",")}: ${JSON.stringify(got)} vs ${JSON.stringify(exp)}`);
}

// 3. Season windows for every day of 2026
for (const [iso, w] of ref.days) {
  const [y, m, dd] = iso.split("-").map(Number);
  ok(seasonWindow(new Date(y, m - 1, dd)) === w, `window ${iso}: ${seasonWindow(new Date(y, m - 1, dd))} vs ${w}`);
}

// 4. Season clock spot checks
const c1 = seasonClock(new Date(2026, 9, 4));
ok(c1.window === "pre_short_rains" && c1.sprayWindowOpen && c1.days === 32 && c1.nextRains.name === "short_rains" && c1.daysToRains === 33, "clock 4 Oct: " + JSON.stringify(c1));
const c2 = seasonClock(new Date(2026, 6, 1));
ok(c2.window === "dry" && !c2.sprayWindowOpen && c2.sprayWindow.name === "pre_short_rains" && c2.days === 92, "clock 1 Jul: " + JSON.stringify(c2));
const c3 = seasonClock(new Date(2027, 0, 10));
ok(c3.window === "dry" && !c3.sprayWindowOpen && c3.sprayWindow.name === "pre_long_rains" && c3.days === 41, "clock 10 Jan: " + JSON.stringify(c3));

// 5. Example: Noor's plot, 4 Oct, 6 rust, 2 healthy, 1 miner, 1 unsure -> rust_high_pre_rains (act)
const noor = summarisePlot(["rust","rust","rust","rust","rust","rust","healthy","healthy","miner","unsure"].map((label) => ({ label: label as Label | "unsure" })));
const card = decide(noor, new Date(2026, 9, 4));
console.log("Noor:", JSON.stringify(noor), "->", card.id, card.severity);
// 6 rust + 1 miner = 2 distinct problems -> mixed_problems (rule 2 before rust rules)
ok(card.id === "mixed_problems", "Noor example with a miner leaf goes to mixed_problems");
const noor2 = summarisePlot(["rust","rust","rust","rust","rust","rust","healthy","healthy","healthy","unsure"].map((label) => ({ label: label as Label | "unsure" })));
ok(decide(noor2, new Date(2026, 9, 4)).id === "rust_high_pre_rains", "6 rust pre rains -> rust_high_pre_rains");
ok(decide(noor2, new Date(2026, 11, 1)).id === "rust_high_in_rains", "6 rust in short rains -> rust_high_in_rains");
ok(decide(noor2, new Date(2026, 7, 1)).id === "rust_high_dry", "6 rust dry -> rust_high_dry");

// 6. cardText fallbacks and labels
const kik = cardText(answerCard("ask_officer"), "kik");
ok(kik.lang === "kik" && kik.machineDraft && !kik.untranslated, "kik machine draft flagged");
const kik2 = cardText(answerCard("rust_low"), "kik");
ok(kik2.lang === "en" && kik2.untranslated, "missing kik falls back to English with flag");
ok(cardText(answerCard("rust_low"), "sw").draft, "sw draft flagged");

// 7. Referral SMS round trip, always <= 160 chars
let longest = 0;
for (const [labels] of ref.cases.slice(0, 500)) {
  const s = summarisePlot(labels.map((label: string) => ({ label })));
  const id = decideId(s, "pre_short_rains");
  const sms = buildReferral({ memberId: "occ-0412", plotId: "7", date: new Date(2026, 9, 4), summary: s, answerId: id, confidence: 0.873, decision: "ask" });
  longest = Math.max(longest, sms.length);
  ok(sms.length <= 160, "sms too long " + sms);
  const p = parseReferral(sms);
  ok(!!p, "parse failed " + sms);
  if (p) {
    ok(p.member_id === "OCC0412" && p.plot_id === "P07" && p.check_date === "2026-10-04", "ids " + sms);
    ok(p.counts.rust === s.counts.rust && p.counts.cercospora === s.counts.cercospora && p.counts.phoma === s.counts.phoma && p.counts.miner === s.counts.miner, "counts " + sms);
    ok(p.counts.healthy === s.counts.healthy && p.uncertain === s.uncertain, "healthy/uncertain " + sms);
    ok(p.answer_id === id && p.decision === "ask" && p.confidence === 0.87, "answer/decision " + sms);
  }
}
console.log("longest SMS", longest, buildReferral({ memberId: "OCC0412", plotId: "P07", date: new Date(2026, 9, 4), summary: noor2, answerId: "rust_high_pre_rains", confidence: meanConfidence([{label:"rust",confidence:0.9},{label:"unsure",confidence:0.3},{label:"healthy",confidence:0.84}]), decision: "act" }));

// 8. Vision: synthetic images
function img(w: number, h: number, f: (x: number, y: number) => [number, number, number]) {
  const d = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const [r, g, b] = f(x, y); const i = (y * w + x) * 4; d[i] = r; d[i+1] = g; d[i+2] = b; d[i+3] = 255; }
  return pixelStats(d, w, h);
}
const noise = (x: number, y: number) => ((x * 73856093) ^ (y * 19349663)) % 40;
const leaf = (x: number, y: number): [number, number, number] => { const inLeaf = (x - 128) ** 2 / 100 ** 2 + (y - 96) ** 2 / 70 ** 2 < 1; const n = noise(x, y); return inLeaf ? [40 + n, 120 + n, 40 + n / 2] : [240 - n / 4, 240 - n / 4, 235 - n / 4]; };
const rusty = (x: number, y: number): [number, number, number] => { const spot = ((x % 22) - 11) ** 2 + ((y % 22) - 11) ** 2 < 30; const base = leaf(x, y); return spot && base[1] > 100 ? [235, 140, 30] : base; };
const sHealthy = img(256, 192, leaf), sRust = img(256, 192, rusty);
const sPaper = img(256, 192, (x, y) => [235 - noise(x, y) / 4, 235 - noise(x, y) / 4, 230]);
const sDark = img(256, 192, (x, y) => leaf(x, y).map((v) => v * 0.12) as [number, number, number]);
const smooth = (f: (x: number, y: number) => [number, number, number], r: number) => (x: number, y: number): [number, number, number] => { const acc = [0, 0, 0]; let k = 0; for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const v = f(x + dx, y + dy); acc[0] += v[0]; acc[1] += v[1]; acc[2] += v[2]; k++; } return [acc[0] / k, acc[1] / k, acc[2] / k]; };
const sBlur = img(256, 192, smooth(leaf, 4));
const q = (s: ReturnType<typeof img>) => qualityFrom(s, 3000, 4000);
console.log("healthy", q(sHealthy), mockClassify(sHealthy, q(sHealthy)).label, "| rust", mockClassify(sRust, q(sRust)).label, mockClassify(sRust, q(sRust)).confidence, "| paper", mockClassify(sPaper, q(sPaper)).label, "| dark", q(sDark).reason, "| blur", q(sBlur).reason, Math.round(sBlur.blur));
ok(q(sHealthy).ok && mockClassify(sHealthy, q(sHealthy)).label === "healthy", "healthy synthetic");
ok(mockClassify(sRust, q(sRust)).label === "rust", "rust synthetic");
ok(mockClassify(sPaper, q(sPaper)).label === "not_leaf", "paper is not_leaf");
ok(q(sDark).reason === "dark", "dark");
ok(q(sBlur).reason === "blurry", "blurry");
ok(qualityFrom(sHealthy, 200, 300).reason === "too_small", "too small");

const nine = summarisePlot(Array(9).fill({ label: "rust" }));
ok(decide(nine, new Date(2026, 9, 4)).id === "too_few_leaves", "9 leaves -> too_few_leaves");
console.log(fails ? `${fails} FAILURES` : "ALL PASS");
process.exit(fails ? 1 : 0);
