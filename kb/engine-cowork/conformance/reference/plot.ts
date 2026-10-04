// summarisePlot, exact semantics from kb/CONTRACTS.md "summarisePlot semantics".
import type { Label, LeafResult, PlotSummary } from './types';

export const DISEASE_LABELS: readonly Label[] = ['rust', 'cercospora', 'phoma', 'miner'];
export const ALL_LABELS: readonly Label[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];

export function emptyCounts(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
}

export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const n = leaves.length;
  const counts = emptyCounts();
  let unsure = 0;
  for (const leaf of leaves) {
    if (leaf.label === 'unsure') unsure += 1;
    else counts[leaf.label] += 1;
  }

  // affected = accepted leaves with a disease label.
  let affected = 0;
  let distinctProblems = 0;
  for (const d of DISEASE_LABELS) {
    affected += counts[d];
    if (counts[d] > 0) distinctProblems += 1;
  }

  // uncertain = unsure PLUS not_leaf.
  const uncertain = unsure + counts.not_leaf;

  // dominant: not_leaf if strictly more than half of n; else most common disease
  // (tie order rust, cercospora, phoma, miner); else healthy if any; else none.
  let dominant: Label | 'none';
  if (n > 0 && counts.not_leaf * 2 > n) {
    dominant = 'not_leaf';
  } else if (affected >= 1) {
    let best: Label = 'rust';
    for (const d of DISEASE_LABELS) {
      // Strict greater keeps the earlier label on a tie.
      if (counts[d] > counts[best]) best = d;
    }
    dominant = best;
  } else if (counts.healthy > 0) {
    dominant = 'healthy';
  } else {
    dominant = 'none';
  }

  return { n, counts, uncertain, dominant, affected, distinctProblems };
}
