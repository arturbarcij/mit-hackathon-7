// Non-ML decision layer: plot summary, season window, rule table, answer cards, referral SMS.
// Pure functions, no DOM. Semantics follow kb/CONTRACTS.md exactly; app/qa/checks/decision_matrix.py
// enumerates the same rules, and test/decision.test.ts checks this file against it.
// Content files are owned by content-voice and synced from the main repo: do not edit them here.
import answersJson from "../content/answers.json";
import rulesJson from "../content/rules.json";
import seasonJson from "../content/season.json";
import type {
  AnswerCard,
  Label,
  Lang,
  LeafResult,
  PlotSummary,
  ReferralInput,
  SeasonClock,
  SeasonWindow,
} from "./types";

interface AnswerEntry {
  id: string;
  kind?: string;
  severity?: string;
  text: Partial<Record<Lang, string>>;
  not_sure?: Partial<Record<Lang, string>>;
  sources?: string[];
  assumption?: boolean;
  review_status?: Partial<Record<Lang, string>>;
}
interface RuleCondition {
  dominant?: string;
  affected_gte?: number;
  affected_lte?: number;
  uncertain_gte?: number;
  distinct_problems_gte?: number;
  window?: string;
}
interface Rule { if: RuleCondition; then: string; assumption?: boolean; sources?: string[]; note?: string }
interface WindowEntry { name: string; start_month: number; start_day: number; end_month: number; end_day: number; wraps_year?: boolean }

const ANSWERS = answersJson as unknown as AnswerEntry[];
const RULES = rulesJson as unknown as Rule[];
const WINDOWS = (seasonJson as unknown as { windows: WindowEntry[] }).windows;
const BY_ID = new Map(ANSWERS.map((a) => [a.id, a]));

export const LABELS: Label[] = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"];
/** Disease labels in tie-break order (kb/CONTRACTS.md). */
export const DISEASES = ["rust", "cercospora", "phoma", "miner"] as const;
export const LANGS: Lang[] = ["sw", "kik", "en"];

const emptyCounts = (): Record<Label, number> => ({ healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 });

/** kb/CONTRACTS.md "summarisePlot semantics". */
export function summarisePlot(leaves: Pick<LeafResult, "label">[]): PlotSummary {
  const counts = emptyCounts();
  let unsure = 0;
  for (const leaf of leaves) {
    if (leaf.label === "unsure") unsure += 1;
    else counts[leaf.label] += 1;
  }
  const n = leaves.length;
  const affected = DISEASES.reduce((sum, d) => sum + counts[d], 0);
  const distinctProblems = DISEASES.filter((d) => counts[d] > 0).length;
  const uncertain = unsure + counts.not_leaf;
  let dominant: PlotSummary["dominant"];
  if (counts.not_leaf > n / 2) dominant = "not_leaf";
  else if (affected >= 1) {
    let best: (typeof DISEASES)[number] = "rust";
    for (const d of DISEASES) if (counts[d] > counts[best]) best = d; // strict > keeps the earlier label on ties
    dominant = best;
  } else if (counts.healthy > 0) dominant = "healthy";
  else dominant = "none";
  return { n, counts, uncertain, dominant, affected, distinctProblems };
}

const md = (month: number, day: number) => month * 100 + day;

/** First matching window in season.json wins; windows cover the whole year. */
export function seasonWindow(date: Date): SeasonWindow {
  const x = md(date.getMonth() + 1, date.getDate());
  for (const w of WINDOWS) {
    const s = md(w.start_month, w.start_day);
    const e = md(w.end_month, w.end_day);
    const hit = w.wraps_year || s > e ? x >= s || x <= e : x >= s && x <= e;
    if (hit) return w.name as SeasonWindow;
  }
  return "dry";
}

function matches(cond: RuleCondition, s: PlotSummary, window: SeasonWindow): boolean {
  if (cond.dominant !== undefined && s.dominant !== cond.dominant) return false;
  if (cond.affected_gte !== undefined && !(s.affected >= cond.affected_gte)) return false;
  if (cond.affected_lte !== undefined && !(s.affected <= cond.affected_lte)) return false;
  if (cond.uncertain_gte !== undefined && !(s.uncertain >= cond.uncertain_gte)) return false;
  if (cond.distinct_problems_gte !== undefined && !(s.distinctProblems >= cond.distinct_problems_gte)) return false;
  if (cond.window !== undefined && window !== cond.window) return false;
  return true;
}

/** A plot check needs at least this many leaves; fewer gives the too_few_leaves card (red-team fix, same as app/src/engine/decide.ts). */
export const MIN_LEAVES = 10;

/** Id of the first rule that matches; "ask_officer" when nothing matches. Never throws. */
export function decideId(summary: PlotSummary, window: SeasonWindow): string {
  try {
    if (!summary || !Number.isFinite(summary.n)) return "ask_officer";
    if (summary.n < MIN_LEAVES) return BY_ID.has("too_few_leaves") ? "too_few_leaves" : "ask_officer";
    for (const r of RULES) if (matches(r.if ?? {}, summary, window)) return r.then || "ask_officer";
    return "ask_officer";
  } catch {
    return "ask_officer";
  }
}

/** Rule that produced an answer, for the "why this answer" panel (officer review and judges). */
export function explain(summary: PlotSummary, date: Date): { window: SeasonWindow; ruleIndex: number; rule: Rule | null } {
  const window = seasonWindow(date);
  const ruleIndex = RULES.findIndex((r) => matches(r.if ?? {}, summary, window));
  return { window, ruleIndex, rule: ruleIndex >= 0 ? RULES[ruleIndex] : null };
}

