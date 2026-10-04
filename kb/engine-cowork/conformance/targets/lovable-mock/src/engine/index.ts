import type {
  AnswerCard,
  Label,
  Lang,
  LeafResult,
  PlotSummary,
  QualityResult,
  ReferralCheck,
} from "./types";

export type {
  AnswerCard,
  Decision,
  Label,
  Lang,
  LeafResult,
  PlotSummary,
  QualityResult,
  ReferralCheck,
} from "./types";

const labels: Label[] = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"];
const emptyCounts = (): Record<Label, number> => ({
  healthy: 0,
  rust: 0,
  cercospora: 0,
  phoma: 0,
  miner: 0,
  not_leaf: 0,
});

export async function loadModel(): Promise<{ version: string; mock: boolean }> {
  return { version: "jani-mock-0.1", mock: true };
}

export function checkQuality(img: ImageBitmap): QualityResult {
  const shortest = Math.min(img.width, img.height);
  const blur = ((img.width * 13 + img.height * 7) % 100) / 100;
  const brightness = 0.42 + (((img.width + img.height) % 40) / 100);
  if (shortest < 240) return { ok: false, reason: "too_small", blur, brightness };
  return { ok: true, blur, brightness };
}

export async function classifyLeaf(img: ImageBitmap): Promise<LeafResult> {
  const quality = checkQuality(img);
  const seed = Math.abs((img.width * 31 + img.height * 17) % 24);
  const unsure = seed % 8 === 0;
  const selected: Label = seed % 5 < 3 ? "rust" : seed % 5 === 3 ? "healthy" : labels[seed % labels.length] ?? "healthy";
  const confidence = unsure ? 0.42 : 0.76 + ((seed % 16) / 100);
  const remainder = (1 - confidence) / (labels.length - 1);
  const probs = emptyCounts();
  for (const label of labels) probs[label] = label === selected ? confidence : remainder;
  return {
    label: unsure ? "unsure" : selected,
    probs,
    confidence,
    quality,
    abstained: unsure,
    modelVersion: "jani-mock-0.1",
  };
}

export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const counts = emptyCounts();
  let uncertain = 0;
  for (const leaf of leaves) {
    if (leaf.label === "unsure") uncertain += 1;
    else counts[leaf.label] += 1;
  }
  const problemLabels: Label[] = ["rust", "cercospora", "phoma", "miner"];
  const affected = problemLabels.reduce((sum, label) => sum + counts[label], 0);
  const distinctProblems = problemLabels.filter((label) => counts[label] > 0).length;
  const dominantEntry = labels.reduce<[Label | "none", number]>(
    (best, label) => (counts[label] > best[1] ? [label, counts[label]] : best),
    ["none", 0],
  );
  return { n: leaves.length, counts, uncertain, dominant: dominantEntry[0], affected, distinctProblems };
}

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  void date;
  if (summary.uncertain >= 2 || summary.counts.not_leaf >= 2) {
    return {
      id: "ask-officer",
      severity: "ask",
      text: { en: "Ask the cooperative officer to check these leaves.", sw: "Ask the cooperative officer to check these leaves.", kik: "Ask the cooperative officer to check these leaves." },
      notSure: { en: "The photos do not give a clear result.", sw: "The photos do not give a clear result.", kik: "The photos do not give a clear result." },
      audio: {}, sources: ["jani-field-guide"], assumption: true,
    };
  }
  if (summary.counts.rust >= Math.max(2, Math.ceil(summary.n / 3))) {
    return {
      id: "rust-action",
      severity: "act",
      text: { en: "Rust signs are common. Check nearby trees today.", sw: "Rust signs are common. Check nearby trees today.", kik: "Rust signs are common. Check nearby trees today." },
      notSure: { en: "A photo cannot confirm the cause.", sw: "A photo cannot confirm the cause.", kik: "A photo cannot confirm the cause." },
      audio: {}, sources: ["jani-field-guide"], assumption: true,
    };
  }
  return {
    id: "keep-watching",
    severity: summary.affected > 0 ? "watch" : "ok",
    text: { en: "No widespread leaf problem was found. Keep watching.", sw: "No widespread leaf problem was found. Keep watching.", kik: "No widespread leaf problem was found. Keep watching." },
    notSure: { en: "Only the leaves you picked were checked.", sw: "Only the leaves you picked were checked.", kik: "Only the leaves you picked were checked." },
    audio: {}, sources: ["jani-field-guide"], assumption: true,
  };
}

export function buildReferral(check: ReferralCheck): string {
  const dominant = check.summary.dominant === "none" ? "no clear problem" : check.summary.dominant;
  return `Jani check: ${check.summary.n} leaves, ${check.summary.affected} affected, ${check.summary.uncertain} not sure. Main result: ${dominant}. Farmer chose: ${check.decision}. Please advise.`;
}

export function smsLink(number: string, body: string): string {
  const separator = /iPhone|iPad|iPod/i.test(typeof navigator === "undefined" ? "" : navigator.userAgent) ? "&" : "?";
  return `sms:${number}${separator}body=${encodeURIComponent(body)}`;
}

export async function play(answerId: string, lang: Lang): Promise<void> {
  void answerId;
  void lang;
  return Promise.resolve();
}
