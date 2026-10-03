import type { Label, LeafResult, PlotSummary } from './types';

export const PROBLEM_LABELS: readonly Label[] = ['rust', 'cercospora', 'phoma', 'miner'];

function emptyCounts(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
}

/**
 * Uncertain leaves are counted in `uncertain` only, never in a class.
 *
 * `dominant` is the most common problem label (ties go to the order rust, cercospora, phoma, miner).
 * `not_leaf` becomes dominant only when at least half of the photos are not leaves, so one stray
 * photo does not hide nine good ones. With no problem leaves it is `healthy` if any leaf was
 * healthy, otherwise `none`.
 */
export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const counts = emptyCounts();
  let uncertain = 0;
  for (const leaf of leaves) {
    if (leaf.label === 'unsure') uncertain += 1;
    else counts[leaf.label] += 1;
  }

  const n = leaves.length;
  const affected = PROBLEM_LABELS.reduce((sum, l) => sum + counts[l], 0);
  const distinctProblems = PROBLEM_LABELS.filter((l) => counts[l] > 0).length;

  let dominant: PlotSummary['dominant'] = 'none';
  if (n > 0 && counts.not_leaf * 2 >= n) {
    dominant = 'not_leaf';
  } else if (affected > 0) {
    let best: Label = PROBLEM_LABELS[0];
    for (const l of PROBLEM_LABELS) if (counts[l] > counts[best]) best = l;
    dominant = best;
  } else if (counts.healthy > 0) {
    dominant = 'healthy';
  }

  return { n, counts, uncertain, dominant, affected, distinctProblems };
}
