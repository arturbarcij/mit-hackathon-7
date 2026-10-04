// "My farm": a schematic of Noor's 2 ha (coffee on the upper slope, maize and beans below).
// Each coffee block is coloured by its latest leaf check stored on this phone. No network, no new AI:
// it only regroups checks the engine already saved, keyed by plotId "<farm>-<block>".
// The layout is a schematic, not a survey: block shapes and sizes are illustrative.
import { decide, getAnswer, seasonWindow, type Check, type Label, type PlotSummary, type Severity } from '../engine';

export type Crop = 'coffee' | 'maize' | 'beans';

export interface FarmBlock {
  id: string; // short, SMS-safe (A-Z 0-9)
  crop: Crop;
  n: number; // 1-based number within its crop, for the label
  path: string; // SVG path in the 340 x 400 schematic
  label: [number, number]; // label anchor
  checkable: boolean; // the leaf model covers coffee only
}

/** Demo farm ID (synthetic member plot from public/geo). Block plot IDs are "P07-C1" and so on. */
export const FARM_ID = 'P07';

export const FARM_BLOCKS: readonly FarmBlock[] = [
  { id: 'C1', crop: 'coffee', n: 1, path: 'M18 34 L168 22 L170 112 L18 118 Z', label: [94, 72], checkable: true },
  { id: 'C2', crop: 'coffee', n: 2, path: 'M168 22 L322 30 L320 110 L170 112 Z', label: [245, 72], checkable: true },
  { id: 'C3', crop: 'coffee', n: 3, path: 'M18 118 L170 112 L170 200 L20 206 Z', label: [94, 160], checkable: true },
  { id: 'C4', crop: 'coffee', n: 4, path: 'M170 112 L320 110 L318 198 L170 200 Z', label: [245, 157], checkable: true },
  { id: 'M1', crop: 'maize', n: 1, path: 'M20 206 L318 198 L316 268 L22 274 Z', label: [170, 240], checkable: false },
  { id: 'B1', crop: 'beans', n: 1, path: 'M22 274 L316 268 L314 322 L24 328 Z', label: [170, 300], checkable: false },
];

export const COFFEE_BLOCKS = FARM_BLOCKS.filter((b) => b.checkable);

export function blockPlotId(blockId: string, farmId = FARM_ID): string {
  return `${farmId}-${blockId}`;
}

/** Days until the next check of a block. Assumption, officer to confirm: matches the
 * three-week repeat in the rust guidance (S03), so a block is looked at once per spray round. */
export const RECHECK_DAYS = 21;

export type BlockStatus = Severity | 'none';

export interface BlockState {
  block: FarmBlock;
  status: BlockStatus;
  last: Check | null;
  count: number;
  due: Date | null;
  overdue: boolean;
  daysAgo: number | null;
}

const DAY = 86_400_000;

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Latest check per coffee block, its status and when it is due again. */
export function blockStates(checks: readonly Check[], now: Date, farmId = FARM_ID): BlockState[] {
  return COFFEE_BLOCKS.map((block) => {
    const pid = blockPlotId(block.id, farmId);
    const mine = checks
      .filter((c) => c.plotId === pid && !isNaN(Date.parse(c.createdAt)))
      .sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt));
    const last = mine[0] ?? null;
    if (!last) return { block, status: 'none' as const, last: null, count: 0, due: null, overdue: true, daysAgo: null };
    const at = new Date(last.createdAt);
    const due = new Date(startOfDay(at) + RECHECK_DAYS * DAY);
    const daysAgo = Math.max(0, Math.round((startOfDay(now) - startOfDay(at)) / DAY));
    const status = decideSeverity(last);
    return { block, status, last, count: mine.length, due, overdue: startOfDay(now) > due.getTime(), daysAgo };
  });
}

// The stored answer is what Noor was told, so its severity colours the block (not a fresh decision).
function decideSeverity(c: Check): Severity {
  return getAnswer(c.answerId).severity;
}

const PRIORITY: Record<BlockStatus, number> = { act: 0, ask: 1, none: 2, watch: 3, ok: 4 };

/** Which block to look at next: never checked or overdue first, then act, ask, watch, ok; oldest first. */
export function nextBlock(states: readonly BlockState[]): BlockState | null {
  if (!states.length) return null;
  const sorted = [...states].sort((a, b) => {
    if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
    if (PRIORITY[a.status] !== PRIORITY[b.status]) return PRIORITY[a.status] - PRIORITY[b.status];
    return (b.daysAgo ?? Infinity) - (a.daysAgo ?? Infinity);
  });
  return sorted[0];
}

/** Checks saved before blocks existed (plotId is the farm ID alone, or missing). */
export function unassignedChecks(checks: readonly Check[], farmId = FARM_ID): number {
  return checks.filter((c) => !c.plotId || c.plotId === farmId).length;
}

function summary(counts: Partial<Record<Label, number>>, uncertain: number): PlotSummary {
  const full: Record<Label, number> = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0, ...counts };
  const diseases: Label[] = ['rust', 'cercospora', 'phoma', 'miner'];
  const affected = diseases.reduce((s, l) => s + full[l], 0);
  const present = diseases.filter((l) => full[l] > 0);
  const dominant = present.sort((a, b) => full[b] - full[a])[0] ?? (full.healthy > 0 ? 'healthy' : 'none');
  const n = Object.values(full).reduce((s, v) => s + v, 0) + uncertain;
  return { n, counts: full, uncertain, dominant, affected, distinctProblems: present.length };
}

/**
 * Example farm for judges and the demo video. SYNTHETIC: never saved, always shown with the
 * "Example data, synthetic" tag. Answers come from the real rule table (decide), not hand-picked.
 */
export function exampleChecks(now: Date, farmId = FARM_ID): Check[] {
  const rows: { block: string; daysAgo: number; s: PlotSummary; decision?: Check['decision'] }[] = [
    { block: 'C1', daysAgo: 2, s: summary({ rust: 6, healthy: 4 }, 0), decision: 'act' },
    { block: 'C2', daysAgo: 30, s: summary({ healthy: 10 }, 0), decision: 'wait' },
    { block: 'C3', daysAgo: 1, s: summary({ healthy: 5, rust: 1 }, 4), decision: 'ask' },
  ];
  return rows.map((r, i) => {
    const at = new Date(startOfDay(now) - r.daysAgo * DAY + 9 * 3_600_000);
    return {
      id: `example-${i}`,
      createdAt: at.toISOString(),
      lang: 'sw',
      leaves: [],
      summary: r.s,
      window: seasonWindow(at),
      answerId: decide(r.s, at).id,
      ...(r.decision ? { decision: r.decision } : {}),
      plotId: blockPlotId(r.block, farmId),
      consentMain: true,
      consentPhotos: false,
      synced: false,
    };
  });
}