const SEVERITIES = new Set(["ok", "watch", "act", "ask"]);

/** Builds the card for any id in answers.json. Unknown ids fall back to ask_officer (fail safe). */
export function answerCard(id: string): AnswerCard {
  const a = BY_ID.get(id) ?? BY_ID.get("ask_officer");
  if (!a) throw new Error("answers.json has no ask_officer entry");
  const audio: Partial<Record<Lang, string>> = {};
  for (const l of LANGS) if (a.text[l]) audio[l] = `/audio/${l}/${a.id}.mp3`;
  return {
    id: a.id,
    severity: (SEVERITIES.has(a.severity ?? "") ? a.severity : "ask") as AnswerCard["severity"],
    text: a.text,
    notSure: a.not_sure,
    audio,
    sources: a.sources ?? [],
    assumption: Boolean(a.assumption),
    reviewStatus: a.review_status,
  };
}

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  return answerCard(decideId(summary, seasonWindow(date)));
}

/** Text in the chosen language. Falls back to English and says so; never invents a translation. */
export function cardText(card: AnswerCard, lang: Lang): {
  text: string;
  notSure: string | null;
  lang: Lang;
  untranslated: boolean;
  machineDraft: boolean;
  draft: boolean;
} {
  const has = Boolean(card.text[lang]);
  const used: Lang = has ? lang : "en";
  const status = card.reviewStatus?.[used] ?? "";
  return {
    text: card.text[used] ?? "",
    notSure: card.notSure?.[used] ?? card.notSure?.en ?? null,
    lang: used,
    untranslated: !has && lang !== "en",
    machineDraft: status.startsWith("machine"),
    draft: status === "draft",
  };
}

// ---------- Season clock ----------

const DAY = 24 * 60 * 60 * 1000;
const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

function occurrences(name: string, around: Date): { start: Date; end: Date }[] {
  const out: { start: Date; end: Date }[] = [];
  const y0 = around.getFullYear();
  for (const w of WINDOWS.filter((x) => x.name === name)) {
    for (const y of [y0 - 1, y0, y0 + 1]) {
      const start = new Date(y, w.start_month - 1, w.start_day);
      const wraps = w.wraps_year || md(w.start_month, w.start_day) > md(w.end_month, w.end_day);
      const end = new Date(wraps ? y + 1 : y, w.end_month - 1, w.end_day);
      out.push({ start, end });
    }
  }
  return out.sort((a, b) => a.start.getTime() - b.start.getTime());
}

const daysBetween = (a: Date, b: Date) => Math.round((startOfDay(b).getTime() - startOfDay(a).getTime()) / DAY);

/** Where today sits in the rust spray calendar (S03 timing, NASA POWER onset; see season.json). */
export function seasonClock(date: Date): SeasonClock {
  const today = startOfDay(date);
  const window = seasonWindow(today);
  type SprayName = "pre_short_rains" | "pre_long_rains";
  const spray = (["pre_short_rains", "pre_long_rains"] as SprayName[])
    .flatMap((name) => occurrences(name, today).map((o) => ({ name, ...o })))
    .filter((o) => o.end.getTime() >= today.getTime())
    .sort((a, b) => a.start.getTime() - b.start.getTime())[0];
  const open = spray.start.getTime() <= today.getTime();
  type RainName = "short_rains" | "long_rains";
  const rains = (["short_rains", "long_rains"] as RainName[])
    .flatMap((name) => occurrences(name, today).map((o) => ({ name, ...o })))
    .filter((o) => o.start.getTime() > today.getTime())
    .sort((a, b) => a.start.getTime() - b.start.getTime())[0];
  return {
    window,
    sprayWindowOpen: open,
    sprayWindow: { name: spray.name, start: spray.start, end: spray.end },
    days: open ? daysBetween(today, spray.end) : daysBetween(today, spray.start),
    daysToRains: daysBetween(today, rains.start),
    nextRains: { name: rains.name, start: rains.start },
  };
}

// ---------- Referral SMS (JANI1, kb/CONTRACTS.md) ----------

export const SMS_MAX = 160;

const cleanId = (s: string, fallback: string) =>
  s.trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10) || fallback;

/** Plot ids are sent as P<digits>, e.g. "7" or "p07" becomes "P07". */
export function normalisePlot(s: string): string {
  const digits = s.replace(/\D/g, "").slice(0, 3);
  return digits ? `P${digits.padStart(2, "0")}` : "P00";
}

const ymd = (d: Date) => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;

/** JANI1 M:<member> P:<plot> D:<yyyymmdd> N R C H L U A Q X. Always at most 160 GSM-7 characters. */
export function buildReferral(o: ReferralInput): string {
  const c = o.summary.counts;
  const q = Math.max(0, Math.min(100, Math.round(o.confidence * 100)));
  const answer = o.answerId.replace(/[^a-z0-9_]/gi, "").slice(0, 40) || "ask_officer";
  const body =
    `JANI1 M:${cleanId(o.memberId, "M0")} P:${normalisePlot(o.plotId)} D:${ymd(o.date)} ` +
    `N:${o.summary.n} R:${c.rust} C:${c.cercospora} H:${c.phoma} L:${c.miner} U:${o.summary.uncertain} ` +
    `A:${answer} Q:${q} X:${o.decision}`;
  return body.slice(0, SMS_MAX);
}

/** Mean confidence of leaves the model accepted (not unsure), 0 when none. */
export function meanConfidence(leaves: Pick<LeafResult, "label" | "confidence">[]): number {
  const ok = leaves.filter((l) => l.label !== "unsure");
  return ok.length ? ok.reduce((s, l) => s + l.confidence, 0) / ok.length : 0;
}
