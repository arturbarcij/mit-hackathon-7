import { LABELS, PROBLEM_LABELS, type Label, type LeafResult, type PlotSummary } from './types.ts'

export function emptyCounts(): Record<Label, number> {
  return {
    healthy: 0,
    rust: 0,
    cercospora: 0,
    phoma: 0,
    miner: 0,
    not_leaf: 0,
  }
}

export function summarisePlot(leaves: LeafResult[]): PlotSummary {
  const counts = emptyCounts()
  let uncertain = 0

  for (const leaf of leaves) {
    if (leaf.abstained || leaf.label === 'unsure') {
      uncertain++
      continue
    }
    counts[leaf.label] += 1
  }

  let affected = 0
  let distinctProblems = 0
  let bestProblem: Label | 'none' = 'none'
  let bestCount = 0
  for (const label of PROBLEM_LABELS) {
    const n = counts[label]
    if (n > 0) {
      distinctProblems += 1
      affected += n
      if (n > bestCount) {
        bestCount = n
        bestProblem = label
      }
    }
  }

  let dominant: Label | 'none' = bestProblem
  if (dominant === 'none') {
    if (counts.not_leaf > 0 && counts.not_leaf >= counts.healthy) dominant = 'not_leaf'
    else if (counts.healthy > 0) dominant = 'healthy'
  }

  return {
    n: leaves.length,
    counts,
    uncertain,
    dominant,
    affected,
    distinctProblems,
  }
}

export function labelKeys(): Label[] {
  return LABELS
}
