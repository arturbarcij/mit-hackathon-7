import answerData from "@/content/answers.json";
import ruleData from "@/content/rules.json";
import seasonData from "@/content/season.json";
import type { AnswerCard, Label, LeafResult, PlotSummary } from "@/engine";

const diseases = ["rust", "cercospora", "phoma", "miner"] as const;
const labels: Label[] = ["healthy", ...diseases, "not_leaf"];

export function summariseForRules(leaves: LeafResult[]): PlotSummary {
  const counts = Object.fromEntries(labels.map((label) => [label, 0])) as Record<Label, number>;
  let unsure = 0;
  for (const leaf of leaves) {
    if (leaf.label === "unsure") unsure += 1;
    else counts[leaf.label] += 1;
  }
  const affected = diseases.reduce((total, label) => total + counts[label], 0);
  const distinctProblems = diseases.filter((label) => counts[label] >= 1).length;
  let dominant: PlotSummary["dominant"] = "none";
  if (counts.not_leaf > leaves.length / 2) dominant = "not_leaf";
  else if (affected >= 1) dominant = diseases.reduce((best, label) => counts[label] > counts[best] ? label : best, diseases[0]);
  else if (counts.healthy > 0) dominant = "healthy";
  return { n: leaves.length, counts, uncertain: unsure + counts.not_leaf, dominant, affected, distinctProblems };
}

export function seasonWindow(date: Date): string {
  const value = (date.getMonth() + 1) * 100 + date.getDate();
  for (const window of seasonData.season.windows) {
    const start = window.start_month * 100 + window.start_day;
    const end = window.end_month * 100 + window.end_day;
    const matches = "wraps_year" in window && window.wraps_year ? value >= start || value <= end : value >= start && value <= end;
    if (matches) return window.name;
  }
  return "";
}

type Condition = { dominant?: string; affected_gte?: number; affected_lte?: number; uncertain_gte?: number; distinct_problems_gte?: number; window?: string };

function matches(condition: Condition, summary: PlotSummary, date: Date): boolean {
  return (condition.dominant === undefined || condition.dominant === summary.dominant)
    && (condition.affected_gte === undefined || summary.affected >= condition.affected_gte)
    && (condition.affected_lte === undefined || summary.affected <= condition.affected_lte)
    && (condition.uncertain_gte === undefined || summary.uncertain >= condition.uncertain_gte)
    && (condition.distinct_problems_gte === undefined || summary.distinctProblems >= condition.distinct_problems_gte)
    && (condition.window === undefined || condition.window === seasonWindow(date));
}

export function applyRules(summary: PlotSummary, date: Date): AnswerCard {
  const rule = ruleData.rules.find((candidate) => matches(candidate.if, summary, date));
  const entry = answerData.answers.find((candidate) => candidate.id === rule?.then)
    ?? answerData.answers.find((candidate) => candidate.id === "ask_officer");
  if (!entry) throw new Error("The answer bank must include ask_officer");
  const card: AnswerCard = {
    id: entry.id,
    severity: entry.severity as AnswerCard["severity"],
    text: entry.text,
    audio: {},
    sources: entry.sources,
    assumption: entry.assumption,
  };
  if ("not_sure" in entry && entry.not_sure) card.notSure = entry.not_sure;
  return card;
}
