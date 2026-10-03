import { LABELS, type Label, type LeafResult, type PlotSummary } from './types.ts';

const PROBLEMS: readonly Label[] = ['rust', 'cercospora', 'phoma', 'miner'];

function emptyCounts(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
}

function isUncertain(leaf: LeafResult): boolean {
  return leaf.abstained || leaf.label === 'unsure' || !leaf.quality.ok;
}

function dominantOf(counts: Record<Label, number>, nonUncertain: number, affected: number): Label | 'none' {
  let top = 0;
  const leaders: Label[] = [];
  for (const label of PROBLEMS) {
    const count = counts[label];
    if (count > top) {
      top = count;
      leaders.length = 0;
      leaders.push(label);
    } else if (count === top && count > 0) {
      leaders.push(label);
    }
  }
  if (leaders.length > 1) return 'none';
  if (leaders.length === 1) return leaders[0];
  if (nonUncertain > 0 && affected === 0 && counts.healthy * 2 > nonUncertain) return 'healthy';
  if (nonUncertain > 0 && counts.not_leaf * 2 > nonUncertain) return 'not_leaf';
  return 'none';
}

export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const counts = emptyCounts();
  let uncertain = 0;
  for (const leaf of leaves) {
    if (isUncertain(leaf)) {
      uncertain += 1;
      continue;
    }
    if (LABELS.includes(leaf.label as Label)) counts[leaf.label as Label] += 1;
  }
  const affected = PROBLEMS.reduce((sum, label) => sum + counts[label], 0);
  const nonUncertain = leaves.length - uncertain;
  const distinctProblems = PROBLEMS.filter((label) => counts[label] > 0).length;
  return {
    n: leaves.length,
    counts,
    uncertain,
    dominant: dominantOf(counts, nonUncertain, affected),
    affected,
    distinctProblems,
  };
}
