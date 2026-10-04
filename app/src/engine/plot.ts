// Plot summary. Semantics are fixed in kb/CONTRACTS.md ("summarisePlot semantics");
// the rules table and the QA decision matrix depend on them.
import { DISEASES, LABELS, type Label, type LeafResult, type PlotSummary } from './types';

export function emptyCounts(): Record<Label, number> {
  return Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
}

export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const n = leaves.length;
  const counts = emptyCounts();
  let unsure = 0;
  for (const leaf of leaves) {
    // Unsure leaves are counted separately and never forced into a class.
    if (leaf.label === 'unsure' || !(leaf.label in counts)) unsure += 1;
    else counts[leaf.label] += 1;
  }

  const affected = DISEASES.reduce((sum, d) => sum + counts[d], 0);
  const distinctProblems = DISEASES.filter((d) => counts[d] > 0).length;
  const uncertain = unsure + counts.not_leaf;

  let dominant: Label | 'none' = 'none';
  if (counts.not_leaf > n / 2) {
    dominant = 'not_leaf';
  } else if (affected >= 1) {
    // Strictly greater keeps the first label on a tie: rust, cercospora, phoma, miner.
    let best: Label = DISEASES[0];
    for (const d of DISEASES) if (counts[d] > counts[best]) best = d;
    dominant = best;
  } else if (counts.healthy > 0) {
    dominant = 'healthy';
  }

  return { n, counts, uncertain, dominant, affected, distinctProblems };
}
